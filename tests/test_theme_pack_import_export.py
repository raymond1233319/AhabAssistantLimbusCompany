import datetime
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
from ruamel.yaml import YAML
from module.config.theme_pack_import_export import (
    generate_theme_pack_export_filename,
    export_theme_pack_weight,
    import_theme_pack_weight,
)


def test_generate_theme_pack_export_filename_with_remark_name():
    """Test filename generation with remark name."""
    with patch('module.config.theme_pack_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="MyTeam")
        }
        result = generate_theme_pack_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"theme_pack_weight_team_MyTeam_{expected_date}.yaml"


def test_generate_theme_pack_export_filename_without_remark_name():
    """Test filename generation without remark name."""
    with patch('module.config.theme_pack_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name=None)
        }
        result = generate_theme_pack_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"theme_pack_weight_team_1_{expected_date}.yaml"


def test_generate_theme_pack_export_filename_team_not_found():
    """Test filename generation when team not found."""
    with patch('module.config.theme_pack_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {}
        result = generate_theme_pack_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"theme_pack_weight_team_1_{expected_date}.yaml"


def test_generate_theme_pack_export_filename_with_special_characters():
    """Test filename generation with special characters in remark name."""
    with patch('module.config.theme_pack_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name='Team<>:"/\\|?*Name')
        }
        result = generate_theme_pack_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"theme_pack_weight_team_Team_________Name_{expected_date}.yaml"


def test_generate_theme_pack_export_filename_with_empty_remark_name():
    """Test filename generation with empty remark name."""
    with patch('module.config.theme_pack_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="")
        }
        result = generate_theme_pack_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"theme_pack_weight_team_1_{expected_date}.yaml"


def test_export_theme_pack_weight_success():
    """Test successful export of theme pack weight."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file for the source theme pack weight
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as source_f:
            source_path = source_f.name
            yaml = YAML()
            theme_pack_data = {
                "preferred_thresholds": 1,
                "theme_pack_list": {"character_1": 100, "character_2": 50}
            }
            yaml.dump(theme_pack_data, source_f)

        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as export_f:
            export_path = export_f.name

        try:
            # Mock theme_list.build_team_weight_path to return the source file
            mock_theme_list.build_team_weight_path.return_value = source_path

            result = export_theme_pack_weight(1, export_path)
            assert result is True
            assert Path(export_path).exists()

            # Verify the exported YAML content
            yaml = YAML()
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = yaml.load(f)

            assert exported_data["preferred_thresholds"] == 1
            assert exported_data["theme_pack_list"]["character_1"] == 100
            assert exported_data["theme_pack_list"]["character_2"] == 50
        finally:
            Path(source_path).unlink()
            Path(export_path).unlink()


def test_export_theme_pack_weight_file_not_found():
    """Test export when source file doesn't exist."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as export_f:
            export_path = export_f.name

        try:
            # Mock theme_list.build_team_weight_path to return a non-existent path
            mock_theme_list.build_team_weight_path.return_value = "/nonexistent/path/theme_pack.yaml"

            result = export_theme_pack_weight(1, export_path)
            assert result is False
        finally:
            Path(export_path).unlink()


def test_import_theme_pack_weight_success():
    """Test successful import of theme pack weight."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file for the import
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as import_f:
            import_path = import_f.name
            yaml = YAML()
            import_data = {
                "preferred_thresholds": 2,
                "theme_pack_list": {"character_1": 200, "character_3": 75}
            }
            yaml.dump(import_data, import_f)

        # Create a temporary file for the target theme pack weight
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as target_f:
            target_path = target_f.name
            yaml = YAML()
            existing_data = {
                "preferred_thresholds": 1,
                "theme_pack_list": {"character_1": 100, "character_2": 50}
            }
            yaml.dump(existing_data, target_f)

        try:
            # Mock theme_list.build_team_weight_path to return the target file
            mock_theme_list.build_team_weight_path.return_value = target_path

            result = import_theme_pack_weight(import_path, 1)
            assert result is True

            # Verify the imported YAML content
            yaml = YAML()
            with open(target_path, 'r', encoding='utf-8') as f:
                imported_data = yaml.load(f)

            # Should have merged/replaced entries
            assert imported_data["preferred_thresholds"] == 2
            assert imported_data["theme_pack_list"]["character_1"] == 200
            assert imported_data["theme_pack_list"]["character_2"] == 50
            assert imported_data["theme_pack_list"]["character_3"] == 75
        finally:
            Path(import_path).unlink()
            Path(target_path).unlink()


def test_import_theme_pack_weight_create_new():
    """Test import when target file doesn't exist."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file for the import
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as import_f:
            import_path = import_f.name
            yaml = YAML()
            import_data = {
                "preferred_thresholds": 1,
                "theme_pack_list": {"character_1": 100}
            }
            yaml.dump(import_data, import_f)

        # Create a temporary directory for the target file
        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = str(Path(temp_dir) / "theme_pack_weight_team_1.yaml")

            try:
                # Mock theme_list.build_team_weight_path to return the target file
                mock_theme_list.build_team_weight_path.return_value = target_path

                result = import_theme_pack_weight(import_path, 1)
                assert result is True
                assert Path(target_path).exists()

                # Verify the imported YAML content
                yaml = YAML()
                with open(target_path, 'r', encoding='utf-8') as f:
                    imported_data = yaml.load(f)

                assert imported_data["preferred_thresholds"] == 1
                assert imported_data["theme_pack_list"]["character_1"] == 100
            finally:
                Path(import_path).unlink()


def test_import_theme_pack_weight_invalid_file():
    """Test import with invalid YAML file."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as import_f:
            import_path = import_f.name
            import_f.write("invalid: yaml: content: [")

        try:
            # Mock theme_list.build_team_weight_path
            mock_theme_list.build_team_weight_path.return_value = "/some/path/theme_pack.yaml"

            result = import_theme_pack_weight(import_path, 1)
            assert result is False
        finally:
            Path(import_path).unlink()


def test_import_theme_pack_weight_empty_file():
    """Test import with empty YAML file."""
    with patch('module.config.theme_pack_import_export.theme_list') as mock_theme_list:
        # Create a temporary file for the import (empty)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as import_f:
            import_path = import_f.name

        # Create a temporary file for the target theme pack weight
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as target_f:
            target_path = target_f.name
            yaml = YAML()
            existing_data = {
                "preferred_thresholds": 1,
                "theme_pack_list": {"character_1": 100}
            }
            yaml.dump(existing_data, target_f)

        try:
            # Mock theme_list.build_team_weight_path to return the target file
            mock_theme_list.build_team_weight_path.return_value = target_path

            result = import_theme_pack_weight(import_path, 1)
            # Empty file should be treated as no data to import, but still succeed
            assert result is True

            # Verify the target file is unchanged
            yaml = YAML()
            with open(target_path, 'r', encoding='utf-8') as f:
                imported_data = yaml.load(f)

            assert imported_data["preferred_thresholds"] == 1
            assert imported_data["theme_pack_list"]["character_1"] == 100
        finally:
            Path(import_path).unlink()
            Path(target_path).unlink()
