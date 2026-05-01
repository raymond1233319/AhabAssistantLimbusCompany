# Team Settings and Theme Pack Import/Export Design

**Date:** 2026-05-01  
**Feature:** Config Import/Export for Team Settings and Theme Pack Weights

## Overview

Add import/export functionality for team settings and theme pack weights, allowing users to:

- Export/import complete team configurations (including custom theme pack weights)
- Export/import theme pack weight configurations
- Create new teams from imported configuration files

## Requirements

### Team Settings Import/Export

- **Export**: Full TeamSetting object to YAML, including custom theme pack weight file if present
- **Import**: Load TeamSetting from YAML with validation and optional theme pack weight
- **Filename format**: `team_settings_{remark_name}_{date}.yaml` (fallback to `team_settings_team_{team_num}_{date}.yaml` if remark_name is empty)
- **Location**: User chooses save/load location via file dialog
- **Validation**: Check for missing fields, show warning dialog with field list, allow user to continue or cancel
- **Confirmation**: Show confirmation dialog before applying imported settings
- **Theme pack weight handling**:
  - Export includes theme pack weight file if it exists (regardless of `use_custom_theme_pack_weight` flag)
  - Import creates/updates theme pack weight file if included, but does NOT automatically enable the flag

### Theme Pack Weight Import/Export

- **Export**: Export entire `theme_pack_weight_team_N.yaml` file as-is (no filtering)
- **Import**: Replace entries that exist in import file, keep others unchanged
- **Filename format**: `theme_pack_weight_team_{remark_name}_{date}.yaml`
- **Location**: User chooses save/load location via file dialog

### Create Team from File

- **Feature**: Option to create a new team from an imported configuration file
- **Location**: In team creation dialog/interface
- **Behavior**: Import settings and create new team entry

## Architecture

### Module Structure

```
module/config/
├── config.py (existing)
├── config_typing.py (existing)
├── team_import_export.py (new)
└── theme_pack_import_export.py (new)
```

**team_import_export.py** handles:

- Exporting TeamSetting object to YAML
- Checking if custom theme pack weight file exists and including it
- Importing TeamSetting from YAML with validation
- Creating theme pack weight file if included in import

**theme_pack_import_export.py** handles:

- Exporting theme pack weights to YAML
- Importing theme pack weights from YAML
- Merging imported entries with existing configuration

### UI Changes

**TeamSettingCard** (`app/team_setting_card.py`):

- Add "Export Settings" button (PrimaryPushButton)
- Add "Import Settings" button (PushButton)
- Position: Add to existing button row or create new row

**ThemePackSettingDialog** (`app/theme_pack_setting_interface.py`):

- Add "Export Theme Pack Weights" button
- Add "Import Theme Pack Weights" button
- Position: Add to button layout at bottom of dialog

**Team Creation Interface**:

- Add "Create Team from File" button/option
- Opens file dialog to select configuration file
- Creates new team with imported settings

## Data Flow

### Team Settings Export Flow

1. User clicks "Export Settings" button in TeamSettingCard
2. Generate filename: `team_settings_{remark_name}_{date}.yaml`
   - If remark*name is None/empty: use `team_settings_team*{team*num}*{date}.yaml`
3. Open QFileDialog.getSaveFileName() for save location
4. Serialize TeamSetting object to YAML using `model_dump()`
5. Check if `theme_pack_weight/theme_pack_weight_team_{team_num}.yaml` exists
6. If exists, load it and include under `custom_theme_pack_weight` key in export
7. Save combined YAML file using ruamel.yaml
8. Show success/error message

### Team Settings Import Flow

1. User clicks "Import Settings" button in TeamSettingCard
2. Open QFileDialog.getOpenFileName() to select YAML file
3. Load and parse YAML file
4. Extract TeamSetting fields from YAML
5. Validate using pydantic: `TeamSetting(**data)`
6. If validation fails (missing fields):
   - Collect list of missing fields
   - Show warning dialog: "Missing fields: {field_list}. Continue with default values?"
   - User chooses: Continue or Cancel
7. Show confirmation dialog: "Import settings for Team {team_num}? This will overwrite current settings."
8. If confirmed:
   - Apply TeamSetting to `cfg.config.teams[str(team_num)]`
   - If `custom_theme_pack_weight` key exists in import:
     - Create/update `theme_pack_weight/theme_pack_weight_team_{team_num}.yaml`
     - Do NOT automatically enable `use_custom_theme_pack_weight` flag
   - Call `cfg.save()` to persist changes
9. Show success message

### Theme Pack Weight Export Flow

