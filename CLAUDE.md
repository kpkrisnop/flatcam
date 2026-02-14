# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FlatCAM Evo is a Python CAM (Computer-Aided Manufacturing) application for preparing CNC jobs to make PCBs. It imports Gerber/Excellon/DXF/SVG files and generates G-Code for isolation routing, drilling, milling, and other PCB manufacturing tasks.

- **Language:** Python 3.6+ (current environment uses 3.11)
- **GUI:** PyQt6
- **Graphics:** VisPy (3D engine), Matplotlib (legacy)
- **Geometry:** Shapely, numpy, scipy
- **Entry point:** `flatcam.py`

## Running the Application

```bash
python flatcam.py                          # Normal launch
python flatcam.py --headless=1             # Headless mode (no GUI)
python flatcam.py --shellfile=<script>     # Execute TCL script on startup
python flatcam.py --shellvar=<values>      # Pass variables to script
```

User data directory: `~/.FlatCAM/` (Unix) or `%APPDATA%\FlatCAM` (Windows).
Log file: `~/.FlatCAM/log.txt`.
Tools database: `~/.FlatCAM/tools_db_<version>.FlatDB` (JSON format).

## Building Documentation

```bash
cd doc && make html    # Build Sphinx docs
```

## Architecture

### Core Modules (root level)

- **appMain.py** (~8k lines) — Main `App` class (QObject). Central orchestrator: manages object lifecycle, signal/slot wiring, CLI args, version management. This is the largest single module.
- **camlib.py** (~8.5k lines) — Core geometry and manufacturing library. Contains `ApertureMacro`, `Geometry`, `CNCjob`, and `AppRTree` classes. All geometric operations and G-code generation live here.
- **defaults.py** — `AppDefaults` class with `factory_defaults` dict. All preference keys and their defaults.
- **appDatabase.py** — Tool database management (diameters, feeds, speeds).
- **appTool.py** — Base class for all tool plugins.
- **appWorker.py / appPool.py** — Threading (QThread) and multiprocessing pool.
- **appTranslation.py** — i18n wrapper around gettext. Strings use `_()` builtin.

### Subsystem Directories

| Directory | Purpose |
|---|---|
| `appGUI/` | Main window (`MainGUI.py`), custom widgets (`GUIElements.py`), canvas (`PlotCanvas3d.py`), themes, preferences panels |
| `appObjects/` | Data model classes: `GerberObject`, `ExcellonObject`, `GeometryObject`, `CNCJobObject`, `DocumentObject`, `ScriptObject`. All inherit from `AppObjectTemplate`. `ObjectCollection` manages them. |
| `appEditors/` | Interactive editors for Gerber, Excellon, Geometry, G-Code, and text. Each editor has sub-plugins in `*_plugins/` dirs. |
| `appHandlers/` | `appIO.py` (file import/export), `appEdit.py` (edit operations on objects) |
| `appParsers/` | File format parsers: `ParseGerber`, `ParseExcellon`, `ParseDXF`, `ParseSVG`, `ParsePDF`, `ParseHPGL2`, `ParseFont` |
| `appPlugins/` | ~39 manufacturing tool plugins (isolation, NCC, paint, milling, drilling, cutout, panelize, levelling, film, solder paste, fiducials, rules check, etc.) |
| `tclCommands/` | ~79 TCL command modules for the scripting interface. Base class: `TclCommand.py`. |
| `preprocessors/` | ~20 G-code post-processors (GRBL variants, Marlin, LinuxCNC, Roland, etc.) |
| `locale/` | Translations for 10 languages |
| `appCommon/` | Shared utilities (`Common.py`), bilinear interpolation |

### Key Patterns

