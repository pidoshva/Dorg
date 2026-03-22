#!/usr/bin/env python3
"""Directory Organizer — Main GUI application."""

import sys
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import generate_plan, apply_plan, undo_last, has_undo, build_tree, MovePlan
from presets import get_all_presets, BasePreset


class DirectoryOrganizer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Directory Organizer")
        self.root.geometry("950x720")
        self.root.minsize(800, 600)

        # State
        self.selected_dir: Path | None = None
        self.selected_preset: BasePreset | None = None
        self.current_plan: MovePlan | None = None
        self.progress_queue = queue.Queue()
        self.presets = get_all_presets()

        # Style
        self.style = ttk.Style()
        try:
            self.style.theme_use("aqua")
        except tk.TclError:
            self.style.theme_use("clam")

        self._configure_styles()
        self._build_ui()
        self._set_state("no_dir")

    def _configure_styles(self):
        self.style.configure("Title.TLabel", font=("Helvetica", 22, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Helvetica", 12), foreground="#666")
        self.style.configure("Dir.TLabel", font=("Helvetica", 13))
        self.style.configure("PresetName.TLabel", font=("Helvetica", 15, "bold"))
        self.style.configure("PresetDesc.TLabel", font=("Helvetica", 11), foreground="#555")
        self.style.configure("Status.TLabel", font=("Helvetica", 11), foreground="#444")
        self.style.configure("Selected.TFrame", relief="solid", borderwidth=2)
        self.style.configure(
            "Apply.TButton",
            font=("Helvetica", 13, "bold"),
            padding=(20, 10),
        )
        self.style.configure(
            "Undo.TButton",
            font=("Helvetica", 13),
            padding=(20, 10),
        )

    def _build_ui(self):
        # Main container with padding
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(title_frame, text="Directory Organizer", style="Title.TLabel").pack(side=tk.LEFT)

        ttk.Label(main, text="Organize any directory with smart file detection",
                  style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 15))

        # Directory picker row
        dir_frame = ttk.Frame(main)
        dir_frame.pack(fill=tk.X, pady=(0, 15))

        self.dir_button = ttk.Button(
            dir_frame, text="  Choose Directory...  ",
            command=self._pick_directory,
        )
        self.dir_button.pack(side=tk.LEFT)

        self.dir_label = ttk.Label(dir_frame, text="No directory selected",
                                   style="Dir.TLabel", foreground="#999")
        self.dir_label.pack(side=tk.LEFT, padx=(15, 0))

        # Separator
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 15))

        # Preset buttons row
        preset_frame = ttk.Frame(main)
        preset_frame.pack(fill=tk.X, pady=(0, 15))

        self.preset_frames = []
        self.preset_buttons = []

        for i, preset in enumerate(self.presets):
            frame = ttk.Frame(preset_frame, padding=10, relief="groove", borderwidth=1)
            frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0 if i == 0 else 8, 0))

            # Icon + name
            ttk.Label(frame, text=f"{preset.icon}  {preset.name}",
                      style="PresetName.TLabel").pack(anchor=tk.W)
            ttk.Label(frame, text=preset.description,
                      style="PresetDesc.TLabel", wraplength=250).pack(anchor=tk.W, pady=(4, 8))

            btn = ttk.Button(
                frame, text="Select",
                command=lambda p=preset: self._select_preset(p),
            )
            btn.pack(fill=tk.X)

            self.preset_frames.append(frame)
            self.preset_buttons.append(btn)

        # Preview area
        preview_label = ttk.Label(main, text="Preview:", style="Status.TLabel")
        preview_label.pack(anchor=tk.W, pady=(5, 5))

        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="none")
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            main, variable=self.progress_var,
            mode="determinate", maximum=100,
        )
        self.progress.pack(fill=tk.X, pady=(0, 5))

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(main, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(anchor=tk.W, pady=(0, 10))

        # Action buttons
        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X)

        self.apply_button = ttk.Button(
            action_frame, text="  Apply Changes  ",
            style="Apply.TButton",
            command=self._apply,
        )
        self.apply_button.pack(side=tk.LEFT)

        self.undo_button = ttk.Button(
            action_frame, text="  Undo Last  ",
            style="Undo.TButton",
            command=self._undo,
        )
        self.undo_button.pack(side=tk.RIGHT)

        # File count label
        self.count_var = tk.StringVar(value="")
        ttk.Label(action_frame, textvariable=self.count_var,
                  style="Status.TLabel").pack(side=tk.LEFT, padx=(20, 0))

    def _set_state(self, state: str):
        """Update UI state."""
        if state == "no_dir":
            for btn in self.preset_buttons:
                btn.configure(state="disabled")
            self.apply_button.configure(state="disabled")
            self.undo_button.configure(state="disabled")
            self.status_var.set("Select a directory to get started.")
        elif state == "dir_selected":
            for btn in self.preset_buttons:
                btn.configure(state="normal")
            self.apply_button.configure(state="disabled")
            # Check for undo
            if self.selected_dir and has_undo(self.selected_dir):
                self.undo_button.configure(state="normal")
            else:
                self.undo_button.configure(state="disabled")
            self.status_var.set("Choose a preset to preview the organization.")
        elif state == "preview_ready":
            for btn in self.preset_buttons:
                btn.configure(state="normal")
            self.apply_button.configure(state="normal")
            if self.selected_dir and has_undo(self.selected_dir):
                self.undo_button.configure(state="normal")
            else:
                self.undo_button.configure(state="disabled")
            n = len(self.current_plan.actions) if self.current_plan else 0
            self.count_var.set(f"{n} file{'s' if n != 1 else ''} to organize")
            self.status_var.set("Review the preview above, then click Apply.")
        elif state == "working":
            self.dir_button.configure(state="disabled")
            for btn in self.preset_buttons:
                btn.configure(state="disabled")
            self.apply_button.configure(state="disabled")
            self.undo_button.configure(state="disabled")
        elif state == "done":
            self.dir_button.configure(state="normal")
            for btn in self.preset_buttons:
                btn.configure(state="normal")
            self.apply_button.configure(state="disabled")
            if self.selected_dir and has_undo(self.selected_dir):
                self.undo_button.configure(state="normal")
            else:
                self.undo_button.configure(state="disabled")

    def _pick_directory(self):
        directory = filedialog.askdirectory(title="Choose a directory to organize")
        if directory:
            self.selected_dir = Path(directory)
            # Shorten display path
            display = str(self.selected_dir)
            home = str(Path.home())
            if display.startswith(home):
                display = "~" + display[len(home):]
            self.dir_label.configure(text=display, foreground="#000")
            self._clear_preview()
            self.selected_preset = None
            self.current_plan = None
            self._set_state("dir_selected")

    def _select_preset(self, preset: BasePreset):
        if not self.selected_dir:
            return

        self.selected_preset = preset

        # Highlight selected preset
        for i, p in enumerate(self.presets):
            if p.name == preset.name:
                self.preset_frames[i].configure(relief="solid", borderwidth=2)
            else:
                self.preset_frames[i].configure(relief="groove", borderwidth=1)

        # Generate preview in thread
        self._set_state("working")
        self.status_var.set(f"Analyzing files with {preset.name}...")
        self.progress_var.set(0)

        def worker():
            try:
                plan = generate_plan(self.selected_dir, preset, self._progress_cb)
                self.progress_queue.put(("preview_done", plan))
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_queue()

    def _apply(self):
        if not self.current_plan:
            return

        result = messagebox.askyesno(
            "Apply Changes",
            f"This will move {len(self.current_plan.actions)} files.\n"
            f"You can undo this later.\n\nProceed?",
        )
        if not result:
            return

        self._set_state("working")
        self.status_var.set("Applying changes...")
        self.progress_var.set(0)

        def worker():
            try:
                apply_plan(self.current_plan, self._progress_cb)
                self.progress_queue.put(("apply_done", None))
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_queue()

    def _undo(self):
        if not self.selected_dir:
            return

        result = messagebox.askyesno(
            "Undo Last Operation",
            "This will reverse the last organization.\nAll files will be moved back.\n\nProceed?",
        )
        if not result:
            return

        self._set_state("working")
        self.status_var.set("Undoing last operation...")
        self.progress_var.set(0)

        def worker():
            try:
                success = undo_last(self.selected_dir, self._progress_cb)
                self.progress_queue.put(("undo_done", success))
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_queue()

    def _progress_cb(self, current: int, total: int, message: str = ""):
        """Thread-safe progress callback."""
        if total > 0:
            pct = (current / total) * 100
        else:
            pct = 0
        self.progress_queue.put(("progress", (pct, message)))

    def _poll_queue(self):
        """Poll the progress queue for updates."""
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()

                if msg_type == "progress":
                    pct, message = data
                    self.progress_var.set(pct)
                    if message:
                        self.status_var.set(message)

                elif msg_type == "preview_done":
                    self.current_plan = data
                    self._populate_tree(data)
                    self._set_state("preview_ready")

                elif msg_type == "apply_done":
                    self.progress_var.set(100)
                    n = len(self.current_plan.actions) if self.current_plan else 0
                    self.status_var.set(f"Done! {n} files organized.")
                    self.current_plan = None
                    self._clear_preview()
                    self._set_state("done")

                elif msg_type == "undo_done":
                    self.progress_var.set(100)
                    if data:
                        self.status_var.set("Undo complete. Files restored.")
                    else:
                        self.status_var.set("Nothing to undo.")
                    self.current_plan = None
                    self._clear_preview()
                    self._set_state("done")

                elif msg_type == "error":
                    messagebox.showerror("Error", str(data))
                    self._set_state("dir_selected")

        except queue.Empty:
            pass

        # Keep polling if we're in working state
        if self.apply_button.cget("state") == "disabled" and \
           self.dir_button.cget("state") == "disabled":
            self.root.after(50, self._poll_queue)

    def _populate_tree(self, plan: MovePlan):
        """Fill the treeview with the plan's folder structure."""
        self._clear_preview()
        tree_data = build_tree(plan)

        # Cap display at 500 items
        item_count = [0]
        max_items = 500

        def insert_node(parent: str, name: str, children: dict | None):
            if item_count[0] >= max_items:
                return
            item_count[0] += 1

            if children is not None:
                # Folder
                node_id = self.tree.insert(parent, "end", text=f"📁 {name}", open=True)
                for child_name in sorted(children.keys(),
                                         key=lambda k: (children[k] is None, k)):
                    insert_node(node_id, child_name, children[child_name])
            else:
                # File
                self.tree.insert(parent, "end", text=f"  📄 {name}")

        for name in sorted(tree_data.keys(),
                           key=lambda k: (tree_data[k] is None, k)):
            insert_node("", name, tree_data[name])

        remaining = len(plan.actions) - item_count[0]
        if remaining > 0:
            self.tree.insert("", "end", text=f"  ... and {remaining} more files")

    def _clear_preview(self):
        """Clear the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.count_var.set("")


def main():
    root = tk.Tk()

    # Center on screen
    root.update_idletasks()
    w, h = 950, 720
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    app = DirectoryOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
