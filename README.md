# Outline

workspcace/
├── README.md                           # Project overview (this file)
├── collection_systems/
│   ├── dust_collectors.py              # Sizing calculations
│   ├── cyclone_muschelknautz_equations.py     # Hoffmann & Stein Ch. 6 (Muschelknautz) equations
│   ├── cyclone_muschelknautz_orchestrator.py  # cyclone_performance(): cut size, efficiency, Δp, emission; PSD class
│   ├── mist_collectors.py              # Open area, air exchange, ambient methods
│   └── fume_hoods.py                   # Capture/face velocity, air exchange, slot sizing
├── core/
│   ├── fluid_properties.py             # Dynamic viscosity, density, etc.
│   ├── geometry.py                     # Shape volumes, segment-stack volume/length, elbow centerline
│   ├── units.py                        # Named pint-based conversions: flow, velocity, length, pressure
|   ├── external_data/
│   │   └── litterature/                # UNUSED: Placeholder for future litterature data
│   │       ├── FUTURE 
|   │   ├── standards/
|   │   │   ├── nfpa_68_2023_data.py    # NFPA_68 tables and methods
|   │   │   ├── acgih_30th_data.py      # ACGIH methods and tables
|   │   │   ├── smacna_round_data.py    # SMACNA chart lookup tables
|   │   │   ├── smacna_square_data.py    # SMACNA chart lookup tables
|   │   │   ├── en_14491_2012_data.py   # EN explosion standards
│   │   └── manufacturer/
│   │       ├── hansentek_data.py       # Hansentek installation distances
│   │       └── lamson_data.py          # Lamson chart data for pressure drop
│   │       └── vdl_data.py             # VDL rotary valves design data
└── duct_design/
    └── square_duct.py                  # SMACNA square duct design
├── explosion_protection/
│   ├── nfpa_68_ch6_equations.py        # NFPA 68 (2023) §6 general venting fundamentals, §6.4.3 L/D equations
│   ├── nfpa_68_ch6_orchestrator.py     # §6.4.3 hydraulic diameter from a segment stack
│   ├── nfpa_68_ch7_equations.py        # Ch. 7 gas/mist venting equations
│   ├── nfpa_68_ch7_orchestrator.py     # Ch. 7 vent area chain (vent_area_gas)
│   ├── nfpa_68_ch8_equations.py        # Ch. 8 dust venting equations
│   ├── nfpa_68_ch8_orchestrator.py     # Ch. 8 vent area chain (vent_area_dust, dust_collector_vent_area)
│   ├── explosion_dynamics.py           # PLANNED
│   ├── en_14491_2012_calc.py           # PLANNED: EN standard venting
│   └── structural_resistance.py        # PLANNED: Dust collector pressure resistance
├── fluid_systems/
│   ├── duct_flow.py                    # Round-duct flow/diameter/velocity (continuity), solve_round_duct()
│   ├── ductwork.py                     # PLANNED: flexible ducting loss
│   ├── pressure_drop.py                # PLANNED: ACGIH method, Lamson method, pneumatic conveying
│   ├── components.py                   # Butterfly valves
│   └── fans_pumps.py                   # Pressure blowers, vacuum pumps, fan curves
├── material_handling/
│   └── rotary_valves.py                # Rotary valve sizing

# Naming convention

Each calculation family is split into two files sharing one prefix:

- `<prefix>_equations.py` - one function per source equation; the docstring cites the equation number and page.
- `<prefix>_orchestrator.py` - organises the equations into the calculation method (input dataclasses, step sequence, result object).

The pair sorts side by side, e.g. `nfpa_68_ch8_equations.py` / `nfpa_68_ch8_orchestrator.py`. Shared helpers and catalogs under `core/` are not equation families and do not follow the pair convention.
