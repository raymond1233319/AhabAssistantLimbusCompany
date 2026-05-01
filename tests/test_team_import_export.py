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


def test_import_team_settings_with_minimal_fields():
    """Test that import_team_settings handles minimal fields correctly using model_construct."""
    from module.config.team_import_export import import_team_settings

    # Create a temporary YAML file with minimal fields
    # Since all TeamSetting fields have defaults, pydantic won't report missing fields
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        import_path = f.name
        yaml = YAML()
        # Only provide minimal fields
        minimal_data = {
            "team_system": 1,
            "team_number": 2,
            # Missing: shop_strategy, sinners_be_select, chosen_sinners, sinner_order, etc.
            # But all these have defaults, so pydantic will use them
        }
        yaml.dump(minimal_data, f)

    try:
        team_setting, theme_pack_weight, missing_fields = import_team_settings(import_path, 2)

        # Should return a valid TeamSetting object with defaults for missing fields
        assert team_setting is not None
        assert team_setting.team_system == 1
        assert team_setting.team_number == 2

        # Should have default values for fields not provided
        assert team_setting.shop_strategy == 0  # default value
        assert team_setting.sinners_be_select == 0  # default value
        assert team_setting.chosen_sinners == [0] * 12  # default value

        # Since all fields have defaults, missing_fields should be empty
        assert missing_fields == []

        # Should have no theme pack weight
        assert theme_pack_weight is None
    finally:
        Path(import_path).unlink()


def test_import_team_settings_with_theme_pack():
    """Test that import_team_settings correctly extracts custom_theme_pack_weight."""
    from module.config.team_import_export import import_team_settings

    # Create a temporary YAML file with theme pack weight
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        import_path = f.name
        yaml = YAML()
        data = {
            "team_system": 0,
            "team_number": 1,
            "shop_strategy": 0,
            "sinners_be_select": 0,
            "chosen_sinners": [0] * 12,
            "sinner_order": [0] * 12,
            "system_burn": False,
            "system_bleed": False,
            "system_tremor": False,
            "system_rupture": False,
            "system_poise": False,
            "system_sinking": False,
            "system_charge": False,
            "system_slash": False,
            "remark_name": "Test Team",
            "use_custom_theme_pack_weight": False,
            "custom_theme_pack_weight": {
                "preferred_thresholds": 1,
                "theme_pack_list": {"forgot": 1, "gambl": 2}
            }
        }
        yaml.dump(data, f)

    try:
        team_setting, theme_pack_weight, missing_fields = import_team_settings(import_path, 1)

        # Should return a valid TeamSetting object
        assert team_setting is not None
        assert team_setting.team_number == 1
        assert team_setting.remark_name == "Test Team"

        # Should have no missing fields
        assert missing_fields == []

        # Should extract theme pack weight
        assert theme_pack_weight is not None
        assert theme_pack_weight["preferred_thresholds"] == 1
        assert theme_pack_weight["theme_pack_list"]["forgot"] == 1
    finally:
        Path(import_path).unlink()
