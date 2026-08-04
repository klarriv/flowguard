import math

# ──────────────────────────────────────────────────────────────────────────────
# NFPA 68 (2023) — Chapter 6
# Fundamentals of Venting of Deflagrations
# ──────────────────────────────────────────────────────────────────────────────
# Scope: General design equations shared across Chapter 7 (gas) and Chapter 8
#        (dust) venting — deflagration index, enclosure/support design
#        pressure, L/D and hydraulic diameter, and fireball / external
#        pressure hazard zones.


# ──────────────────────────────────────────────────────────────────────────────
# §6.1 — Basic Concepts
# ──────────────────────────────────────────────────────────────────────────────

def deflagration_index(dP_dt_max, V):
    """
    Deflagration index K from the maximum rate of pressure rise attained by
    combustion in a closed vessel of volume V ("cube-root law").

    Args:
        dP_dt_max (float): Maximum rate of pressure rise [bar/s]
        V         (float): Closed vessel volume [m³]

    Returns:
        float: Deflagration index K [bar·m/s]

    Reference:
        NFPA 68 (2023), §6.1.1, Eq. 6.1.1
    """
    return dP_dt_max * V ** (1 / 3)


# ──────────────────────────────────────────────────────────────────────────────
# §6.3.1 — Enclosure Design Pressure Selection Criteria
# ──────────────────────────────────────────────────────────────────────────────

def max_pred_deformation_permitted(Fu, Pmawp):
    """
    Maximum permitted Pred where permanent deformation, but not rupture, of
    the enclosure can be accepted.

    Args:
        Fu    (float): Ratio of ultimate stress to allowable stress of the
                       enclosure material, per the ASME BPVC [-]
        Pmawp (float): Enclosure design pressure per the ASME BPVC [bar-g]

    Returns:
        float: Maximum permitted Pred [bar-g]

    Reference:
        NFPA 68 (2023), §6.3.1.3.2, Eq. 6.3.1.3.2a
    """
    return (2 / 3) * Fu * Pmawp


def max_pred_no_deformation_permitted(Fy, Pmawp):
    """
    Maximum permitted Pred where permanent deformation of the enclosure
    cannot be accepted.

    Args:
        Fy    (float): Ratio of yield stress to allowable stress of the
                       enclosure material, per the ASME BPVC [-]
        Pmawp (float): Enclosure design pressure per the ASME BPVC [bar-g]

    Returns:
        float: Maximum permitted Pred [bar-g]

    Reference:
        NFPA 68 (2023), §6.3.1.3.2, Eq. 6.3.1.3.2b
    """
    return (2 / 3) * Fy * Pmawp


# ──────────────────────────────────────────────────────────────────────────────
# §6.3.2 — Enclosure Strength vs. Dynamic Load
# ──────────────────────────────────────────────────────────────────────────────

DLF_DEFAULT = 1.5   # §6.3.2.1 — worst-case default absent detailed structural analysis


def max_pred_dynamic(Pes, DLF=DLF_DEFAULT):
    """
    Maximum permitted Pred accounting for the dynamic load factor of the
    enclosure's structural response.

    Args:
        Pes (float): Enclosure strength evaluated from static pressure
                     calculations, for either deformation or burst [bar-g]
        DLF (float): Dynamic load factor = Xm/Xs, where Xm is the maximum
                     dynamic deflection and Xs is the static deflection
                     produced by the same peak load applied statically [-].
                     Default DLF_DEFAULT = 1.5, the worst-case value
                     permitted absent a detailed structural response
                     analysis (§6.3.2.1).

    Returns:
        float: Maximum permitted Pred [bar-g]

    Reference:
        NFPA 68 (2023), §6.3.2, Eq. 6.3.2
    """
    return Pes / DLF


# ──────────────────────────────────────────────────────────────────────────────
# §6.3.5 — Enclosure Support Criteria
# ──────────────────────────────────────────────────────────────────────────────

DLF_REACTION_FORCE         = 1.2   # §6.3.5.2
REACTION_FORCE_UNIT_FACTOR = 100   # a, SI units → Fr in kN                §6.3.5.2
REACTION_DURATION_COEFF_SI = 4.3e-3   # b, SI units [s]                    §6.3.5.5


