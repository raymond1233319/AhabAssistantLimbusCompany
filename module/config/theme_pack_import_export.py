import datetime
import re
from pathlib import Path

from ruamel.yaml import YAML

from module.config import cfg, theme_list
from module.logger import log


def generate_theme_pack_export_filename(team_num: int) -> str:
    """Generate export filename for theme pack weight.

    Args:
        team_num: Team number

    Returns:
        Filename in format: theme_pack_weight_team_{remark_name}_{date}.yaml
        or theme_pack_weight_team_{team_num}_{date}.yaml if no remark_name
    """
    team_setting = cfg.config.teams.get(str(team_num))
    remark_name = team_setting.remark_name if team_setting else None

    date_str = datetime.date.today().isoformat()

    if remark_name:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', remark_name)
        return f"theme_pack_weight_team_{safe_name}_{date_str}.yaml"
    else:
        return f"theme_pack_weight_team_{team_num}_{date_str}.yaml"


def export_theme_pack_weight(team_num: int, file_path: str) -> bool:
    """Export theme pack weight to YAML file.

    Args:
        team_num: Team number
        file_path: Path to export the theme pack weight to

    Returns:
        True on success, False on failure
    """
    try:
        theme_pack_weight_path = theme_list.build_team_weight_path(team_num)

        if not Path(theme_pack_weight_path).exists():
            log.error(f"Theme pack weight file not found for team {team_num}")
            return False

        yaml = YAML()
        with open(theme_pack_weight_path, 'r', encoding='utf-8') as f:
            theme_pack_data = yaml.load(f)

        if not theme_pack_data:
            log.error(f"Theme pack weight file is empty for team {team_num}")
            return False

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(theme_pack_data, f)

        log.info(f"Exported theme pack weight for team {team_num} to {file_path}")
        return True
    except Exception as e:
        log.error(f"Failed to export theme pack weight: {e}")
        return False


def _deep_merge_dicts(existing: dict, import_data: dict) -> dict:
    """Deep merge import_data into existing dictionary.

    Args:
        existing: Existing dictionary
        import_data: Dictionary to merge in

    Returns:
        Merged dictionary
    """
    result = existing.copy()
    for key, value in import_data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def import_theme_pack_weight(file_path: str, team_num: int) -> bool:
    """Import theme pack weight from YAML file.

    Args:
        file_path: Path to the YAML file to import
        team_num: Team number (used for context)

    Returns:
        True on success, False on failure
    """
    try:
        yaml = YAML()

        # Load import data
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = yaml.load(f)

        if not import_data:
            log.warning(f"Import file is empty for team {team_num}")
            return True

        # Load existing theme pack weight or create empty dict
        theme_pack_weight_path = theme_list.build_team_weight_path(team_num)
        target_path = Path(theme_pack_weight_path)

        if target_path.exists():
            with open(theme_pack_weight_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.load(f)
                if not existing_data:
                    existing_data = {}
        else:
            existing_data = {}

        # Merge/replace entries from import
        if isinstance(import_data, dict):
            existing_data = _deep_merge_dicts(existing_data, import_data)
        else:
            log.error(f"Import data is not a dictionary for team {team_num}")
            return False

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Save back to theme_pack_weight_team_{team_num}.yaml
        with open(theme_pack_weight_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f)

        log.info(f"Imported theme pack weight for team {team_num} from {file_path}")
        return True
    except Exception as e:
        log.error(f"Failed to import theme pack weight: {e}")
        return False