1. User clicks "Export Theme Pack Weights" button in ThemePackSettingDialog
2. Generate filename: `theme_pack_weight_team_{remark_name}_{date}.yaml`
3. Open QFileDialog.getSaveFileName() for save location
4. Load `theme_pack_weight/theme_pack_weight_team_{team_num}.yaml`
5. Write entire file to user-chosen location
6. Show success/error message

### Theme Pack Weight Import Flow

1. User clicks "Import Theme Pack Weights" button in ThemePackSettingDialog
2. Open QFileDialog.getOpenFileName() to select YAML file
3. Load YAML from selected file
4. Load existing `theme_pack_weight/theme_pack_weight_team_{team_num}.yaml` (or create empty dict if doesn't exist)
5. Merge/replace entries from import file into existing configuration
6. Save updated configuration back to `theme_pack_weight/theme_pack_weight_team_{team_num}.yaml`
7. Show success message

### Create Team from File Flow

1. User clicks "Create Team from File" button in team creation interface
2. Open QFileDialog.getOpenFileName() to select YAML file
3. Load and parse YAML file (same as Team Settings Import Flow steps 3-6)
4. Show dialog to let user choose team number (1-20)
5. If team number already exists, show confirmation: "Team {team_num} already exists. Overwrite?"
6. Create/update team entry in `cfg.config.teams[str(team_num)]`
7. Apply imported settings (including theme pack weight if present)
8. Show success message

## Module Functions

### team_import_export.py

```python
def export_team_settings(team_num: int, file_path: str) -> bool
    """
    Export team settings to YAML file.

    Args:
        team_num: Team number (1-20)
        file_path: Full path to save file

    Returns:
        True if successful, False otherwise

    Process:
        - Get TeamSetting from cfg.config.teams[str(team_num)]
        - Serialize to dict using model_dump()
        - Check if theme_pack_weight_team_{team_num}.yaml exists
        - If exists, load and add under 'custom_theme_pack_weight' key
        - Write to file_path using ruamel.yaml
    """

def import_team_settings(file_path: str, team_num: int) -> tuple[TeamSetting | None, dict | None, list[str]]
    """
    Import team settings from YAML file.

    Args:
        file_path: Full path to import file
        team_num: Target team number (for validation)

    Returns:
        Tuple of (TeamSetting object, theme_pack_weight dict, missing_fields list)
        - TeamSetting: Validated TeamSetting object, or None if validation failed critically
        - theme_pack_weight: Dict of theme pack weights if present in import, or None
        - missing_fields: List of field names that were missing (empty if all present)

    Process:
        - Load YAML from file_path
        - Extract TeamSetting fields
        - Try to validate using pydantic TeamSetting(**data)
        - Catch validation errors, collect missing fields
        - Extract custom_theme_pack_weight if present
        - Return tuple
    """

def apply_team_settings(team_num: int, team_setting: TeamSetting, theme_pack_weight: dict | None) -> None
    """
    Apply imported team settings to configuration.

    Args:
        team_num: Team number to update
        team_setting: Validated TeamSetting object
        theme_pack_weight: Optional theme pack weight dict

    Process:
        - Update cfg.config.teams[str(team_num)] = team_setting
        - If theme_pack_weight provided:
            - Ensure theme_pack_weight directory exists
            - Save to theme_pack_weight/theme_pack_weight_team_{team_num}.yaml
        - Call cfg.save() to persist
    """

def generate_team_export_filename(team_num: int) -> str
    """
    Generate export filename for team settings.

    Args:
        team_num: Team number

    Returns:
        Filename string: team_settings_{remark_name}_{date}.yaml
        Falls back to team_settings_team_{team_num}_{date}.yaml if remark_name is empty
    """
```

### theme_pack_import_export.py

```python
def export_theme_pack_weight(team_num: int, file_path: str) -> bool
    """
    Export theme pack weight configuration to YAML file.

    Args:
        team_num: Team number
        file_path: Full path to save file

    Returns:
        True if successful, False otherwise

    Process:
        - Load theme_pack_weight/theme_pack_weight_team_{team_num}.yaml
        - Write entire file to file_path using ruamel.yaml
    """

def import_theme_pack_weight(file_path: str, team_num: int) -> bool
    """
    Import theme pack weight configuration from YAML file.

    Args:
        file_path: Full path to import file
        team_num: Target team number

    Returns:
        True if successful, False otherwise

    Process:
        - Load YAML from file_path
        - Load existing theme_pack_weight/theme_pack_weight_team_{team_num}.yaml
          (or create empty dict if doesn't exist)
        - Merge/replace entries from import into existing config
        - Ensure theme_pack_weight directory exists
        - Save updated config back to theme_pack_weight/theme_pack_weight_team_{team_num}.yaml
    """

def generate_theme_pack_export_filename(team_num: int) -> str
    """
    Generate export filename for theme pack weights.

    Args:
        team_num: Team number

    Returns:
        Filename string: theme_pack_weight_team_{remark_name}_{date}.yaml
    """
```

## Error Handling

### File Operations

- **Invalid YAML syntax**: Show error dialog "Invalid YAML file format"
- **File not found**: Show error dialog "File not found: {path}"
- **Permission errors**: Show error dialog "Cannot write to file: {path}"
- **Empty/corrupt files**: Show error dialog with details

### Validation

- **Missing required fields**: Show warning dialog with field list, allow continue with defaults or cancel
- **Invalid field types**: Show error dialog "Invalid data type for field {field_name}: expected {type}"
- **Pydantic validation errors**: Catch ValidationError, extract user-friendly messages

### Edge Cases

- **Empty remark_name**: Use fallback filename `team_settings_team_{team_num}_{date}.yaml`
- **Team doesn't exist**: Create new team entry in `cfg.config.teams`
- **Theme pack weight file doesn't exist**: Skip including it in export (no error)
- **Import without theme pack weight**: Just import team settings, don't touch weight file
- **Import with theme pack weight but team_num mismatch**: Use target team_num, not imported one
- **Invalid team_num**: Validate team_num is in valid range (1-20), show error if not

### Data Integrity

- **Backup**: Use existing config backup mechanism (config.yaml.bak)
- **Validation**: Validate team_num is valid (1-20 range)
- **Theme pack keys**: Validate theme pack weight keys are valid theme pack names (optional, can be lenient)

## UI Dialog Messages

### Validation Warning

```
Title: "Missing Fields"
Message: "The following fields are missing from the import file:
- {field_1}
- {field_2}
- ...

Default values will be used for these fields. Continue?"
Buttons: [Continue] [Cancel]
```

### Import Confirmation

```
Title: "Confirm Import"
Message: "Import settings for Team {team_num} ({remark_name})?
This will overwrite current settings."
Buttons: [Import] [Cancel]
```

### Success Messages

- "Settings exported successfully to {filename}"
- "Settings imported successfully"
- "Theme pack weights exported successfully"
- "Theme pack weights imported successfully"

### Error Messages

- "Failed to export: {error_message}"
- "Failed to import: {error_message}"
- "Invalid YAML file format"
- "File not found: {path}"
- "Cannot write to file: {path}"

## File Format

### Team Settings Export Format

```yaml
# TeamSetting fields
team_system: 0
team_number: 1
shop_strategy: 0
sinners_be_select: 0
chosen_sinners: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
sinner_order: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# ... all other TeamSetting fields ...
remark_name: "My Team"
use_custom_theme_pack_weight: true

# Optional: included if theme_pack_weight_team_N.yaml exists
custom_theme_pack_weight:
  preferred_thresholds: 1
  theme_pack_list:
    forgot: 1
    gambl: 2
    # ... other theme packs ...
  theme_pack_list_hard:
    seismic: 1
    # ... other hard theme packs ...
```

### Theme Pack Weight Export Format

```yaml
preferred_thresholds: 0

theme_pack_list:
  forgot: 1
  gambl: 2
  und: 1
  # ... other theme packs ...
theme_pack_list_hard:
  seismic: 1
  extrenal: 2
  # ... other hard theme packs ...
theme_pack_list_cn:
  # ... Chinese theme packs if present ...
theme_pack_list_hard_cn:
  # ... Chinese hard theme packs if present ...
```

## Implementation Notes

- Use `ruamel.yaml` for YAML operations (consistent with existing code)
- Use `QFileDialog.getSaveFileName()` and `QFileDialog.getOpenFileName()` for file dialogs
- Use existing `MessageBoxConfirm` from `app.card.messagebox_custom` for confirmation dialogs
- Use `BaseInfoBar` for success/error messages
- Follow existing code style and patterns in the codebase
- Ensure proper error handling and user feedback at every step
- Use `datetime.date.today().isoformat()` for date in filename
- Sanitize remark_name for filename (remove invalid characters)

## Testing Considerations

- Test with valid and invalid YAML files
- Test with missing fields
- Test with empty remark_name
- Test with non-existent theme pack weight files
- Test import/export round-trip (export then import should preserve data)
- Test with special characters in remark_name
- Test file permission errors
- Test with corrupt YAML files
- Test "Create Team from File" with various team numbers
