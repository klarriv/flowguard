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
        