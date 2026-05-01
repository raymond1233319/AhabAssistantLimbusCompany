import datetime
from unittest.mock import MagicMock, patch
from module.config.team_import_export import generate_team_export_filename
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