- **Object model:** All project items (Gerber, Excellon, Geometry, CNCJob) are subclasses of `AppObjectTemplate` in `appObjects/`. They're managed by `ObjectCollection` which backs the GUI project tree.
- **Plugin/tool architecture:** Tools in `appPlugins/` inherit from `AppTool`. Each tool typically has a UI panel, processing logic, and an associated TCL command.
- **Signal/slot communication:** PyQt signals drive the event system. `LoudDict` (in `appCommon/Common.py`) and `FCSignal` provide custom observable patterns.
- **Threading model:** Long operations run on `QThread` via `appWorker.py`. CPU-bound parallel work uses `multiprocessing.Pool` via `appPool.py`. Never access GUI from worker threads.
- **File import flow:** `appIO.py` detects format → appropriate parser loads geometry → object created and added to `ObjectCollection` → rendered on VisPy canvas.
- **Preferences:** Stored via `QSettings("Open Source", "FlatCAM_EVO")`. Defaults defined in `defaults.py`. Tools read from the shared options dict.
- **Localization:** All user-facing strings wrapped in `_()`. Translation catalogs in `locale/`. New strings need `gettext` extraction.

### No Automated Test Suite

The project does not have an integrated test framework (no pytest/unittest). Testing is manual. If adding tests, place them alongside the relevant module or in a new `tests/` directory.

## Critical Subsystems and Known Pitfalls

### Tool Data Flow (frequent source of bugs)

Tools are stored as dicts in each object's `.tools` attribute. The key is a tool number (int), the value contains `'tooldia'`, `'data'` (a dict of parameters), `'solid_geometry'`, and type-specific keys like `'drills'`/`'slots'` for Excellon.

Parameter keys are namespaced by tool type: `tools_drill_*`, `tools_mill_*`, `tools_iso_*`, `tools_paint_*`, `tools_ncc_*`, `tools_cutout_*`. The `tool_target` field in the DB is an **integer** (0=General, 1=Milling, 2=Drilling, 3=Isolation, 4=Paint, 5=NCC, 6=Cutout) — never compare it to a translated string.

**CNC generation parameter chain:** Tool plugins (e.g. `ToolMilling.py`) extract parameters from `tools_dict[uid]['data']`, then pass them to `camlib.py` methods (`generate_from_geometry_2`, `geometry_tool_gcode_gen`, `excellon_tool_gcode_gen`). When adding new per-tool parameters, you must thread them through: `defaults.py` → `appDatabase.py` (new-tool template) → plugin extraction → camlib method signature/usage. Parameters that read from `self.app.options` instead of the tool dict will not be per-tool customizable.

**Tool database matching:** `replace_tools()` in each plugin matches Excellon/Geometry tools against the Tools Database by diameter. It filters DB keys by namespace prefix (e.g. `tools_drill_*` for drilling) and skips other `tools_*` keys. When adding new parameters to the DB template in `appDatabase.py`, ensure the key follows the correct namespace.

### Worker Thread / UI Safety

Worker threads (`appWorker.py`) run operations like move-to-origin, CNC generation, etc. They must **never** access Qt widgets directly. Object `.ui` panels get destroyed when the user switches objects or closes tabs, so any widget access from a worker can hit `RuntimeError: wrapped C/C++ object has been deleted`.

**Pattern to follow:** Always wrap UI access in worker-callable methods with `try/except (RuntimeError, AttributeError)`. Key danger spots: `set_offset_values()`, `plot()`, `ui_disconnect()`, and any signal handler that touches `self.ui.*` widgets.

### Tool Dict Ownership

When copying tool dicts between the plugin and the object, always use `deepcopy()`. Assigning `self.excellon_tools = self.excellon_obj.tools` creates a reference — mutations to the plugin's copy will corrupt the object's original tools. This applies to all tool plugins, not just drilling.

### Floating-Point Tool Diameter Matching

Tool diameters are floats. When comparing diameters (e.g. matching against the Tools Database), always truncate both sides with `self.app.dec_format(float(dia), self.decimals)` before using `==`. Raw float comparison will fail due to precision differences between parser output and database storage.
