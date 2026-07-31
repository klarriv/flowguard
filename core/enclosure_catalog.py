"""
Enclosure geometry catalog.

Provides ready-made segment stacks (see core.geometry for the segment dict
schema) for common enclosure shapes and for named Donaldson dust-collector
models. All dimensions are SI (metres).

The DONALDSON_CATALOG values below are placeholders — real dimensional data
for each family/model has not been supplied yet. The structure and accessor
functions are stable; only the numbers need to be replaced.
"""

from dataclasses import dataclass, field


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
    """A single Donaldson dust-collector model and its enclosure geometry."""
    name: str
    segments: list = field(default_factory=list)


@dataclass
class DonaldsonFamily:
    """A Donaldson product family, grouping several models."""
    name: str
    models: dict  # model name -> DonaldsonModel


# Placeholder catalog — dimensions are illustrative, not manufacturer data.
DONALDSON_CATALOG = {
    "Torit DFO": DonaldsonFamily("Torit DFO", {
        "DFO 2-4": DonaldsonModel("DFO 2-4", segments=[
            {"type": "cylinder",       "r": 0.6, "h": 1.2},
            {"type": "truncated_cone", "R": 0.6, "r": 0.15, "h": 0.6},
        ]),
        "DFO 4-12": DonaldsonModel("DFO 4-12", segments=[
            {"type": "cylinder",       "r": 0.9, "h": 1.8},
            {"type": "truncated_cone", "R": 0.9, "r": 0.2, "h": 0.9},
        ]),
    }),
    "Torit PowerCore": DonaldsonFamily("Torit PowerCore", {
        "CPC 2": DonaldsonModel("CPC 2", segments=[
            {"type": "cuboid",                 "a": 0.8, "b": 0.8, "h": 1.0},
            {"type": "truncated_rect_pyramid", "A": 0.8, "B": 0.8, "a": 0.15, "b": 0.15, "h": 0.4},
        ]),
        "CPC 4": DonaldsonModel("CPC 4", segments=[
            {"type": "cuboid",                 "a": 1.2, "b": 1.2, "h": 1.4},
            {"type": "truncated_rect_pyramid", "A": 1.2, "B": 1.2, "a": 0.2, "b": 0.2, "h": 0.6},
        ]),
    }),
}


def list_families():
    """Names of all Donaldson families in the catalog."""
    return list(DONALDSON_CATALOG.keys())


def list_models(family):
    """Names of all models within a Donaldson family."""
    return list(DONALDSON_CATALOG[family].models.keys())


def get_model(family, model):
    """Look up a DonaldsonModel by family and model name."""
    return DONALDSON_CATALOG[family].models[model]
