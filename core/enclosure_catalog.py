"""
Enclosure geometry catalog.

Provides ready-made segment stacks (see core.geometry for the segment dict
schema) for common enclosure shapes and for named Donaldson dust-collector
models. All dimensions returned are SI (metres).

Donaldson DLMC data comes from "DLMC Dirty Side Dimensions.xlsx"
(flowguard-app/docs_for_claude_code/Donaldson db). It is transcribed here in
inches, as in the sheet, and converted to metres with core.units at import.
Each model is a rectangular body (cuboid) plus one hopper chosen from the
options available for its width; a hopper may be several identical copies
side by side along the body length (segment "cols").
"""

import copy
from dataclasses import dataclass, field

from core.units import in_to_m


def circular_enclosure_default():
    """Default segment stack for a cylindrical enclosure with a conical hopper."""
    return [
        {"type": "cylinder",       "r": 0.5, "h": 1.0},
        {"type": "truncated_cone", "R": 0.5, "r": 0.1, "h": 0.5},
    ]


def rectangular_enclosure_default():
    """Default segment stack for a rectangular enclosure with a pyramidal hopper."""
    return [
        {"type": "cuboid",                 "a": 1.0, "b": 1.0, "h": 1.0},
        {"type": "truncated_rect_pyramid", "A": 1.0, "B": 1.0, "a": 0.2, "b": 0.2, "h": 0.5},
    ]


@dataclass
class DonaldsonModel:
    """A Donaldson dust-collector model: one body and its hopper options."""
    name: str
    body: dict                                      # cuboid segment [m]
    hoppers: dict = field(default_factory=dict)     # hopper name -> segment [m]


@dataclass
class DonaldsonFamily:
    """A Donaldson product family, grouping several models."""
    name: str
    models: dict  # model name -> DonaldsonModel


# ── DLMC source data (inches, as in the spreadsheet) ──────────────────────────
# Model "W/H/15": W modules wide (along body length a), H modules high.
_DLMC_MODULE_A_IN = 39.47609    # body length per module of width
_DLMC_B_IN        = 68.8421     # body depth, same for every model
_DLMC_BODY_H_IN   = {2: 61.11, 3: 83.904, 4: 123.57, 5: 148.404, 6: 171.234, 8: 216.892}

# (W, H) in sheet order. 1/7/15 and 3/7/15 are left out until the 7-high
# body height is known (blank in the sheet).
_DLMC_MODELS = [
    (1, 2), (1, 3), (1, 4), (2, 2), (1, 5), (2, 3), (2, 4), (3, 3),
    (2, 5), (2, 6), (3, 5), (2, 8), (3, 6), (4, 5), (3, 8), (4, 8),
]

# Hopper options by body width W: (name, A, B, a, b, h, copies).
# A×B is the top (large) face of one copy, a×b its outlet; copies sit side by
# side along the body length, so copies × A equals the body length.
_DLMC_HOPPERS_IN = {
    1: [
        ("single outlet",  39.47609,  68.8421, 9.88,   9.88, 60,    1),
    ],
    2: [
        ("dual outlet",    39.47609,  68.8421, 9.88,   9.88, 60,    2),
        ("single outlet",  78.95218,  68.8421, 9.88,   9.88, 72,    1),
        ("through hopper", 78.95218,  68.8421, 30.81,  9.75, 54,    1),
    ],
    3: [
        ("triple outlet",  39.47609,  68.8421, 9.88,   9.88, 60,    3),
        ("single outlet",  118.42827, 68.8421, 9.88,   9.88, 93.25, 1),
        ("through hopper", 118.42827, 68.8421, 70.39,  9.71, 54,    1),
    ],
    4: [
        ("four outlets",   39.47609,  68.8421, 9.88,   9.88, 60,    4),
        ("dual outlet",    78.95218,  68.8421, 9.88,   9.88, 72,    2),
        ("through hopper", 157.90436, 68.8421, 109.87, 9.70, 54,    1),
    ],
}


def _dlmc_body(w, h):
    return {
        "type": "cuboid",
        "a": in_to_m(w * _DLMC_MODULE_A_IN),
        "b": in_to_m(_DLMC_B_IN),
        "h": in_to_m(_DLMC_BODY_H_IN[h]),
    }


def _dlmc_hopper(A, B, a, b, h, copies):
    seg = {
        "type": "truncated_rect_pyramid",
        "A": in_to_m(A), "B": in_to_m(B), "a": in_to_m(a), "b": in_to_m(b), "h": in_to_m(h),
    }
    if copies > 1:
        seg["cols"], seg["rows"] = copies, 1
    return seg


def _build_dlmc():
    models = {}
    for w, h in _DLMC_MODELS:
        name = f"DLMC {w}/{h}/15"
        hoppers = {
            hname: _dlmc_hopper(A, B, a, b, hh, n)
            for hname, A, B, a, b, hh, n in _DLMC_HOPPERS_IN[w]
        }
        models[name] = DonaldsonModel(name, body=_dlmc_body(w, h), hoppers=hoppers)
    return DonaldsonFamily("DLMC", models)


DONALDSON_CATALOG = {"DLMC": _build_dlmc()}


def list_families():
    """Names of all Donaldson families in the catalog."""
    return list(DONALDSON_CATALOG.keys())


def list_models(family):
    """Names of all models within a Donaldson family."""
    return list(DONALDSON_CATALOG[family].models.keys())


def get_model(family, model):
    """Look up a DonaldsonModel by family and model name."""
    return DONALDSON_CATALOG[family].models[model]


def list_hoppers(family, model):
    """Hopper options available for a model (depends on its width)."""
    return list(get_model(family, model).hoppers.keys())


def get_segments(family, model, hopper):
    """Segment stack [body, hopper] for a model and hopper choice (copies, safe to edit)."""
    m = get_model(family, model)
    return [copy.deepcopy(m.body), copy.deepcopy(m.hoppers[hopper])]