def reaction_force(Av, Pred, DLF=DLF_REACTION_FORCE, a=REACTION_FORCE_UNIT_FACTOR):
    """
    Maximum reaction force on the supporting structure resulting from
    combustion venting.

    Args:
        Av   (float): Vent area [m²]
        Pred (float): Maximum pressure developed during venting [bar-g]
        DLF  (float): Dynamic load factor. Default DLF_REACTION_FORCE = 1.2
                      (§6.3.5.2).
        a    (float): Units conversion factor. Default
                      REACTION_FORCE_UNIT_FACTOR = 100 for SI units
                      (Av in m², Pred in bar-g, Fr in kN).

    Returns:
        float: Maximum reaction force Fr [kN]

    Reference:
        NFPA 68 (2023), §6.3.5.2, Eq. 6.3.5.2
    """
    return a * DLF * Av * Pred


def reaction_force_duration(Pmax, Pred, V, Av, b=REACTION_DURATION_COEFF_SI):
    """
    Duration of the reaction force pressure pulse after vent opening.
    Represents the available duration data within −37 percent to +118 percent.

    Args:
        Pmax (float): Maximum pressure developed in an unvented explosion [bar-g]
        Pred (float): Maximum pressure developed during venting [bar-g]
        V    (float): Enclosure volume [m³]
        Av   (float): Area of vent, without vent duct [m²]
        b    (float): Empirical coefficient. Default REACTION_DURATION_COEFF_SI
                      = 4.3e-3 for SI units (V in m³, Av in m²); use 1.3e-3
                      for imperial units (V in ft³, Av in ft²).

    Returns:
        float: Duration of the pressure pulse tf [s]

    Reference:
        NFPA 68 (2023), §6.3.5.5, Eq. 6.3.5.5
    """
    return b * math.sqrt(Pmax / Pred) * (V / Av)


def total_impulse(Fr, tf):
    """
    Total impulse experienced by the structure supporting a vented enclosure
    during deflagration venting.

    Args:
        Fr (float): Maximum reaction force from reaction_force() [kN]
        tf (float): Duration of the pressure pulse from
                    reaction_force_duration() [s]

    Returns:
        float: Total impulse I [kN·s]

    Reference:
        NFPA 68 (2023), §6.3.5.6, Eq. 6.3.5.6
    """
    return 0.52 * Fr * tf


# ──────────────────────────────────────────────────────────────────────────────
# §6.4.3 — L/D of Elongated Enclosures
# ──────────────────────────────────────────────────────────────────────────────

def effective_area(Veff, H):
    """
    Effective cross-sectional area of an enclosure, for use in the
    hydraulic diameter equations below.

    Args:
        Veff (float): Effective volume — the volume of the part of the
                      enclosure through which the flame passes as it
                      travels along H [m³]
        H    (float): Maximum flame travel length [m]

    Returns:
        float: Effective cross-sectional area Aeff [m²]

    Reference:
        NFPA 68 (2023), §6.4.3.5
    """
    return Veff / H


def hydraulic_diameter(Aeff, p):
    """
    Effective hydraulic diameter of an enclosure cross section, general form.

    Args:
        Aeff (float): Effective cross-sectional area = Veff / H [m²]
        p    (float): Perimeter of the general cross-sectional shape [m]

    Returns:
        float: Effective hydraulic diameter Dhe [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6, Eq. 6.4.3.6
    """
    return 4 * (Aeff / p)


def hydraulic_diameter_circular(Aeff):
    """
    Effective hydraulic diameter for a generally cylindrical enclosure (and
    any hopper extension), based on a circular cross section.

    Args:
        Aeff (float): Effective cross-sectional area [m²]

    Returns:
        float: Effective hydraulic diameter Dhe [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6.1, Eq. 6.4.3.6.1
    """
    return (4 * Aeff / math.pi) ** 0.5


def hydraulic_diameter_square(Aeff):
    """
    Effective hydraulic diameter for a generally rectangular or square
    enclosure with an aspect ratio between 1 and 1.2, based on a square
    cross section.

    Args:
        Aeff (float): Effective cross-sectional area [m²]

    Returns:
        float: Effective hydraulic diameter Dhe [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6.2, Eq. 6.4.3.6.2
    """
    return Aeff ** 0.5


def rect_characteristic_length(Aeff, R):
    """
    Characteristic length D1 of a rectangular cross section with aspect
    ratio R ≥ 1.2, used to build up the perimeter in
    hydraulic_diameter_rectangular().

    Args:
        Aeff (float): Effective cross-sectional area [m²]
        R    (float): Aspect ratio of the largest cross section [-]

    Returns:
        float: Characteristic length D1 [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6.3, Eq. 6.4.3.6.3a
    """
    return (Aeff / R) ** 0.5


def rect_perimeter(D1, R):
    """
    Perimeter of a rectangular cross section with aspect ratio R ≥ 1.2.

    Args:
        D1 (float): Characteristic length from rect_characteristic_length() [m]
        R  (float): Aspect ratio of the largest cross section [-]

    Returns:
        float: Perimeter p [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6.3, Eq. 6.4.3.6.3b
    """
    return 2 * (R + 1) * D1


