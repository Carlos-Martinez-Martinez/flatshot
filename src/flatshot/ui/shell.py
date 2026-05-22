"""Structural UI containers for the FlatShot workspace."""
from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout

from flatshot.application.app_state import BatchSummary, UiViewState


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
