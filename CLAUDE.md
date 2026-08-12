# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
streamlit run app/app.py
```

The app runs on `http://localhost:8501`. The `PROJECTS_ROOT` environment variable overrides the default projects directory (`projects/` at the repo root).

PDF report generation requires WeasyPrint:

```bash
pip install weasyprint
```

## Architecture

FlowGuard is a Streamlit engineering-calculation app focused on explosion protection per NFPA 68 (2023). It has three distinct layers:

### 1. Calculation engine (`explosion_protection/`)

Pure-Python library with no Streamlit dependency. Key files:

- `nfpa_68_ch6_equations.py` — general venting fundamentals shared across Chapters 7/8 (§6.1–§6.8): deflagration index, enclosure design pressure/reaction forces, and the §6.4.3 hydraulic diameter/L-D equations (`hydraulic_diameter_circular/square/rectangular`, `effective_area`, `ld_ratio`).
- `nfpa_68_ch8_equations.py` — raw equation implementations (§8.2–§8.5 formulas, each function maps directly to one NFPA equation)
- `nfpa_68_ch8_dust_vent.py` — orchestrator that sequences the equations into the full calculation chain (Av0 → Av1 → Av2 → Av3 → Av4 → Avf). This file owns the input dataclasses (`Enclosure`, `Dust`, `Vent`, `Duct`, `TurbulenceInputs`, `PartialVolumeInputs`), enums (`TurbulenceMode`, `SubatmosphericMethod`), result dataclass (`DustVentResult`), and the two public entry points: `vent_area_dust()` and `dust_collector_vent_area()`.

The Chapter 7 gas-vent equivalents (`nfpa_68_ch7_*.py`) exist but are not yet wired into the UI.

### 2. Streamlit UI (`app/`)

- `app.py` — home page; handles project selection/creation and shows a run list
- `pages/1_Dust_Vent_NFPA68.py` — the main calculation page; builds input widgets, calls the engine, renders the step-by-step result table, and drives save/PDF
- `utils/project_store.py` — filesystem CRUD for projects and runs
- `utils/serializer.py` — converts engine dataclasses ↔ JSON-safe dicts for persistence and form pre-fill
- `components/report.py` — generates a PDF report from a saved run dict using WeasyPrint (renders HTML → PDF)

### 3. Project data (`projects/`)

```
projects/
└── {project_name}/
    ├── project.yaml          # name, client, description, created
    └── runs/
        ├── {run_id}.json     # inputs + outputs serialized by serializer.py
        └── {run_id}.pdf      # generated report (optional)
```

Run IDs are 8-character UUID hex strings. Runs are loaded back into the UI via `load_run()`, which pre-fills the form through the `_pre()` helper in the page module.

### 4. Core utilities (`core/`)

Standalone geometry helpers (`geometry.py`) used by calculation modules. Not Streamlit-specific. Includes shape volume formulas (`vol_cuboid`, `vol_cylinder`, `vol_truncated_cone`, `vol_truncated_rect_pyramid`), segment-stack aggregation (`segment_volume`, `enclosure_volume_and_length`), and §6.4.3 hydraulic diameter orchestration (`enclosure_hydraulic_diameter`, `largest_cross_section`) that picks the circular/square/rectangular formula in `nfpa_68_ch6_equations.py` matching the shape of the enclosure's largest cross section. A segment may set `cols`/`rows` (default 1×1, via `segment_count()`) to represent identical side-by-side copies — e.g. multiple hoppers under one shared body — scaling volume and combined cross-section area but never height. `enclosure_catalog.py` holds named geometry templates (circular/rectangular presets, Donaldson family/model catalog).

Vent location is intentionally not a parameter anywhere in this chain: per §6.4.3.2/.3, the caller is expected to already pass Veff/H as the volume/length of just the part of the enclosure the flame must traverse to reach the vent (or, per §6.4.3.4, conservatively the whole enclosure) — not something these functions can determine themselves. Multiple vents at different elevations along the same axis (§6.4.3.2.2, which calls for a per-section L/D) is a known, unsupported case.

## Key conventions

- All physical quantities use SI units (m, m³, bar-g, kg/m², m/s) throughout the engine and storage layers.
- The calculation chain always proceeds Av0 → Av1 → Av2 → Av3 → Av4 → Avf; each step is a separate `_step_*` function in the orchestrator, making it straightforward to add new correction steps.
- New calculation pages go in `app/pages/` and must manually add the `_workspace` path insertion (see the existing pattern in `1_Dust_Vent_NFPA68.py`) to import from the engine.
- `sys.path.insert(0, str(_workspace))` at the top of each page handles the package resolution for both the Streamlit multi-page layout and flat dev/test runs.
