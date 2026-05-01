import datetime
import re

from module.config import cfg


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
