"""
FlatShot - Modern Image Processing Application
Entry point for both GUI and CLI modes.
"""
import sys


def _install_excepthook():
    """Global exception hook to log crashes to flatshot/logs/app_crash.log."""
    import traceback
    from pathlib import Path
    import tempfile
    import faulthandler

    log_dir = Path(__file__).resolve().parents[2] / "logs"  # project_root/logs
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app_crash.log"
    temp_fallback = Path(tempfile.gettempdir()) / "flatshot_app_crash.log"

    def _write_log(msg: str):
        for target in (log_file, temp_fallback):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("a", encoding="utf-8") as f:
                    f.write(msg + "\n")
                print(f"[crash-log] {target}", flush=True)
                return
            except Exception as ex:
                print(f"[crash-log-error] {target}: {ex}", flush=True)

    def hook(exc_type, exc_value, exc_tb):
        formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _write_log(formatted)
        print(formatted, file=sys.stderr, flush=True)

    sys.excepthook = hook
    try:
        fh_target = log_file
        try:
            faulthandler.enable(open(fh_target, "a", encoding="utf-8"))
        except Exception:
            fh_target = temp_fallback
            faulthandler.enable(open(fh_target, "a", encoding="utf-8"))
        print(f"[faulthandler] logging to {fh_target}", file=sys.stderr, flush=True)
    except Exception as ex:
        print(f"[faulthandler-error] {ex}", file=sys.stderr, flush=True)


def _calculate_ui_scale(app):
    """
    Compute a UI scale factor based on the available screen geometry.
    Keeps values between 0.65 and 1.0 to avoid unreadable text.
    """
    try:
        screen = app.primaryScreen()
        if not screen:
            return 1.0

        available = screen.availableGeometry()
        usable_w = available.width() * 0.94  # leave some headroom for window frame
        usable_h = available.height() * 0.90  # leave space for taskbar/title/menu

        # Base logical size (in logical pixels)
        base_width, base_height = 1400, 1100
        scale_w = usable_w / base_width
        scale_h = usable_h / base_height
        base_scale = min(scale_w, scale_h, 1.0)

        # Account for OS display scaling (e.g., Windows 125% -> logical DPI ~120)
        dpi = max(screen.logicalDotsPerInch(), 72)  # guard against zero
        dpi_factor = 96.0 / dpi  # below 1.0 when OS scaling > 100%

        scale = base_scale * dpi_factor
        return max(min(scale, 1.0), 0.65)
    except Exception:
        # Fallback in case screen information is unavailable
        return 1.0


def main_gui():
    """Launch the GUI application."""
    _install_excepthook()
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import qInstallMessageHandler
    from PyQt6.QtGui import QFont
    
    from flatshot.ui.main_window import MainWindow
    from flatshot.ui.widgets import ModernSplashScreen
    from flatshot.ui.styles import get_stylesheet
    
    def _qt_message_handler(mode, context, message):
        # Suppress noisy font warnings while keeping other Qt messages visible.
        if "QFont::setPointSize: Point size <= 0" in message:
            return
        try:
            print(message, file=sys.stderr)
        except Exception:
            pass

    qInstallMessageHandler(_qt_message_handler)
    app = QApplication(sys.argv)
    ui_scale = _calculate_ui_scale(app)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    scaled_size = font.pointSizeF() * (ui_scale if ui_scale > 0 else 1.0)
    if scaled_size <= 1:
        scaled_size = 10
    font.setPointSizeF(scaled_size)
    app.setFont(font)
    
    # Apply dark theme
    app.setStyleSheet(get_stylesheet(ui_scale))
    
    # Show splash screen
    splash = ModernSplashScreen()
    splash.show()
    splash.update_status("Cargando módulos...")
    
    # Process events to show splash
    app.processEvents()
    
    # Create main window
    splash.update_status("Inicializando interfaz...")
    window = MainWindow(ui_scale=ui_scale)
    
    # Finish splash and show main window
    splash.finish(window)
    
    sys.exit(app.exec())


def main_cli():
    """Launch the CLI application."""
    from flatshot.cli import main as cli_main
    cli_main()


def main():
    """Main entry point - detects CLI or GUI mode."""
    # Check if running in CLI mode
    if len(sys.argv) > 1 and sys.argv[1] in ['list-presets', 'process', '--help', '-h']:
        main_cli()
    elif len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # Remove --cli flag and run CLI
        sys.argv.pop(1)
        main_cli()
    else:
        main_gui()


if __name__ == "__main__":
    main()
