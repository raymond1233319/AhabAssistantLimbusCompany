import datetime
from unittest.mock import MagicMock, patch
from module.config.team_import_export import generate_team_export_filename
from module.config import cfg

def test_generate_team_export_filename_with_remark_name():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="MyTeam")
        }
        with patch('module.config.team_import_export.datetime') as mock_datetime:
            mock_datetime.date.today.return_value.isoformat.return_value = "2026-05-01"
            result = generate_team_export_filename(1)
            assert result == "team_settings_MyTeam_2026-05-01.yaml"

def test_generate_team_export_filename_without_remark_name():
    with patch('module.config.team_import_export.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name=None)
        }
        with patch('module.config.team_import_export.datetime') as mock_datetime:
            mock_datetime.date.today.return_value.isoformat.return_value = "2026-05-01"
            result = generate_team_export_filename(1)
            assert result == "team_settings_team_1_2026-05-01.yaml"
