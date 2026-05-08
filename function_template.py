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

    Reference:
        Prismatoid formula — V = h/3 * (A1 + A2 + sqrt(A1*A2))
    """