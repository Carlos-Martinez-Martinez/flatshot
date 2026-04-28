"""Structural UI containers for the FlatShot workspace."""
from dataclasses import dataclass

from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout


@dataclass
class UiViewState:
    selected_image: str | None = None
    active_folder: str | None = None
    grid_columns: int = 3
    preview_background: str = "#E6E6E6"
    guides_enabled: bool = False
    advanced_open: bool = False


@dataclass
class BatchSummary:
    folders_count: int = 0
    images_count: int = 0
    processed_count: int = 0
    error_count: int = 0
    adjusted_count: int = 0
    destination_label: str = "Subcarpeta en origen"


class _ShellFrame(QFrame):
    """Base frame with a stable class property for stylesheet targeting."""

    class_name = "shell-frame"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", self.class_name)


class AppShell(_ShellFrame):
    class_name = "app-shell"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)


class WorkflowPanel(_ShellFrame):
    class_name = "workflow-panel"


class CanvasWorkbench(_ShellFrame):
    class_name = "canvas-workbench"


class BatchPanel(_ShellFrame):
    class_name = "batch-panel"


class ExportBar(_ShellFrame):
    class_name = "export-bar"


class CommandBar(_ShellFrame):
    class_name = "command-bar"