def hydraulic_diameter_rectangular(Aeff, R):
    """
    Effective hydraulic diameter for a generally rectangular enclosure with
    aspect ratio R ≥ 1.2. Orchestrates Eq. 6.4.3.6.3a–c in sequence.

    Args:
        Aeff (float): Effective cross-sectional area [m²]
        R    (float): Aspect ratio of the largest cross section [-]

    Returns:
        float: Effective hydraulic diameter Dhe [m]

    Reference:
        NFPA 68 (2023), §6.4.3.6.3, Eq. 6.4.3.6.3a–c
    """
    D1 = rect_characteristic_length(Aeff, R)
    p  = rect_perimeter(D1, R)
    return 4 * Aeff / p


def ld_ratio(H, Dhe):
    """
    Enclosure L/D ratio for use throughout this standard.

    Args:
        H   (float): Maximum flame travel length, taken along the central
                     axis, from the farthest end of the enclosure to the
                     opposite end of the vent [m]
        Dhe (float): Effective hydraulic diameter [m]

    Returns:
        float: L/D ratio [-]

    Reference:
        NFPA 68 (2023), §6.4.3.7, Eq. 6.4.3.7
    """
    return H / Dhe


# ──────────────────────────────────────────────────────────────────────────────
# §6.8 — Fireball Dimensions
# ──────────────────────────────────────────────────────────────────────────────

FIREBALL_K_METAL    = 10   # K for metal dusts                             §6.8.3
FIREBALL_K_CHEMICAL = 8    # K for chemical and agricultural dusts         §6.8.3
ALPHA_HORIZONTAL    = 0.20   # §6.8.8 — horizontal vents
ALPHA_VERTICAL      = 0.25   # §6.8.8 — vertical (upward directed) vents


def fireball_length_gas(V, n=1):
    """
    Axial length, width, and height of the fireball hazard zone distributed
    around the centerline of each vent discharge, for gas deflagration
    venting. Not subject to a distance limit (§6.8.6).

    Args:
        V (float): Volume of the vented enclosure [m³]
        n (int):   Number of independent vents (§6.8.4). Default 1.

    Returns:
        float: Fireball hazard zone dimension LF [m]

    Reference:
        NFPA 68 (2023), §6.8.2, Eq. 6.8.2
    """
    return 3.1 * (V / n) ** 0.402


def fireball_length_dust(V, K, n=1):
    """
    Axial length, width, and height of the fireball hazard zone distributed
    around the centerline of each vent discharge, for dust deflagration
    venting. Axial distance is limited to 60 m (§6.8.5).

    Args:
        V (float): Volume of the vented enclosure [m³]
        K (float): Flame length factor [-]. Use FIREBALL_K_METAL = 10 for
                   metal dusts, FIREBALL_K_CHEMICAL = 8 for chemical and
                   agricultural dusts.
        n (int):   Number of independent vents (§6.8.4). Default 1.

    Returns:
        float: Fireball hazard zone dimension LF [m]

    Reference:
        NFPA 68 (2023), §6.8.3, Eq. 6.8.3
    """
    return K * (V / n) ** (1 / 3)


def external_pressure_cubic(Pred, Av, V):
    """
    Approximate external pressure resulting from venting of a cubic vessel.

    Args:
        Pred (float): Reduced pressure [bar-g]
        Av   (float): Vent area [m²]
        V    (float): Enclosure volume [m³]

    Returns:
        float: External pressure Pmax,a [bar-g]

    Reference:
        NFPA 68 (2023), §6.8.7, Eq. 6.8.7
    """
    return 0.2 * Pred * Av ** 0.1 * V ** 0.18


def external_pressure_distance(Pmax_a, LF, r, alpha=ALPHA_HORIZONTAL):
    """
    Approximate maximum external pressure at a distance beyond the fireball
    hazard zone. Valid only for distances r > α · LF.

    Args:
        Pmax_a (float): External pressure at the vent from
                        external_pressure_cubic() [bar-g]
        LF     (float): Maximum length of the fireball [m]
        r      (float): Distance from the vent [m]
        alpha  (float): Directional factor [-]. Default ALPHA_HORIZONTAL = 0.20
                        for horizontal vents; use ALPHA_VERTICAL = 0.25 for
                        vertical (upward directed) vents.

    Returns:
        float: Maximum external pressure Pmax,r [bar-g]

    Reference:
        NFPA 68 (2023), §6.8.8, Eq. 6.8.8
    """
    return Pmax_a * (alpha * LF / r)
