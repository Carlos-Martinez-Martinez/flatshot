"""
Tests for FlatShot CLI
"""
import pytest
import sys
import ast
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestCLIHelp:
    """Tests for CLI help output."""
    
    def test_cli_help_runs(self):
        """Test that CLI help runs without error."""
        from flatshot.cli import main
        
        with patch('sys.argv', ['flatshot', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 on --help
            assert exc_info.value.code == 0

    def test_cli_does_not_import_qt_bound_persistence_or_worker_helpers(self):
        """CLI should not import Qt-bound persistence or worker adapters."""
        import flatshot.cli as cli

        tree = ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        assert "flatshot.utils.config" not in imports
        assert "flatshot.utils.log_manager" not in imports
        assert "flatshot.workers.export_worker" not in imports
    
    def test_process_help_runs(self):
        """Test that process subcommand help works."""
        from flatshot.cli import main
        
        with patch('sys.argv', ['flatshot', 'process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestListPresets:
    """Tests for list-presets command."""
    
    def test_list_presets_runs(self, capsys):
        """Test that list-presets runs and produces output."""
        from flatshot.cli import list_presets
        
        list_presets()
        
        captured = capsys.readouterr()
        # Should contain either presets or "No presets found"
        assert len(captured.out) > 0


class TestGetPresetSettings:
    """Tests for preset loading."""
    
    def test_get_nonexistent_preset_exits(self):
        """Test that getting nonexistent preset exits with error."""
        from flatshot.cli import get_preset_settings
        
        with pytest.raises(SystemExit) as exc_info:
            get_preset_settings("ThisPresetDoesNotExist12345")
        
        assert exc_info.value.code == 1


class TestNamingTemplate:
    """Tests for naming template functionality."""
    
    def test_apply_naming_template_basic(self):
        """Test basic naming template application."""
        from flatshot.application.export_runner import apply_naming_template
        
        result = apply_naming_template(
            "{original}{suffix}",
            "product_001",
            "_PRO",
            "Camisetas",
            1
        )
        
        assert result == "product_001_PRO"
    
    def test_apply_naming_template_with_folder(self):
        """Test naming template with folder placeholder."""
        from flatshot.application.export_runner import apply_naming_template
        
        result = apply_naming_template(
            "{folder}_{original}",
            "product_001",
            "_PRO",
            "Camisetas",
            1
        )
        
        assert result == "Camisetas_product_001"
    
    def test_apply_naming_template_with_index(self):
        """Test naming template with index placeholder."""
        from flatshot.application.export_runner import apply_naming_template
        
        result = apply_naming_template(
            "producto_{index}",
            "any_name",
            "_PRO",
            "Folder",
            42
        )
        
        assert result == "producto_042"  # Zero-padded to 3 digits
    
    def test_apply_naming_template_custom_padding(self):
        """Test naming template with custom index padding."""
        from flatshot.application.export_runner import apply_naming_template
        
        result = apply_naming_template(
            "item_{index:05d}",
            "any_name",
            "_PRO",
            "Folder",
            7
        )
        
        assert result == "item_00007"

    def test_apply_naming_template_variant_tokens(self):
        """Test naming template with output variant placeholders."""
        from flatshot.application.export_runner import apply_naming_template

        result = apply_naming_template(
            "{original}_{variant_id}_{bg}{suffix}",
            "camiseta_001",
            "_BLANCO",
            "Camisetas",
            1,
            variant_label="Blanco RGB255",
            variant_id="white_rgb255",
            bg="FFFFFF",
        )

        assert result == "camiseta_001_white_rgb255_FFFFFF_BLANCO"

    def test_apply_naming_template_variant_suffix_example(self):
        """Test the main variant suffix example keeps the expected filename."""
        from flatshot.application.export_runner import apply_naming_template

        result = apply_naming_template(
            "{original}{suffix}",
            "camiseta_001",
            "_BLANCO",
            "Camisetas",
            1,
            variant_label="Blanco RGB255",
            variant_id="white_rgb255",
            bg="FFFFFF",
        )

        assert result == "camiseta_001_BLANCO"


class TestProcessValidation:
    """Tests for process command input validation."""
    
    def test_process_missing_input(self):
        """Test that process requires input folder."""
        from flatshot.cli import main
        
        with patch('sys.argv', ['flatshot', 'process']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 2 on missing required argument
            assert exc_info.value.code == 2
    
    def test_process_nonexistent_folder(self, capsys, tmp_path):
        """Test process with nonexistent folder shows error."""
        from flatshot.cli import process_folder
        import argparse
        
        fake_path = tmp_path / "nonexistent_folder"
        
        args = argparse.Namespace(
            input=str(fake_path),
            preset=None,
            output=None,
            size=None,
            format="JPG",
            suffix=None,
            template=None,
            dry_run=False
        )
        
        with pytest.raises(SystemExit) as exc_info:
            process_folder(args)
        
        assert exc_info.value.code == 1


class TestDryRun:
    """Tests for dry-run functionality."""
    
    def test_dry_run_no_files_created(self, tmp_path, capsys):
        """Test that dry-run doesn't create output files."""
        from flatshot.cli import process_folder
        import argparse
        from PIL import Image
        
        # Create test folder with a test image
        test_folder = tmp_path / "test_images"
        test_folder.mkdir()
        
        # Create a simple test PNG
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        img.save(test_folder / "test.png")
        
        args = argparse.Namespace(
            input=str(test_folder),
            preset=None,
            output="_TEST_OUTPUT",
            size="400x600",
            format="JPG",
            suffix="_test",
            template=None,
            dry_run=True
        )
        
        process_folder(args)
        
        # Output folder should NOT exist after dry run
        output_folder = test_folder / "_TEST_OUTPUT"
        assert not output_folder.exists()
        
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
