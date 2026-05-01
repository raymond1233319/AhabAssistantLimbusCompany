import datetime
import re
from pathlib import Path

from ruamel.yaml import YAML

from module.config import cfg, theme_list
from module.logger import log


def generate_team_export_filename(team_num: int) -> str:
    """Generate export filename for team settings."""
    team_setting = cfg.config.teams.get(str(team_num))
    remark_name = team_setting.remark_name if team_setting else None

    date_str = datetime.date.today().isoformat()

    if remark_name:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', remark_name)
        return f"team_settings_{safe_name}_{date_str}.yaml"
    else:
        return f"team_settings_team_{team_num}_{date_str}.yaml"


def export_team_settings(team_num: int, file_path: str) -> bool:
    """Export team settings to YAML file."""
    try:
        team_setting = cfg.config.teams.get(str(team_num))
        if not team_setting:
            log.error(f"Team {team_num} not found")
            return False

        yaml = YAML()
        export_data = team_setting.model_dump()

        theme_pack_weight_path = theme_list.build_team_weight_path(team_num)
        if Path(theme_pack_weight_path).exists():
            with open(theme_pack_weight_path, 'r', encoding='utf-8') as f:
                theme_pack_data = yaml.load(f)
                if theme_pack_data:
                    export_data['custom_theme_pack_weight'] = theme_pack_data

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(export_data, f)

        log.info(f"Exported team {team_num} settings to {file_path}")
        return True
    except Exception as e:
        log.error(f"Failed to export team settings: {e}")
        return False
