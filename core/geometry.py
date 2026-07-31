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


def equivalent_diameter(V, L):
    """
    Diameter of a cylinder with the same volume and length as the enclosure.

    Args:
        V (float): Total volume [m³]
        L (float): Total length [m]

    Returns:
        float: Equivalent diameter [m], 0.0 if L <= 0
    """
    return 2.0 * math.sqrt(V / (math.pi * L)) if L > 0 else 0.0


def ld_ratio(L, D):
    """
    Enclosure L/D ratio.

    Args:
        L (float): Total length [m]
        D (float): Characteristic diameter [m]

    Returns:
        float: L/D [-], 0.0 if D <= 0
    """
    return L / D if D > 0 else 0.0
