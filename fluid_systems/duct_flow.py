"""Round-duct continuity: flow, diameter and velocity from any two.

SI only (Q in m³/s, D in m, V in m/s, A in m²). These are standard textbook
relations with no single book/standard reference, so equations and the solver
live together in this one file rather than an equations/orchestrator pair.
"""
import math
from dataclasses import dataclass


def round_duct_area(diameter):
    """Cross-section area of a round duct [m²]; continuity, Q = V·A, A = π·D²/4."""
    return math.pi * diameter**2 / 4


def round_duct_velocity(flow, diameter):
    """Mean velocity [m/s]; continuity, Q = V·A, A = π·D²/4, so V = Q/A."""
    return flow / round_duct_area(diameter)


def round_duct_diameter(flow, velocity):
    """Diameter [m]; continuity, Q = V·A, A = π·D²/4, so D = √(4·Q/(π·V))."""
    return math.sqrt(4 * flow / (math.pi * velocity))


def round_duct_flow(diameter, velocity):
    """Volumetric flow [m³/s]; continuity, Q = V·A, A = π·D²/4."""
    return velocity * round_duct_area(diameter)


@dataclass(frozen=True)
class RoundDuctResult:
    flow: float       # m³/s
    diameter: float   # m
    velocity: float   # m/s
    area: float       # m²


def solve_round_duct(flow=None, diameter=None, velocity=None) -> RoundDuctResult:
    """Solve a round duct from exactly two of flow [m³/s], diameter [m], velocity [m/s].

    Raises ValueError unless exactly two are given and each is finite and > 0.
    """
    given = {"flow": flow, "diameter": diameter, "velocity": velocity}
    supplied = {k: v for k, v in given.items() if v is not None}
    if len(supplied) != 2:
        raise ValueError(
            f"Exactly two of flow, diameter, velocity are required; got {len(supplied)}."
        )
    for name, value in supplied.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite number > 0; got {value!r}.")

    if flow is None:
        flow = round_duct_flow(diameter, velocity)
    elif diameter is None:
        diameter = round_duct_diameter(flow, velocity)
    else:
        velocity = round_duct_velocity(flow, diameter)
    return RoundDuctResult(flow, diameter, velocity, round_duct_area(diameter))
