# Outline

workspcace/
├── README.md                           # Project overview (this file)
├── collection_systems/
│   ├── dust_collectors.py              # Sizing calculations
│   ├── cyclones.py                     # Cyclone sizing
│   ├── mist_collectors.py              # Open area, air exchange, ambient methods
│   └── fume_hoods.py                   # Capture/face velocity, air exchange, slot sizing
├── core/
│   ├── fluid_properties.py             # Dynamic viscosity, density, etc.
│   ├── geometry.py                     # Shape volumes, segment-stack volume/length, elbow centerline
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
│   ├── explosion_dynamics.py
│   ├── nfpa_68_2023_calc.py            # NFPA 68 (bucket elevator, dust collector)
│   ├── en_14491_2012_calc.py           # EN standard venting
│   └── structural_resistance.py        # Dust collector pressure resistance
├── fluid_systems/
│   ├── ductwork.py                     # Basic ductulator, flexible ducting loss
│   ├── pressure_drop.py                # ACGIH method, Lamson method, pneumatic conveying
│   ├── components.py                   # Butterfly valves
│   └── fans_pumps.py                   # Pressure blowers, vacuum pumps, fan curves
├── material_handling/
│   └── rotary_valves.py                # Rotary valve sizing
