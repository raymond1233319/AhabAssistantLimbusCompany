import datetime
import re
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML
from pydantic import ValidationError

from module.config import cfg, theme_list
from module.config.config_typing import TeamSetting
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

        # Exclude statistics fields and team_system from export
        stats_fields = ['total_mirror_time_hard', 'mirror_hard_count',
                       'total_mirror_time_normal', 'mirror_normal_count', 'team_system']
        for field in stats_fields:
            export_data.pop(field, None)

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


def import_team_settings(file_path: str, team_num: int) -> tuple[Optional[TeamSetting], Optional[dict], list[str]]:
    """Import team settings from YAML file.

    Args:
        file_path: Path to the YAML file to import
        team_num: Team number (used for context, not validation)

    Returns:
        Tuple of (TeamSetting, theme_pack_weight, missing_fields)
        - TeamSetting: Parsed team settings, or None if parsing failed
        - theme_pack_weight: Custom theme pack weight dict if present, or None
        - missing_fields: List of missing required fields, or empty list if all fields present
    """
    try:
        yaml = YAML()
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)

        if not data:
            return None, None, ["File is empty"]

        theme_pack_weight = data.pop('custom_theme_pack_weight', None)

        try:
            team_setting = TeamSetting(**data)
            return team_setting, theme_pack_weight, []
        except ValidationError as e:
            missing_fields = [err['loc'][0] for err in e.errors() if err['type'] == 'missing']
            if missing_fields:
                # Create with defaults for missing fields using model_construct
                team_setting = TeamSetting.model_construct(**data)
                return team_setting, theme_pack_weight, missing_fields
            else:
                log.error(f"Validation error: {e}")
                return None, None, [str(e)]
    except Exception as e:
        log.error(f"Failed to import team settings: {e}")
        return None, None, [str(e)]


def apply_team_settings(team_num: int, team_setting: TeamSetting, theme_pack_weight: Optional[dict]) -> None:
    """Apply imported team settings to configuration."""
    cfg.config.teams[str(team_num)] = team_setting

    if theme_pack_weight:
        theme_pack_weight_path = Path(theme_list.build_team_weight_path(team_num))
        theme_pack_weight_path.parent.mkdir(parents=True, exist_ok=True)

        yaml = YAML()
        with open(theme_pack_weight_path, 'w', encoding='utf-8') as f:
            yaml.dump(theme_pack_weight, f)

        log.info(f"Created/updated theme pack weight file for team {team_num}")

    cfg.save()
    log.info(f"Applied settings for team {team_num}")
