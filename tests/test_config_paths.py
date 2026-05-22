from pathlib import Path

import flatshot.application.config_paths as config_paths_module
from flatshot.application.config_paths import CONFIG_DIR_ENV_VAR, ConfigPathResolver


def test_config_path_resolver_does_not_import_pyqt():
    source = config_paths_module.Path(config_paths_module.__file__).read_text(encoding="utf-8")

    assert "PyQt6" not in source
    assert "QStandardPaths" not in source


def test_config_path_resolver_uses_explicit_config_dir(tmp_path):
    resolver = ConfigPathResolver(tmp_path / "config")

    assert resolver.config_dir() == tmp_path / "config"
    assert resolver.settings_file() == tmp_path / "config" / "settings.json"
    assert resolver.logs_dir() == tmp_path / "config" / "logs"
    assert (tmp_path / "config" / "logs").is_dir()


def test_config_path_resolver_uses_environment_override(tmp_path):
    configured = tmp_path / "env-config"
    resolver = ConfigPathResolver(environ={CONFIG_DIR_ENV_VAR: str(configured)})

    assert resolver.config_dir() == configured


def test_default_user_config_dir_matches_current_windows_qt_fallback_shape():
    path = ConfigPathResolver.default_user_config_dir(
        environ={"LOCALAPPDATA": r"C:\Users\demo\AppData\Local"},
        home=Path(r"C:\Users\demo"),
        platform="win32",
    )

    assert path == Path(r"C:\Users\demo\AppData\Local")


def test_default_user_config_dir_uses_xdg_config_home_on_linux(tmp_path):
    path = ConfigPathResolver.default_user_config_dir(
        environ={"XDG_CONFIG_HOME": str(tmp_path / "xdg")},
        home=tmp_path / "home",
        platform="linux",
    )

    assert path == tmp_path / "xdg"
