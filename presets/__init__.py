"""Base preset class and registry."""

from pathlib import Path
from classifier.signals import FileClassification
from engine import MoveAction


class BasePreset:
    name: str = "Base"
    description: str = ""
    icon: str = ""

    def organize(
        self,
        files: list[tuple[Path, FileClassification]],
        base_dir: Path,
    ) -> list[MoveAction]:
        """Given classified files, return MoveActions for where each should go."""
        raise NotImplementedError


PRESET_REGISTRY: dict[str, BasePreset] = {}


def register(preset_class):
    """Decorator to register a preset."""
    instance = preset_class()
    PRESET_REGISTRY[instance.name] = instance
    return preset_class


def get_all_presets() -> list[BasePreset]:
    """Return all registered presets in display order."""
    # Import to trigger registration
    from . import dad, productive, messy  # noqa: F401
    return list(PRESET_REGISTRY.values())
