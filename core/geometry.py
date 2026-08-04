import math

from explosion_protection.nfpa_68_ch6_equations import (
    effective_area, hydraulic_diameter_circular,
    hydraulic_diameter_square, hydraulic_diameter_rectangular,
)

# Volume calculation of common 3D geometries
def vol_cuboid(a, b, h):
    """
    Volume of a rectangular cuboid.

    Args:
        a (float): Base length [m]
        b (float): Base width [m]
        h (float): Height [m]

    Returns:
        float: Volume [m³]
    """
    return a*b*h

def vol_truncated_rect_pyramid(A, B, a, b, h):
    """
    Volume of a truncated rectangular pyramid (frustum).

    Args:
        A (float): Large base length [m]
        B (float): Large base width [m]
        a (float): Small base length [m]
        b (float): Small base width [m]
        h (float): Height [m]

    Returns:
        float: Volume [m³]
    """
    A1 = A*B
    A2 = a*b
    avg_length = (A+a)/2
    avg_width =  (B+b)/2
    A_mid = avg_length * avg_width
    return h/6 * (A1 + A2 + 4*A_mid)

def vol_cylinder(r, h):
    """
    Volume of a cylinder.

    Args:
        r (float): Cylinder radius [m]
        h (float): Height [m]

    Returns:
        float: Volume [m³]
    """
    return math.pi * r**2 * h

def vol_truncated_cone(R, r, h):
    """
    Volume of a truncated cone.

    Args:
        R (float): Large radius [m]
        r (float): Small radius [m]
        h (float): Height [m]

    Returns:
        float: Volume [m³]
    """
    return (1/3) * math.pi * h * (r**2 + r * R + R**2)


# Enclosure geometry aggregation — segments are dicts of the form
# {"type": "cuboid"|"cylinder"|"truncated_cone"|"truncated_rect_pyramid", <shape dims, SI>}
SEGMENT_VOLUME_FNS = {
    "cuboid":                 lambda s: vol_cuboid(s["a"], s["b"], s["h"]),
    "cylinder":               lambda s: vol_cylinder(s["r"], s["h"]),
    "truncated_cone":         lambda s: vol_truncated_cone(s["R"], s["r"], s["h"]),
    "truncated_rect_pyramid": lambda s: vol_truncated_rect_pyramid(s["A"], s["B"], s["a"], s["b"], s["h"]),
}


def segment_volume(segment):
    """
    Volume of a single enclosure segment.

    Args:
        segment (dict): {"type": <shape key>, ...dims [m]} — see SEGMENT_VOLUME_FNS.

    Returns:
        float: Volume [m³]
    """
    return SEGMENT_VOLUME_FNS[segment["type"]](segment)


def enclosure_volume_and_length(segments):
    """
    Total volume and stacked height of an enclosure built from segments.

    Args:
        segments (list[dict]): Ordered list of segment dicts, each stacked
            along the same axis. See segment_volume() for the dict schema.

    Returns:
        tuple[float, float]: (V, L) — total volume [m³], total height [m]
    """
    V = sum(segment_volume(s) for s in segments)
    L = sum(s["h"] for s in segments)
    return V, L


def _segment_cross_section(s):
    """
    Own maximum cross-sectional area and (shape family, aspect ratio) for a
    single segment. Used by enclosure_hydraulic_diameter() to find "the
    largest cross section" per NFPA 68 §6.4.3.6.2/.3.

    Returns:
        tuple: (area [m²], (family, R)) — family is "circular" or
               "rectangular"; R is None for circular segments.
    """
    if s["type"] in ("cylinder", "truncated_cone"):
        r = max(s.get("r", 0.0), s.get("R", 0.0))
        return math.pi * r ** 2, ("circular", None)
    A = s.get("A", s.get("a"))
    B = s.get("B", s.get("b"))
    return A * B, ("rectangular", max(A, B) / min(A, B))


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
        segments (list[dict]): Segment stack — see segment_volume() for
            the dict schema.
        V (float): Effective volume Veff [m³]
        L (float): Maximum flame travel length H [m]

    Returns:
        float: Effective hydraulic diameter Dhe [m]
    """
    Aeff = effective_area(V, L)
    _, (family, R) = max((_segment_cross_section(s) for s in segments),
                          key=lambda x: x[0])
    if family == "circular":
        return hydraulic_diameter_circular(Aeff)
    if R < 1.2:
        return hydraulic_diameter_square(Aeff)
    return hydraulic_diameter_rectangular(Aeff, R)
