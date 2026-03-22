"""Core engine: plan generation, execution, undo, manifest management."""

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from classifier import classify_file
from classifier.signals import FileClassification


@dataclass
class MoveAction:
    source: Path
    destination: Path
    classification: FileClassification
    content: Optional[str] = None  # If set, create file with this content instead of moving


@dataclass
class MovePlan:
    actions: list[MoveAction] = field(default_factory=list)
    base_dir: Path = Path(".")
    preset_name: str = ""


MANIFEST_FILENAME = ".organizer_manifest.json"
HIDDEN_PREFIXES = (".", "__")
SKIP_NAMES = {MANIFEST_FILENAME, ".DS_Store", "Thumbs.db", "desktop.ini"}


def scan_directory(directory: Path) -> list[tuple[Path, FileClassification]]:
    """Scan top-level files in directory and classify each one."""
    results = []
    for entry in sorted(directory.iterdir()):
        # Skip directories
        if entry.is_dir():
            continue
        # Skip hidden files and system files
        if entry.name.startswith(HIDDEN_PREFIXES) or entry.name in SKIP_NAMES:
            continue
        # Skip symlinks
        if entry.is_symlink():
            continue
        try:
            classification = classify_file(entry)
            results.append((entry, classification))
        except (OSError, PermissionError):
            continue
    return results


def generate_plan(directory: Path, preset, progress_callback: Callable = None) -> MovePlan:
    """Scan directory, classify files, and ask preset where each should go."""
    files = scan_directory(directory)
    if progress_callback:
        progress_callback(0, len(files), "Classifying files...")

    actions = preset.organize(files, directory)

    # Deduplicate destinations
    seen_destinations: dict[str, int] = {}
    for action in actions:
        dest_str = str(action.destination)
        if dest_str in seen_destinations:
            seen_destinations[dest_str] += 1
            count = seen_destinations[dest_str]
            stem = action.destination.stem
            suffix = action.destination.suffix
            parent = action.destination.parent
            action.destination = parent / f"{stem} ({count}){suffix}"
        else:
            seen_destinations[dest_str] = 1

    plan = MovePlan(actions=actions, base_dir=directory, preset_name=preset.name)
    return plan


def apply_plan(plan: MovePlan, progress_callback: Callable = None) -> bool:
    """Execute all moves in the plan. Returns True on success."""
    completed = []
    total = len(plan.actions)

    try:
        for i, action in enumerate(plan.actions):
            if action.content is not None:
                # Create a new file
                os.makedirs(action.destination.parent, exist_ok=True)
                with open(action.destination, "w", encoding="utf-8") as f:
                    f.write(action.content)
                completed.append(action)
            else:
                # Move file
                os.makedirs(action.destination.parent, exist_ok=True)
                shutil.move(str(action.source), str(action.destination))
                completed.append(action)

            if progress_callback:
                progress_callback(i + 1, total, f"Moving {action.source.name}...")

    except Exception as e:
        # Rollback completed moves
        for action in reversed(completed):
            try:
                if action.content is not None:
                    os.remove(action.destination)
                else:
                    os.makedirs(action.source.parent, exist_ok=True)
                    shutil.move(str(action.destination), str(action.source))
            except Exception:
                pass
        raise RuntimeError(f"Failed to apply plan: {e}. All changes rolled back.") from e

    # Write manifest
    _save_manifest(plan)
    return True


def undo_last(directory: Path, progress_callback: Callable = None) -> bool:
    """Undo the last applied operation. Returns True if successful."""
    manifest_path = directory / MANIFEST_FILENAME
    if not manifest_path.exists():
        return False

    try:
        with open(manifest_path, "r") as f:
            operations = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    if not operations:
        return False

    last_op = operations.pop()
    moves = last_op.get("moves", [])
    total = len(moves)

    for i, move in enumerate(reversed(moves)):
        src = Path(move["source"])
        dst = Path(move["destination"])
        is_created = move.get("created", False)

        try:
            if is_created:
                # Remove created file
                if dst.exists():
                    os.remove(dst)
            else:
                # Reverse the move
                os.makedirs(src.parent, exist_ok=True)
                shutil.move(str(dst), str(src))
        except Exception:
            pass

        if progress_callback:
            progress_callback(i + 1, total, f"Restoring {src.name}...")

    # Clean up empty directories
    _cleanup_empty_dirs(directory)

    # Update manifest
    if operations:
        with open(manifest_path, "w") as f:
            json.dump(operations, f, indent=2)
    else:
        os.remove(manifest_path)

    return True


def has_undo(directory: Path) -> bool:
    """Check if there's an undo operation available."""
    manifest_path = directory / MANIFEST_FILENAME
    if not manifest_path.exists():
        return False
    try:
        with open(manifest_path, "r") as f:
            operations = json.load(f)
        return bool(operations)
    except Exception:
        return False


def build_tree(plan: MovePlan) -> dict:
    """Convert a flat plan into a nested tree dict for display.

    Returns: {"folder_name": {"subfolder": {"file.txt": None}}}
    """
    tree = {}
    for action in plan.actions:
        try:
            rel = action.destination.relative_to(plan.base_dir)
        except ValueError:
            rel = action.destination
        parts = rel.parts
        node = tree
        for part in parts[:-1]:
            if part not in node or node[part] is None:
                node[part] = {}
            node = node[part]
        # Leaf = filename
        node[parts[-1]] = None
    return tree


def _save_manifest(plan: MovePlan):
    """Append operation to manifest file."""
    manifest_path = plan.base_dir / MANIFEST_FILENAME
    operations = []
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                operations = json.load(f)
        except (json.JSONDecodeError, OSError):
            operations = []

    moves = []
    for action in plan.actions:
        move_entry = {
            "source": str(action.source),
            "destination": str(action.destination),
        }
        if action.content is not None:
            move_entry["created"] = True
        moves.append(move_entry)

    operations.append({
        "timestamp": datetime.now().isoformat(),
        "preset_name": plan.preset_name,
        "target_directory": str(plan.base_dir),
        "moves": moves,
    })

    with open(manifest_path, "w") as f:
        json.dump(operations, f, indent=2)


def _cleanup_empty_dirs(directory: Path):
    """Remove empty directories left behind after undo."""
    for dirpath, dirnames, filenames in os.walk(str(directory), topdown=False):
        dp = Path(dirpath)
        if dp == directory:
            continue
        try:
            if not any(dp.iterdir()):
                dp.rmdir()
        except OSError:
            pass
