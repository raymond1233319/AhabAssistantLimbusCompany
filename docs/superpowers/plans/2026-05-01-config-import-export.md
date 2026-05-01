# Config Import/Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add import/export functionality for team settings and theme pack weights

**Architecture:** Two new modules in `module/config/` handle import/export logic. UI buttons in TeamSettingCard and ThemePackSettingDialog call these modules. Validation uses pydantic, file dialogs use QFileDialog, user confirmation via MessageBoxConfirm.

**Tech Stack:** Python, PySide6, ruamel.yaml, pydantic

---

## File Structure

**New Files:**
- `module/config/team_import_export.py` - Team settings import/export functions
- `module/config/theme_pack_import_export.py` - Theme pack weight import/export functions

**Modified Files:**
- `app/team_setting_card.py` - Add import/export buttons and handlers
- `app/theme_pack_setting_interface.py` - Add import/export buttons and handlers

---

### Task 1: Create team_import_export module with export function

**Files:**
- Create: `module/config/team_import_export.py`

- [ ] **Step 1: Write test for generate_team_export_filename**

Create `tests/test_team_import_export.py`:

```python
import datetime
from unittest.mock import MagicMock, patch
from module.config.team_import_export import generate_team_export_filename
from module.config import cfg

def test_generate_team_export_filename_with_remark_name():
    with patch('module.config.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name="MyTeam")
        }
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-05-01"
            result = generate_team_export_filename(1)
            assert result == "team_settings_MyTeam_2026-05-01.yaml"

def test_generate_team_export_filename_without_remark_name():
    with patch('module.config.cfg') as mock_cfg:
        mock_cfg.config.teams = {
            "1": MagicMock(remark_name=None)
        }
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-05-01"
            result = generate_team_export_filename(1)
            assert result == "team_settings_team_1_2026-05-01.yaml"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_team_import_export.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'module.config.team_import_export'"

- [ ] **Step 3: Create module with generate_team_export_filename**

Create `module/config/team_import_export.py`:

```python
import datetime
import re
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_team_import_export.py::test_generate_team_export_filename_with_remark_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/team_import_export.py tests/test_team_import_export.py
git commit -m "feat: add team export filename generation"
```

---

### Task 2: Add export_team_settings function

**Files:**
- Modify: `module/config/team_import_export.py`

- [ ] **Step 1: Write test for export_team_settings**

Add to `tests/test_team_import_export.py`:

```python
from pathlib import Path
import tempfile
from module.config.team_import_export import export_team_settings

def test_export_team_settings_without_theme_pack():
    with patch('module.config.cfg') as mock_cfg:
        mock_team = MagicMock()
        mock_team.model_dump.return_value = {"team_system": 0, "team_number": 1}
        mock_cfg.config.teams = {"1": mock_team}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            file_path = f.name
        
        try:
            result = export_team_settings(1, file_path)
            assert result is True
            assert Path(file_path).exists()
        finally:
            Path(file_path).unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_team_import_export.py::test_export_team_settings_without_theme_pack -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement export_team_settings**

Add to `module/config/team_import_export.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_team_import_export.py::test_export_team_settings_without_theme_pack -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/team_import_export.py tests/test_team_import_export.py
git commit -m "feat: add team settings export function"
```

---

### Task 3: Add import_team_settings function

**Files:**
- Modify: `module/config/team_import_export.py`

- [ ] **Step 1: Write test for import_team_settings**

Add to `tests/test_team_import_export.py`:

```python
def test_import_team_settings_valid():
    yaml_content = """
team_system: 1
team_number: 2
shop_strategy: 0
remark_name: "Test Team"
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f.write(yaml_content)
        file_path = f.name
    
    try:
        team_setting, theme_pack, missing = import_team_settings(file_path, 2)
        assert team_setting is not None
        assert team_setting.team_system == 1
        assert theme_pack is None
        assert len(missing) == 0
    finally:
        Path(file_path).unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_team_import_export.py::test_import_team_settings_valid -v`
Expected: FAIL

- [ ] **Step 3: Implement import_team_settings**

Add to `module/config/team_import_export.py`:

```python
from pydantic import ValidationError

def import_team_settings(file_path: str, team_num: int) -> tuple[Optional[TeamSetting], Optional[dict], list[str]]:
    """Import team settings from YAML file."""
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
                team_setting = TeamSetting(**data)
                return team_setting, theme_pack_weight, missing_fields
            else:
                log.error(f"Validation error: {e}")
                return None, None, [str(e)]
    except Exception as e:
        log.error(f"Failed to import team settings: {e}")
        return None, None, [str(e)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_team_import_export.py::test_import_team_settings_valid -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/team_import_export.py tests/test_team_import_export.py
git commit -m "feat: add team settings import function"
```

