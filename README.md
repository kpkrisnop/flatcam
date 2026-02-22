# FlatCAM Evo — Patched Fork

A community-maintained fork of **FlatCAM Evo 8.9.95** with bug fixes for tool database
handling, drilling workflow, object lifecycle, and worker-thread safety.

Upstream: [FlatCAM Beta by Marius Stanciu](https://bitbucket.org/marius_stanciu/flatcam_beta)
Original FlatCAM: [FlatCAM by Juan Pablo Caram](https://bitbucket.org/jpcgt/flatcam)

---

## What Is FlatCAM Evo

FlatCAM Evo is a 2D Computer-Aided Manufacturing (CAM) application for preparing CNC jobs
to make printed circuit boards (PCBs). It imports industry-standard PCB design files and
generates G-Code for:

- **Isolation routing** — cutting around copper traces
- **Drilling** — through-hole component holes and vias
- **Milling** — board outline cutout and copper removal
- **Solder paste dispensing** — stencil generation
- **Panelization** — multi-board layouts

### Supported File Formats

| Input                  | Output |
| ---------------------- | ------ |
| Gerber (RS-274X)       | G-Code |
| Excellon (drill files) | DXF    |
| DXF                    | SVG    |
| SVG, PDF, HPGL/2       |        |

### G-Code Post-Processors

Ships with ~20 post-processors including GRBL 1.1, Marlin, LinuxCNC, Roland,
Paste (solder paste), and several GRBL variants.

---

## Improvements Over Upstream

This fork fixes a series of bugs in FlatCAM Evo 8.9.95 that cause crashes and
incorrect behavior during normal use.

### Object Lifecycle Fixes

- **Object deletion crash** — deleting Gerber or Excellon objects caused an unhandled
  exception in the object collection cleanup and associated signal teardown
- **Worker thread UI safety** — worker threads accessing destroyed Qt widgets after the
  user switches or closes objects now fail gracefully instead of raising
  `RuntimeError: wrapped C/C++ object has been deleted`

### Tool Database & Parameter Chain Fixes

- **Tool database overwriting** (`ToolDrilling`) — `build_tool_ui()` was unconditionally
  overwriting the plugin's working tool copy from the source object on every call,
  discarding any per-tool database values already loaded. Fixed to preserve loaded values
  in the non-default sort path.
- **Tool data flow** — several tool plugins (`ToolMilling`, `ToolIsolation`, `ToolNCC`,
  `ToolPaint`, `ToolCutOut`) were reading parameters from `obj_options` (application-level
  globals) instead of `tools[uid]['data']` (per-tool database values). Parameters now
  correctly come from the tool database entry.
- **Database template cleanup** — removed redundant duplicate parameter definitions from
  `appDatabase.py` and unified the per-tool parameter defaults in `defaults.py`.

### Drilling Workflow Fixes

- **Excellon drill duplication** — drills from an Excellon object were being appended to
  the job list on each UI refresh, causing duplicated drill paths in generated G-Code.
- **Drilling tool database not applied** — the drilling plugin was not correctly applying
  tool database entries, causing all drills to use default parameters regardless of the
  database configuration.

### Other Fixes

- **Dwell parameter not applied** — the dwell parameter set per-tool in the database was
  not being passed through to G-Code generation in `ToolMilling` and `ToolCutOut`.
- **Move object log error** — `ToolMove` raised an unhandled `AttributeError` when
  logging certain object move operations.

---

## Requirements

| Requirement | Version        |
| ----------- | -------------- |
| Python      | 3.11 or later  |
| PyQt6       | 6.x            |
| numpy       | ≥ 1.16, < 2.0  |
| scipy       | latest         |
| Shapely     | latest         |
| VisPy       | latest         |
| Pillow      | latest         |
| GDAL        | system library |
| GEOS        | system library |

Full Python dependency list is in `requirements.txt`.

---

## Installation

### macOS — Homebrew (Recommended)

Install via the Homebrew tap:

```bash
brew tap KP-Krisnop/flatcam-evo
brew install flatcam-evo
```

Run:

```bash
flatcam
```

---

### macOS — From Source

Requires [Homebrew](https://brew.sh) and [Mamba/Conda](https://conda-forge.org/download/).

**1. Install system dependencies:**

```bash
brew install python@3.11 pyqt gdal geos freetype spatialindex qpdf pkg-config
```

**2. Clone the repository:**

```bash
git clone https://github.com/KP-Krisnop/flatcam-evo.git
cd flatcam-evo
```

**3. Create and activate a conda environment:**

```bash
mamba env create -f environment.yml
mamba activate flatcam
```

Or with pip only:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --no-binary pillow -r requirements.txt
```

**4. Run:**

```bash
python flatcam.py
```

---

### Linux (Ubuntu / Debian)

**1. Install system dependencies:**

```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-pip python3.11-venv python3-tk \
    libgdal-dev libgeos-dev libfreetype-dev libspatialindex-dev \
    libqpdf-dev pkg-config
```

**2. Clone the repository:**

```bash
git clone https://github.com/KP-Krisnop/flatcam-evo.git
cd flatcam-evo
```

**3. Create a virtual environment and install dependencies:**

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. Run:**

```bash
python flatcam.py
```

> **Tip:** On systems where `python3.11` is not the default, use the full path, e.g.
> `/usr/bin/python3.11`.

**Conda/Mamba alternative (any Linux distro):**

```bash
mamba env create -f environment.yml
mamba activate flatcam
python flatcam.py
```

---

### Windows

**1. Install Python 3.11:**

Download from [python.org](https://www.python.org/downloads/windows/) and check
"Add Python to PATH" during installation.

**2. Install system dependencies:**

GDAL and GEOS are required. The easiest method is to use the
[OSGeo4W installer](https://trac.osgeo.org/osgeo4w/) or install pre-built wheels:

```cmd
pip install gdal geos
```

If GDAL installation fails, use the pre-built wheel from
[Christoph Gohlke's archive](https://github.com/cgohlke/geospatial-wheels/releases)
matching your Python version.

**3. Clone the repository:**

```cmd
git clone https://github.com/KP-Krisnop/flatcam-evo.git
cd flatcam-evo
```

**4. Create a virtual environment and install dependencies:**

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**5. Run:**

```cmd
python flatcam.py
```

**Portable mode:**

To run FlatCAM from a USB drive without writing to `%APPDATA%`, edit
`config\configuration.txt` and set:

```
portable=True
```

User data will then be stored in the `config\` folder next to the application.

---

### Conda / Mamba (All Platforms)

If you have [Mamba](https://conda-forge.org/download/) or Conda installed:

```bash
git clone https://github.com/KP-Krisnop/flatcam-evo.git
cd flatcam-evo
mamba env create -f environment.yml
mamba activate flatcam
python flatcam.py
```

This is the simplest method on all platforms as Conda handles the GDAL/GEOS system
library dependencies automatically.

---

## Running the Application

```bash
python flatcam.py                          # Normal GUI launch
python flatcam.py --headless=1             # Headless mode (no GUI)
python flatcam.py --shellfile=<script>     # Execute a TCL script on startup
python flatcam.py --shellvar=<values>      # Pass variables to TCL script
```

User data and preferences are stored in:

| Platform           | Location               |
| ------------------ | ---------------------- |
| macOS / Linux      | `~/.FlatCAM/`          |
| Windows            | `%APPDATA%\FlatCAM\`   |
| Windows (portable) | `<app folder>\config\` |

Log file: `~/.FlatCAM/log.txt` (or equivalent on Windows).
Tools database: `~/.FlatCAM/tools_db_<version>.FlatDB` (JSON format, editable).

---

## Project Structure

```
flatcam.py          Entry point
appMain.py          Central App class (~8k lines)
camlib.py           Core geometry and G-code generation
defaults.py         All preference keys and factory defaults
appDatabase.py      Tool database management
appObjects/         Data model: Gerber, Excellon, Geometry, CNCJob objects
appPlugins/         ~39 manufacturing tool plugins
appGUI/             Main window, widgets, canvas, preferences panels
appParsers/         File format parsers (Gerber, Excellon, DXF, SVG, PDF)
appEditors/         Interactive geometry editors
preprocessors/      G-code post-processors (~20 machine profiles)
tclCommands/        TCL scripting interface (~79 commands)
locale/             Translations (10 languages)
```

---

## Known Limitations

- **Tab detachment on Linux/macOS** — Detaching tool panels into floating windows can
  cause a segmentation fault in some environments. The upstream workaround is in place
  but the underlying Qt issue is not fully resolved.
- **File type association** — Windows registers `.gbr`, `.exc`, `.dxf` file associations
  automatically. macOS and Linux require manual file association setup through the OS.
- **OR-Tools optimization** — The advanced drill path optimization (shortest path) requires
  a 64-bit Python environment. 32-bit installations fall back to a simpler algorithm
  automatically.
- **numpy < 2.0** — numpy 2.x introduced breaking API changes. This fork pins numpy below
  2.0 until upstream compatibility is addressed.

---

## Credits

- **Marius Stanciu** — FlatCAM Evo / FlatCAM Beta author
- **Juan Pablo Caram** — original FlatCAM author
- **tomoyanonymous** — [homebrew-flatcam](https://github.com/tomoyanonymous/homebrew-flatcam)
  tap that the macOS formula is based on
- **Krisnop Saimuey** — bug fixes in this fork
- **Claude Code** — execute the bug fixes

---

## License

FlatCAM Evo is released under the MIT License. See `LICENSE` for details.
