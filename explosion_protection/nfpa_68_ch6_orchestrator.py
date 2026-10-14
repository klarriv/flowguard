"""
NFPA 68 (2023) Chapter 6 — §6.4.3 effective hydraulic diameter orchestration.

Logic layer beside the raw equations in nfpa_68_ch6_equations.py: given a
stack of enclosure segments, picks the §6.4.3.6 hydraulic-diameter formula
(circular, square or rectangular) that matches the shape of the enclosure's
largest cross section and returns Dhe.

Segments are plain dicts, using the schema documented in
core.geometry.segment_volume() ({"type": ..., <dims, SI>, optional "cols"
and "rows" for side-by-side copies}). This module depends only on that
schema, not on core code.
"""

import math

from explosion_protection.nfpa_68_ch6_equations import (
    effective_area, hydraulic_diameter_circular,
    hydraulic_diameter_square, hydraulic_diameter_rectangular,
)


def _segment_cross_section(s):
    """
    Combined maximum cross-sectional area and (shape family, aspect ratio)
    for a segment, accounting for its side-by-side copies (cols x rows).
    Used by enclosure_hydraulic_diameter() to find "the largest cross
    section" per NFPA 68 §6.4.3.6.2/.3.

    Returns:
        tuple: (area [m²], (family, R)) — family is "circular" or
               "rectangular"; R is None for circular segments, otherwise
               the aspect ratio of the *combined* tiled footprint.
    """
    cols = s.get("cols", 1)
    rows = s.get("rows", 1)
    if s["type"] in ("cylinder", "truncated_cone"):
        r = max(s.get("r", 0.0), s.get("R", 0.0))
        return math.pi * r ** 2 * cols * rows, ("circular", None)
    A = s.get("A", s.get("a"))
    B = s.get("B", s.get("b"))
    width, depth = A * cols, B * rows
    return width * depth, ("rectangular", max(width, depth) / min(width, depth))


def largest_cross_section(segments):
    """
    Shape family and aspect ratio of an enclosure's largest cross section,
    per NFPA 68 §6.4.3.6.2/.3 ("the aspect ratio of the largest cross
    section"). Exposed separately from enclosure_hydraulic_diameter() so
    callers can display which shape/formula was selected.

    Args:
        segments (list[dict]): Segment stack — see core.geometry.segment_volume()
            for the dict schema.

    Returns:
        tuple: (family, R) — family is "circular" or "rectangular"; R is
               None for circular, otherwise that segment's own aspect ratio.
    """
    _, (family, R) = max((_segment_cross_section(s) for s in segments),
                          key=lambda x: x[0])
    return family, R


def enclosure_hydraulic_diameter(segments, V, L):
    """
    Effective hydraulic diameter Dhe for a segmented enclosure, using the
    NFPA 68 §6.4.3.6 formula that matches the shape of its largest cross
    section (circular, square, or rectangular).

    V and L must already represent Veff and H per §6.4.3.2/.3 — i.e. the
    segment stack should be modeled to end at the vent, not necessarily at
    the physical extent of the enclosure. Does not support multiple vents
    at different elevations along the same axis (§6.4.3.2.2), which would
    require a per-section L/D rather than one global value.

    Args:
        segments (list[dict]): Segment stack — see core.geometry.segment_volume()
            for the dict schema.
        V (float): Effective volume Veff [m³]
        L (float): Maximum flame travel length H [m]

    Returns:
        float: Effective hydraulic diameter Dhe [m]
    """
    Aeff = effective_area(V, L)
    family, R = largest_cross_section(segments)
    if family == "circular":
        return hydraulic_diameter_circular(Aeff)
    if R < 1.2:
        return hydraulic_diameter_square(Aeff)
    return hydraulic_diameter_rectangular(Aeff, R)