---

### Task 4: Add apply_team_settings function

**Files:**
- Modify: `module/config/team_import_export.py`

- [ ] **Step 1: Write test for apply_team_settings**

Add to `tests/test_team_import_export.py`:

```python
def test_apply_team_settings():
    with patch('module.config.cfg') as mock_cfg:
        mock_cfg.config.teams = {}
        mock_cfg.save = MagicMock()
        
        team_setting = TeamSetting(team_system=1, team_number=2)
        apply_team_settings(2, team_setting, None)
        
        assert "2" in mock_cfg.config.teams
        mock_cfg.save.assert_called_once()
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_team_import_export.py::test_apply_team_settings -v`
Expected: FAIL

- [ ] **Step 3: Implement apply_team_settings**

Add to `module/config/team_import_export.py`:

```python
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
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_team_import_export.py::test_apply_team_settings -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/team_import_export.py tests/test_team_import_export.py
git commit -m "feat: add apply team settings function"
```

---

### Task 5: Create theme_pack_import_export module

**Files:**
- Create: `module/config/theme_pack_import_export.py`

- [ ] **Step 1: Write test for generate_theme_pack_export_filename**

Create `tests/test_theme_pack_import_export.py`:

```python
from unittest.mock import MagicMock, patch
from module.config.theme_pack_import_export import generate_theme_pack_export_filename

def test_generate_theme_pack_export_filename():
    with patch('module.config.cfg') as mock_cfg:
        mock_cfg.config.teams = {"1": MagicMock(remark_name="MyTeam")}
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = "2026-05-01"
            result = generate_theme_pack_export_filename(1)
            assert result == "theme_pack_weight_team_MyTeam_2026-05-01.yaml"
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_theme_pack_import_export.py -v`
Expected: FAIL

- [ ] **Step 3: Create module**

Create `module/config/theme_pack_import_export.py`:

```python
import datetime
import re
from pathlib import Path

from ruamel.yaml import YAML

from module.config import cfg, theme_list
from module.logger import log


def generate_theme_pack_export_filename(team_num: int) -> str:
    """Generate export filename for theme pack weights."""
    team_setting = cfg.config.teams.get(str(team_num))
    remark_name = team_setting.remark_name if team_setting else None
    
    date_str = datetime.date.today().isoformat()
    
    if remark_name:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', remark_name)
        return f"theme_pack_weight_team_{safe_name}_{date_str}.yaml"
    else:
        return f"theme_pack_weight_team_{team_num}_{date_str}.yaml"
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_theme_pack_import_export.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/theme_pack_import_export.py tests/test_theme_pack_import_export.py
git commit -m "feat: add theme pack export filename generation"
```

---

### Task 6: Add theme pack export/import functions

**Files:**
- Modify: `module/config/theme_pack_import_export.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_theme_pack_import_export.py`:

```python
import tempfile
from module.config.theme_pack_import_export import export_theme_pack_weight, import_theme_pack_weight

def test_export_theme_pack_weight():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        file_path = f.name
    
    try:
        result = export_theme_pack_weight(1, file_path)
        assert result is True
    finally:
        Path(file_path).unlink()

def test_import_theme_pack_weight():
    yaml_content = """
preferred_thresholds: 1
theme_pack_list:
  forgot: 2
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f.write(yaml_content)
        file_path = f.name
    
    try:
        result = import_theme_pack_weight(file_path, 1)
        assert result is True
    finally:
        Path(file_path).unlink()
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_theme_pack_import_export.py -v`
Expected: FAIL

- [ ] **Step 3: Implement functions**

Add to `module/config/theme_pack_import_export.py`:

```python
def export_theme_pack_weight(team_num: int, file_path: str) -> bool:
    """Export theme pack weight configuration to YAML file."""
    try:
        theme_pack_weight_path = theme_list.build_team_weight_path(team_num)
        
        if not Path(theme_pack_weight_path).exists():
            log.error(f"Theme pack weight file not found for team {team_num}")
            return False
        
        yaml = YAML()
        with open(theme_pack_weight_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        
        log.info(f"Exported theme pack weights for team {team_num} to {file_path}")
        return True
    except Exception as e:
        log.error(f"Failed to export theme pack weights: {e}")
        return False


def import_theme_pack_weight(file_path: str, team_num: int) -> bool:
    """Import theme pack weight configuration from YAML file."""
    try:
        yaml = YAML()
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = yaml.load(f)
        
        if not import_data:
            log.error("Import file is empty")
            return False
        
        theme_pack_weight_path = Path(theme_list.build_team_weight_path(team_num))
        theme_pack_weight_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_data = {}
        if theme_pack_weight_path.exists():
            with open(theme_pack_weight_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.load(f) or {}
        
        for key, value in import_data.items():
            if isinstance(value, dict) and key in existing_data and isinstance(existing_data[key], dict):
                existing_data[key].update(value)
            else:
                existing_data[key] = value
        
        with open(theme_pack_weight_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f)
        
        log.info(f"Imported theme pack weights for team {team_num}")
        return True
    except Exception as e:
        log.error(f"Failed to import theme pack weights: {e}")
        return False
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_theme_pack_import_export.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add module/config/theme_pack_import_export.py tests/test_theme_pack_import_export.py
git commit -m "feat: add theme pack import/export functions"
```

---

### Task 7: Add export button to TeamSettingCard

**Files:**
- Modify: `app/team_setting_card.py`

- [ ] **Step 1: Add import statements**

Add to imports in `app/team_setting_card.py`:

```python
from PySide6.QtWidgets import QFileDialog
from module.config.team_import_export import export_team_settings, generate_team_export_filename
from app.card.messagebox_custom import BaseInfoBar
from qfluentwidgets import InfoBarPosition
```

- [ ] **Step 2: Add export button in __init_card**

Find the button initialization section and add:

```python
self.export_button = PrimaryPushButton(self.tr("导出设置"))
self.export_button.clicked.connect(self.on_export_settings)
```

- [ ] **Step 3: Add button to layout**

In `__init_layout`, add button to appropriate layout:

```python
self.setting_layout.addWidget(self.export_button)
```

- [ ] **Step 4: Implement on_export_settings handler**

Add method to TeamSettingCard class:

```python
def on_export_settings(self):
    """Handle export settings button click."""
    default_filename = generate_team_export_filename(self.team_num)
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        self.tr("导出队伍设置"),
        default_filename,
        "YAML Files (*.yaml *.yml)"
    )
    
    if file_path:
        success = export_team_settings(self.team_num, file_path)
        if success:
            BaseInfoBar.success(
                title=self.tr("导出成功"),
                content=self.tr(f"设置已导出到 {file_path}"),
                parent=self,
                position=InfoBarPosition.TOP
            )
        else:
            BaseInfoBar.error(
                title=self.tr("导出失败"),
                content=self.tr("导出设置时发生错误"),
                parent=self,
                position=InfoBarPosition.TOP
            )
```

- [ ] **Step 5: Test manually**

Run: `uv run main.py`
Navigate to team settings, click export button, verify file dialog opens and export works

- [ ] **Step 6: Commit**

```bash
git add app/team_setting_card.py
git commit -m "feat: add export button to TeamSettingCard"
```

---

### Task 8: Add import button to TeamSettingCard

**Files:**
- Modify: `app/team_setting_card.py`

- [ ] **Step 1: Add import statements**

Add to imports:

```python
from module.config.team_import_export import import_team_settings, apply_team_settings
from app.card.messagebox_custom import MessageBoxConfirm
```

- [ ] **Step 2: Add import button**

In `__init_card`:

```python
self.import_button = PushButton(self.tr("导入设置"))
self.import_button.clicked.connect(self.on_import_settings)
```

- [ ] **Step 3: Add to layout**

In `__init_layout`:

```python
self.setting_layout.addWidget(self.import_button)
```

- [ ] **Step 4: Implement on_import_settings handler**

Add method:

```python
def on_import_settings(self):
    """Handle import settings button click."""
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        self.tr("导入队伍设置"),
        "",
        "YAML Files (*.yaml *.yml)"
    )
    
    if not file_path:
        return
    
    team_setting, theme_pack, missing_fields = import_team_settings(file_path, self.team_num)
    
    if team_setting is None:
        BaseInfoBar.error(
            title=self.tr("导入失败"),
            content=self.tr("无法读取配置文件"),
            parent=self,
            position=InfoBarPosition.TOP
        )
        return
    
    if missing_fields:
        msg = self.tr("以下字段缺失:\n") + "\n".join(f"- {f}" for f in missing_fields)
        msg += "\n\n" + self.tr("将使用默认值。是否继续?")
        box = MessageBoxConfirm(self.tr("缺失字段"), msg, self)
        if not box.exec():
            return
    
    remark = team_setting.remark_name or f"队伍 {self.team_num}"
    confirm_msg = self.tr(f"导入队伍 {self.team_num} ({remark}) 的设置?\n这将覆盖当前设置。")
    box = MessageBoxConfirm(self.tr("确认导入"), confirm_msg, self)
    if box.exec():
        apply_team_settings(self.team_num, team_setting, theme_pack)
        self.team_setting = team_setting
        self.read_settings()
        BaseInfoBar.success(
            title=self.tr("导入成功"),
            content=self.tr("设置已导入"),
            parent=self,
            position=InfoBarPosition.TOP
        )
```

- [ ] **Step 5: Test manually**

Run: `uv run main.py`
Test import with valid file, test with missing fields, verify confirmation dialogs

- [ ] **Step 6: Commit**

```bash
git add app/team_setting_card.py
git commit -m "feat: add import button to TeamSettingCard"
```

---

### Task 9: Add export/import buttons to ThemePackSettingDialog

**Files:**
- Modify: `app/theme_pack_setting_interface.py`

- [ ] **Step 1: Add imports**

Add to imports in `app/theme_pack_setting_interface.py`:

```python
from PySide6.QtWidgets import QFileDialog
from module.config.theme_pack_import_export import (
    export_theme_pack_weight,
    import_theme_pack_weight,
    generate_theme_pack_export_filename
)
from app.card.messagebox_custom import BaseInfoBar
from qfluentwidgets import InfoBarPosition
```

- [ ] **Step 2: Add buttons in __init__**

Find button initialization and add:

```python
self.export_theme_button = PrimaryPushButton(self.tr("导出主题包权重"))
self.export_theme_button.clicked.connect(self.on_export_theme_pack)

self.import_theme_button = PushButton(self.tr("导入主题包权重"))
self.import_theme_button.clicked.connect(self.on_import_theme_pack)
```

- [ ] **Step 3: Add to layout**

Find button layout and add:

```python
button_layout.addWidget(self.export_theme_button)
button_layout.addWidget(self.import_theme_button)
```

- [ ] **Step 4: Implement handlers**

Add methods:

```python
def on_export_theme_pack(self):
    """Handle export theme pack button click."""
    default_filename = generate_theme_pack_export_filename(self.team_num)
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        self.tr("导出主题包权重"),
        default_filename,
        "YAML Files (*.yaml *.yml)"
    )
    
    if file_path:
        success = export_theme_pack_weight(self.team_num, file_path)
        if success:
            BaseInfoBar.success(
                title=self.tr("导出成功"),
                content=self.tr(f"主题包权重已导出到 {file_path}"),
                parent=self,
                position=InfoBarPosition.TOP
            )
        else:
            BaseInfoBar.error(
                title=self.tr("导出失败"),
                content=self.tr("导出主题包权重时发生错误"),
                parent=self,
                position=InfoBarPosition.TOP
            )

def on_import_theme_pack(self):
    """Handle import theme pack button click."""
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        self.tr("导入主题包权重"),
        "",
        "YAML Files (*.yaml *.yml)"
    )
    
    if not file_path:
        return
    
    box = MessageBoxConfirm(
        self.tr("确认导入"),
        self.tr("导入主题包权重将覆盖当前设置。是否继续?"),
        self
    )
    if box.exec():
        success = import_theme_pack_weight(file_path, self.team_num)
        if success:
            self.load_config()
            BaseInfoBar.success(
                title=self.tr("导入成功"),
                content=self.tr("主题包权重已导入"),
                parent=self,
                position=InfoBarPosition.TOP
            )
        else:
            BaseInfoBar.error(
                title=self.tr("导入失败"),
                content=self.tr("导入主题包权重时发生错误"),
                parent=self,
                position=InfoBarPosition.TOP
            )
```

- [ ] **Step 5: Test manually**

Run: `uv run main.py`
Open theme pack dialog, test export/import

- [ ] **Step 6: Commit**

```bash
git add app/theme_pack_setting_interface.py
git commit -m "feat: add import/export buttons to ThemePackSettingDialog"
```

---

## Plan Complete

All core functionality implemented. Manual testing required for UI integration.
