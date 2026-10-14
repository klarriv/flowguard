import math

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


def segment_count(segment):
    """
    Number of identical side-by-side copies of a segment (cols x rows).
    Not an NFPA equation — a modeling convenience for enclosures with
    parallel discharge paths (e.g. multiple hoppers under one shared body).
    Default 1x1 — every existing preset/catalog entry is unaffected.

    Args:
        segment (dict): See segment_volume() for the dict schema. May
            include "cols" and "rows" (positive ints).

    Returns:
        int: cols * rows
    """
    return segment.get("cols", 1) * segment.get("rows", 1)


def enclosure_volume_and_length(segments):
    """
    Total volume and stacked height of an enclosure built from segments.

    Each segment's volume is scaled by its own segment_count() (side-by-side
    copies), but height is not — parallel copies occupy the same vertical
    span, not an additional one, so the flame-travel length H is unaffected
    by tiling.

    Args:
        segments (list[dict]): Ordered list of segment dicts, each stacked
            along the same axis. See segment_volume() for the dict schema.

    Returns:
        tuple[float, float]: (V, L) — total volume [m³], total height [m]
    """
    V = sum(segment_volume(s) * segment_count(s) for s in segments)
    L = sum(s["h"] for s in segments)
    return V, L
