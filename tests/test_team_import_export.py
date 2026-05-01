import datetime
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from ruamel.yaml import YAML
from module.config.team_import_export import generate_team_export_filename, export_team_settings
from module.config import cfg

def test_generate_team_export_filename_with_remark_name():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="MyTeam")
        }
        result = generate_team_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"team_settings_MyTeam_{expected_date}.yaml"

def test_generate_team_export_filename_without_remark_name():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name=None)
        }
        result = generate_team_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"team_settings_team_1_{expected_date}.yaml"

def test_generate_team_export_filename_team_not_found():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {}
        result = generate_team_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"team_settings_team_1_{expected_date}.yaml"

def test_generate_team_export_filename_with_special_characters():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name='Team<>:"/\\|?*Name')
        }
        result = generate_team_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"team_settings_Team_________Name_{expected_date}.yaml"

def test_generate_team_export_filename_with_empty_remark_name():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="")
        }
        result = generate_team_export_filename(1)
        expected_date = datetime.date.today().isoformat()
        assert result == f"team_settings_team_1_{expected_date}.yaml"

def test_export_team_settings_without_theme_pack():
    with patch('module.config.team_import_export.cfg') as mock_cfg, \
         patch('module.config.team_import_export.theme_list') as mock_theme_list:
        mock_team = MagicMock()
        mock_team.model_dump.return_value = {"team_system": 0, "team_number": 1}
        mock_cfg.config.teams = {"1": mock_team}

        # Mock theme_list.build_team_weight_path to return a non-existent path
        mock_theme_list.build_team_weight_path.return_value = "/nonexistent/path/theme_pack.yaml"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            file_path = f.name

        try:
            result = export_team_settings(1, file_path)
            assert result is True
            assert Path(file_path).exists()

            # Verify the exported YAML content
            yaml = YAML()
            with open(file_path, 'r', encoding='utf-8') as f:
                exported_data = yaml.load(f)

            assert exported_data == {"team_system": 0, "team_number": 1}
            assert 'custom_theme_pack_weight' not in exported_data
        finally:
            Path(file_path).unlink()


def test_export_team_settings_with_theme_pack():
    with patch('module.config.team_import_export.cfg') as mock_cfg, \
         patch('module.config.team_import_export.theme_list') as mock_theme_list:
        mock_team = MagicMock()
        mock_team.model_dump.return_value = {"team_system": 0, "team_number": 1}
        mock_cfg.config.teams = {"1": mock_team}

        # Create a temporary file for the theme pack weight
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as theme_f:
            theme_pack_path = theme_f.name
            yaml = YAML()
            theme_pack_data = {"character_1": 100, "character_2": 50}
            yaml.dump(theme_pack_data, theme_f)

        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as export_f:
            export_path = export_f.name

        try:
            # Mock theme_list.build_team_weight_path to return the theme pack file
            mock_theme_list.build_team_weight_path.return_value = theme_pack_path

            result = export_team_settings(1, export_path)
            assert result is True
            assert Path(export_path).exists()

            # Verify the exported YAML content includes the theme pack weight
            yaml = YAML()
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = yaml.load(f)

            assert exported_data["team_system"] == 0
            assert exported_data["team_number"] == 1
            assert 'custom_theme_pack_weight' in exported_data
            assert exported_data['custom_theme_pack_weight'] == {"character_1": 100, "character_2": 50}
        finally:
            Path(theme_pack_path).unlink()
            Path(export_path).unlink()
