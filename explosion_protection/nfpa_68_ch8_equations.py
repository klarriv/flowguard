import math
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# NFPA 68 (2023) — Chapter 8
# Venting of Deflagrations of Dusts and Hybrid Mixtures
# ──────────────────────────────────────────────────────────────────────────────
# Scope: All enclosures with L/D ≤ 6 handling combustible dusts or hybrid
#        mixtures at near-atmospheric or elevated/subatmospheric initial pressure.

# ──────────────────────────────────────────────────────────────────────────────
# §8.2.1 — Minimum Vent Area Requirement
# ──────────────────────────────────────────────────────────────────────────────

def vent_area_atm(Pstat, KSt, V, Pmax, Pred):
    """
    Minimum vent area for near-atmospheric initial pressure
    (−0.2 bar-g ≤ P_initial ≤ 0.2 bar-g).

    Args:
        Pstat (float): Nominal static burst pressure of the vent [bar-g]
        KSt   (float): Deflagration index [bar·m/s]
        V     (float): Enclosure volume [m³]
        Pmax  (float): Maximum pressure of unvented deflagration at
                       atmospheric initial pressure [bar-g]
        Pred  (float): Reduced pressure after deflagration venting [bar-g]

    Returns:
        float: Minimum vent area Av0 [m²]

    Reference:
        NFPA 68 (2023), §8.2.1.1, Eq. 8.2.1.1
    """
    return 1e-4 * (1 + 1.54 * Pstat ** (4 / 3)) * KSt * V ** 0.75 * math.sqrt(Pmax / Pred - 1)


def vent_area_elevated_pressure(Pstat, Pinitial, KSt, V, Pmax, Pred):
    """
    Minimum vent area for elevated or subatmospheric initial pressure
    (P_initial > 0.2 bar-g  OR  P_initial < −0.2 bar-g).

    Intermediate quantities Peffective, PEmax, and Pi_effective are computed
    internally and also returned for traceability.

    Args:
        Pstat    (float): Static burst pressure of the vent [bar-g]
        Pinitial (float): Enclosure pressure at moment of ignition [bar-g]
        KSt      (float): Deflagration index [bar·m/s]
        V        (float): Enclosure volume [m³]
        Pmax     (float): Maximum pressure of unvented deflagration at
                          atmospheric initial pressure [bar-g]
        Pred     (float): Reduced pressure [bar-g]

    Returns:
        tuple:
            Av0          (float): Minimum vent area [m²]
            Peffective   (float): Effective pressure = 1/3 · Pinitial [bar-g]
            PEmax        (float): Maximum pressure of unvented deflagration
                                  at initial pressure [bar-g]
            Pi_effective (float): Pressure ratio Π_effective [-]

    Reference:
        NFPA 68 (2023), §8.2.1.2, Eq. 8.2.1.2
    """
    Peffective = Pinitial / 3.0
    PEmax      = (Pmax + 1) * (Pinitial + 1) - 1   # [(bar-abs)(bar-abs)/1 bar-abs − 1]
    Pi_eff     = (Pred - Peffective) / (PEmax - Peffective)

    Pstat_adj  = (Pstat - Pinitial) / (1 + Peffective)
    bracket    = 1 + 1.54 * Pstat_adj ** (4 / 3)
    Av0        = 1e-4 * bracket * KSt * V ** 0.75 * math.sqrt(1 / Pi_eff - 1)
    return Av0, Peffective, PEmax, Pi_eff


def vent_area_subatm_simplified(Pstat, KSt, V, Pmax, Pred):
    """
    Simplified minimum vent area for subatmospheric initial pressure
    (P_initial < −0.2 bar-g). Permitted alternative to Eq. 8.2.1.2.

    Args:
        Pstat (float): Static burst pressure of the vent [bar-g]
        KSt   (float): Deflagration index [bar·m/s]
        V     (float): Enclosure volume [m³]
        Pmax  (float): Maximum pressure of unvented deflagration at
                       atmospheric initial pressure [bar-g]
        Pred  (float): Reduced pressure [bar-g]

    Returns:
        float: Minimum vent area Av0 [m²]

    Reference:
        NFPA 68 (2023), §8.2.1.2.2, Eq. 8.2.1.2.2
    """
    return 1.1e-4 * (1 + 1.54 * Pstat ** (4 / 3)) * KSt * V ** 0.75 * math.sqrt(Pmax / Pred - 1)


# ──────────────────────────────────────────────────────────────────────────────
# §8.2.2 — Effects of Elevated L/D
# ──────────────────────────────────────────────────────────────────────────────

def vent_area_ld_correction(Av0, LD, Pred, Pinitial=0.0):
    """
    Required vent area corrected for enclosure L/D ratio (2 < L/D ≤ 6).

    When L/D ≤ 2, Av1 = Av0.
    When P_initial < 0.2 bar-g, Pinitial shall be set to zero (§8.2.2.4).

    Args:
        Av0      (float): Vent area from §8.2.1 [m²]
        LD       (float): Enclosure length-to-diameter ratio [-]
        Pred     (float): Reduced pressure after deflagration venting [bar-g]
        Pinitial (float): Enclosure pressure at moment of ignition [bar-g].
                          Set to 0.0 when P_initial < 0.2 bar-g per §8.2.2.4.

    Returns:
        float: L/D-corrected vent area Av1 [m²]

    Reference:
        NFPA 68 (2023), §8.2.2.3, Eq. 8.2.2.3
    """
    if LD <= 2:
        return Av0
    factor = 1 + 0.6 * (LD - 2) ** 0.75 * math.exp(-0.95 * (Pred / (1 + Pinitial)) ** 2)
    return Av0 * factor


# ──────────────────────────────────────────────────────────────────────────────
# §8.2.4 — Effects of Additional Turbulence
# ──────────────────────────────────────────────────────────────────────────────

def axial_velocity(Q, A):
    """
    Average axial gas velocity in an enclosure.

    Args:
        Q (float): Volumetric air flow rate [m³/s]
        A (float): Average cross-sectional area of the flow path [m²]

    Returns:
        float: Average axial gas velocity v [m/s]

    Reference:
        NFPA 68 (2023), §8.2.4.1, Eq. 8.2.4.1
    """
    return Q / A


def tangential_velocity(Q, Ain):
    """
    Tangential velocity from tangential inlet = Q/Ain (A.8.2.4.2).
    Effective tangential air velocity = 0.5 · v_tan_max (§8.2.4.2).

    Args:
        Q (float): Volumetric air flow rate [m³/s]
        Ain (float): Inlet cross-sectional area [m²]

    Returns:
        float: Effective tangential velocity vtan [m/s]

    Reference:
        NFPA 68 (2023), A.8.2.4.2
        NFPA 68 (2023), §8.2.4.2
    """
    return 0.5 * (Q / Ain)


def vent_area_turbulence(Av1, vaxial, vtan):
    """
    Vent area corrected for additional turbulence when either vaxial or vtan
    exceeds 20 m/s.

    When max(vaxial, vtan) ≤ 20 m/s, Av2 = Av1 (§8.2.4.5).

    Args:
        Av1    (float): Vent area from §8.2.2 [m²]
        vaxial (float): Axial air velocity [m/s]
        vtan   (float): Tangential air velocity (= 0.5 · vtan_max) [m/s]

    Returns:
        float: Turbulence-corrected vent area Av2 [m²]

    Reference:
        NFPA 68 (2023), §8.2.4.6, Eq. 8.2.4.6
    """
    v_max = max(vaxial, vtan)
    if v_max <= 20.0:
        return Av1
    return (1 + (v_max - 20) / 36 * 0.7) * Av1


def vent_area_building_turbulence(Av1):
    """
    Vent area for buildings with a dust explosion hazard (§8.2.4.7).
    A factor of 1.7 is applied to account for enhanced turbulence in buildings.

    Args:
        Av1 (float): Vent area from §8.2.2 [m²]

    Returns:
        float: Building turbulence-corrected vent area Av2 [m²]

    Reference:
        NFPA 68 (2023), §8.2.4.7, Eq. 8.2.4.7
    """
    return 1.7 * Av1


# ──────────────────────────────────────────────────────────────────────────────
# §8.3 — Effects of Panel Inertia
# ──────────────────────────────────────────────────────────────────────────────

def panel_mass_threshold(Pred, n, V, KSt):
    """
    Threshold panel areal mass MT. When panel mass M ≤ MT, no inertia
    correction is needed (Av3 = Av2).

    Args:
        Pred (float): Reduced pressure after deflagration venting [bar-g]
        n    (int):   Number of vent panels [-]
        V    (float): Enclosure volume [m³]
        KSt  (float): Deflagration index [bar·m/s]

    Returns:
        float: Threshold panel areal mass MT [kg/m²]

    Reference:
        NFPA 68 (2023), §8.3.2, Eq. 8.3.2
    """
    return (6.67 * Pred ** 0.2 * n ** 0.3 * (V / KSt ** 0.5)) ** 1.67


def vent_area_panel_inertia(Av2, M, MT, KSt, n, V, Pred, Fsh=1.0):
    """
    Vent area corrected for vent panel inertia. Only applied when M > MT and
    M ≤ 40 kg/m². For M > 40 kg/m² use Annex G (§8.3.3).

    When KSt < 75 bar·m/s, KSt = 75 shall be used in this equation (§8.3.5).

    Args:
        Av2  (float): Vent area from §8.2.4 [m²]
        M    (float): Vent panel areal mass [kg/m²]
        MT   (float): Threshold panel areal mass from panel_mass_threshold() [kg/m²]
        KSt  (float): Deflagration index [bar·m/s]
        n    (int):   Number of vent panels [-]
        V    (float): Enclosure volume [m³]
        Pred (float): Reduced pressure after deflagration venting [bar-g]
        Fsh  (float): Shape factor — 1.0 for translating panels,
                      1.1 for hinged panels [-] (§8.3.4)

    Returns:
        float: Panel-inertia-corrected vent area Av3 [m²]

    Reference:
        NFPA 68 (2023), §8.3.4, Eq. 8.3.4
    """
    if M <= MT:
        return Av2
    KSt_eff = max(KSt, 75.0)   # §8.3.5
    inertia_factor = 1 + 0.0075 * M ** 0.6 * (KSt_eff ** 0.5 / (n ** 0.3 * V * Pred ** 0.2))
    return Fsh * inertia_factor * Av2


# ──────────────────────────────────────────────────────────────────────────────
# §8.4 — Effects of Partial Volume
# ──────────────────────────────────────────────────────────────────────────────

def partial_volume_fraction(Me, Venc, Vsolid, cw):
    """
    Partial volume fill fraction Xr for process enclosures.

    Args:
        Me     (float): Total mass of combustible dust that could be suspended
                        inside the enclosure [g]
        Venc   (float): Enclosure volume [m³]
        Vsolid (float): Volume of solid objects inside the enclosure [m³]
        cw     (float): Worst-case dust concentration [g/m³].
                        Use 200 g/m³ if no measured value is available (§8.4.2.2).

    Returns:
        float: Fill fraction Xr [-]

    Reference:
        NFPA 68 (2023), §8.4.1, Eq. 8.4.1
    """
    cr = 0.5 * cw
    return (Me / (Venc - Vsolid)) / cr


def vent_area_partial_volume(Av3, Xr, Pred, Pmax):
    """
    Vent area adjusted for partial volume deflagration. Applied when Xr > Π
    and Xr < 1.0. When Xr ≤ Π, no venting is required (§8.4.3.1).
    When partial volume is not applied, Av4 = Av3 (§8.4.3.2).

    Args:
        Av3  (float): Vent area for full-volume deflagration [m²]
        Xr   (float): Partial volume fill fraction [-]
        Pred (float): Reduced pressure [bar-g]
        Pmax (float): Maximum pressure of unvented deflagration at
                      atmospheric initial pressure [bar-g]

    Returns:
        float: Partial-volume vent area Av4 [m²], or 0.0 if Xr ≤ Π
               (no venting required).

    Reference:
        NFPA 68 (2023), §8.4.3, Eq. 8.4.3
    """
    Pi = Pred / Pmax
    if Xr >= 1.0: 
        return Av3
    if Xr <= Pi:
        return 0.0   # §8.4.3.1 — no deflagration venting required
    return Av3 * Xr ** (-1 / 3) * math.sqrt((Xr - Pi) / (1 - Pi))


# ──────────────────────────────────────────────────────────────────────────────
# §8.4.5 — Building Partial Volumes
# ──────────────────────────────────────────────────────────────────────────────

def entrainment_threshold_velocity(rho_p):
    """
    Threshold entrainment velocity for a dust layer.

    Args:
        rho_p (float): Particle density [kg/m³]

    Returns:
        float: Threshold velocity Ut [m/s]

    Reference:
        NFPA 68 (2023), §8.4.5.3.5, Eq. 8.4.5.3.5a
    """
    return 0.46 * rho_p ** (1 / 3)


def entrained_mass_flux(rho, Ut, U=50):
    """
    Maximum entrainment mass flux from a dust layer surface.

    Only valid when U > Ut. Returns 0.0 if U ≤ Ut.

    Args:
        rho (float): Gas density [kg/m³]
        U   (float): Free-stream velocity [m/s] (default = 50m/s)
        Ut  (float): Threshold velocity from entrainment_threshold_velocity() [m/s]

    Returns:
        float: Entrained mass flux m" [kg/(m²·s)]

    Reference:
        NFPA 68 (2023), §8.4.5.3.5, Eq. 8.4.5.3.5b
    """
    if U <= Ut:
        return 0.0
    return 0.002 * rho * U * (U ** 0.5 - Ut ** 2 / U ** 1.5)


def max_entrained_mass(m_flux, A, t):
    """
    Maximum mass entrained during an initiating event.

    Args:
        m_flux (float): Entrained mass flux [kg/(m²·s)]
        A      (float): Surface area [m²]
        t      (float): Initiating event duration [s]

    Returns:
        float: Maximum entrained mass Mmax [kg]

    Reference:
        NFPA 68 (2023), §8.4.5.3.5, Eq. 8.4.5.3.5c
    """
    return m_flux * A * t


def entrainment_factor(Mmax, M):
    """
    Entrainment factor ηD for a dust layer. Capped at 1.0 when Mmax ≥ M.

    Args:
        Mmax (float): Maximum entrained mass [kg]
        M    (float): Average accumulation mass [kg]

    Returns:
        float: Entrainment factor ηD [-]

    Reference:
        NFPA 68 (2023), §8.4.5.3.5, Eq. 8.4.5.3.5d
    """
    return min(Mmax / M, 1.0)


def building_partial_volume_fraction(
    Mf_bar, Af_dusty, eta_Dfloor, Afs,
    Ms_bar, Asur, eta_Dsur, Ass,
    Me, V, Vsolid, cw
):
    """
    Worst-case building partial volume fraction Xr.

    Args:
        Mf_bar     (float): Average mass of floor samples [g]
        Af_dusty   (float): Total area of floor with dust deposits [m²]
        eta_Dfloor (float): Entrainment factor for floor accumulations [-]
        Afs        (float): Measured floor sample areas [m²]
        Ms_bar     (float): Average mass of surface samples [g]
        Asur       (float): Total area of surfaces with dust deposits [m²]
        eta_Dsur   (float): Entrainment factor for surface accumulations [-]
        Ass        (float): Measured sample areas of surfaces with dust
                            deposits [m²]
        Me         (float): Total mass of combustible dust releasable from
                            process equipment [g]
        V          (float): Building volume [m³]
        Vsolid     (float): Volume of solid objects [m³]
        cw         (float): Worst-case dust concentration [g/m³].
                            Use 200 g/m³ if no measured value (§8.4.5.3.2).

    Returns:
        float: Worst-case building partial volume fraction Xr [-]

    Reference:
        NFPA 68 (2023), §8.4.5.3, Eq. 8.4.5.3
    """
    cr    = 0.5 * cw
    Vfree = V - Vsolid
    floor = (Mf_bar * Af_dusty * eta_Dfloor) / (Afs * Vfree * cr)
    surf  = (Ms_bar * Asur * eta_Dsur)        / (Ass  * Vfree * cr)
    equip = Me / (Vfree * cr)
    return floor + surf + equip


def vent_area_building_partial_volume(Av3, Xr, Pred, Pmax):
    """
    Minimum required vent area for a building partial volume deflagration.

    When Xr > 1  → Av4 = Av3  (full volume governs).
    When Xr ≤ Π  → no venting required (return 0.0).
    When Π < Xr ≤ 1 → apply partial volume correction.

    Args:
        Av3  (float): Full-volume vent area [m²]
        Xr   (float): Worst-case building partial volume fraction [-]
        Pred (float): Reduced pressure [bar-g]
        Pmax (float): Maximum pressure of unvented deflagration [bar-g]

    Returns:
        float: Required vent area Av4 [m²]

    Reference:
        NFPA 68 (2023), §8.4.5.2, Eq. 8.4.5.2
    """
    Pi = Pred / Pmax
    if Xr > 1.0:
        return Av3
    if Xr <= Pi:
        return 0.0
    return Av3 * Xr ** (-1 / 3) * math.sqrt((Xr - Pi) / (1 - Pi))


# ──────────────────────────────────────────────────────────────────────────────
# §8.5 — Effects of Vent Ducts
# ──────────────────────────────────────────────────────────────────────────────
# Annex references used in this section:
#   A.8.5a  — Definition of K on static pressure drop
#   A.8.5b  — Root-isolation constraint: E1 = Avf·Lduct/V ≤ 1
#   A.8.5c  — D'Arcy friction factor (Colebrook fully-rough)
#   A.8.5d  — Worked example; K values for inlet/outlet/elbows/rain hat
#              are tabulated in the companion helper module (nfpa_68_ch8_duct_helper)
# ──────────────────────────────────────────────────────────────────────────────

# Reference roughness values [m] for use with darcy_friction_factor()
ROUGHNESS_SMOOTH_PIPE  = 0.0000015  # 0.0015 mm — smooth / plastic pipe
ROUGHNESS_CLEAN_STEEL  = 0.000046   # 0.046  mm — clean commercial steel
ROUGHNESS_USED_STEEL   = 0.00026    # 0.26   mm — corroded / repeatedly-used
                                    #             steel (NFPA 68 default, A.8.5c)

# Reference resistance coefficient K0 assumed in the test configurations that
# generated the §8.2.1 / §8.2.2 validation data (§8.5.1)
K0_REFERENCE = 1.5


def darcy_friction_factor(Dh, epsilon=ROUGHNESS_USED_STEEL):
    """
    D'Arcy friction factor for fully turbulent duct flow.

    Uses the Colebrook fully-rough (high-Re) simplification, which is
    appropriate for all practical vent duct Reynolds numbers:

        1 / √fD = −2 · log10(ε / (3.7 · Dh))      [Eq. A.8.5c]

    This is equivalent to the Moody fully-rough asymptote and requires no
    iteration.

    Args:
        Dh      (float): Internal hydraulic diameter of the duct [m]
        epsilon (float): Absolute internal roughness [m].
                         Default ROUGHNESS_USED_STEEL = 2.6e-4 m, which
                         NFPA 68 assumes for steel ducts that have been
                         repeatedly exposed to combustion events. (A.8.5c)

    Returns:
        float: D'Arcy friction factor fD [-]

    Reference:
        NFPA 68 (2023), Annex A.8.5c
    """
    return (1.0 / (1.14 - 2.0 * math.log10(epsilon / Dh))) ** 2


def duct_resistance_coefficient(Kinlet, fD, Lduct, Dh, K_elbows=0.0, Koutlet=0.0):
    """
    Overall resistance coefficient K of the vent duct system, defined on the
    static pressure drop from enclosure to duct exit at average flow velocity U:

        K ≡ ΔP / (½ ρ U²)    [Eq. A.8.5a]

    Assembled as:

        K = K_inlet + f_D · L_duct / D_h + K_elbows + K_outlet + …  [Eq. 8.5.1d]

    Typical K values (from Annex figures — tabulated in duct_helper module):
        Inserted duct inlet  →  K_inlet = 2.0   [Fig. A.8.5(a)]
        Flush duct inlet     →  K_inlet = 1.5   [Fig. A.8.5(a)]
        Plain duct outlet    →  K_outlet = 0.0  [Fig. A.8.5(a)]
        Round elbow (R/D=1.5)→  K = 0.39/elbow [Fig. A.8.5(b)]
        Rain hat (H=0.5D)    →  K = 0.73        [Fig. A.8.5(d)]

    Note on loss coefficient convention (A.8.5):
        K must be based on the STATIC pressure drop and on the average duct
        velocity U. Some references define K on total pressure or a different
        velocity; ensure consistency before combining coefficients.

    Args:
        Kinlet   (float): Inlet resistance coefficient [-].
                          Use 1.5 for flush inlet, 2.0 for inserted inlet.
        fD       (float): D'Arcy friction factor from darcy_friction_factor() [-]
        Lduct    (float): Overall duct centerline length, including the
                          centerline path through all elbows and fittings [m]
        Dh       (float): Vent duct hydraulic diameter [m]
        K_elbows (float): Sum of resistance coefficients for all elbows and
                          fittings [-]. Default 0.0.
                          Use duct_helper.k_round_elbow() or
                          duct_helper.k_rect_elbow() for each elbow, then sum.
                          For angles other than 90°, scale proportionally.
        Koutlet  (float): Outlet resistance coefficient [-]. Default 0.0
                          (plain open outlet per Fig. A.8.5(a)).
                          Use duct_helper.k_rain_hat() when a rain hat is fitted.

    Returns:
        float: Overall resistance coefficient K [-]

    Reference:
        NFPA 68 (2023), §8.5.1, Eq. 8.5.1d; Annex A.8.5a, A.8.5(a)–(d)
    """
    return Kinlet + fD * Lduct / Dh + K_elbows + Koutlet


def _e1_e2(Avf, Lduct, V, Pstat, KSt):
    """
    Internal helper: compute intermediate duct parameters E1 and E2.

    E1 = Avf · Lduct / V            [Eq. 8.5.1b]
    E2 = 1e4 · Avf / [(1 + 1.54·Pstat^(4/3)) · KSt · V^(3/4)]  [Eq. 8.5.1c]

    Args:
        Avf   (float): Current vent area estimate [m²]
        Lduct (float): Duct overall length [m]
        V     (float): Enclosure volume [m³]
        Pstat (float): Vent static opening pressure [bar-g]
        KSt   (float): Deflagration index [bar·m/s]

    Returns:
        tuple: (E1 [-], E2 [-])
    """
    denom = (1 + 1.54 * Pstat ** (4 / 3)) * KSt * V ** 0.75
    E1 = Avf * Lduct / V
    E2 = 1e4 * Avf / denom
    return E1, E2


def vent_area_duct(Av4, Lduct, V, Pstat, KSt, K, K0=K0_REFERENCE,
                   tol=1e-6, max_iter=200):
    """
    Required vent area when a duct is attached to the vent opening.

    Solves Eq. 8.5.1a implicitly for Avf by successive substitution, isolating
    the physically meaningful (smaller) root by enforcing the constraint:

        E1 = Avf · Lduct / V  ≤  1     [Annex A.8.5b]

    The iteration applies:
        E1, E2  = _e1_e2(Avf, ...)
        Avf_new = Av4 · (1 + 1.18 · E1^0.8 · E2^0.4) · √(K / K0)

    Convergence behaviour:
        The equation set is non-linear and may have two mathematical roots for
        a given Pred. The upper root is an artifact; the A.8.5b constraint
        (E1 ≤ 1) keeps the iteration on the lower, meaningful branch.
        When no solution exists (duct too long / Pred too low), a RuntimeError
        is raised — reduce duct length or raise Pred. (§8.5.3)

    Applicability limits (caller's responsibility to verify):
        §8.5.4  Vent cover located at the duct entrance.
        §8.5.5  Initial pressure ≤ 0.2 bar-g.
        §8.5.6  Duct cross-section varies ≤ 10% along its length.
        §8.5.9  L_eff ≤ min(10000·Dh/KSt, 11000/KSt) — use max_duct_length().

    Args:
        Av4      (float): Vent area entering the duct correction step (after
                          all prior corrections: L/D, turbulence, panel inertia,
                          partial volume) [m²]
        Lduct    (float): Overall duct centerline length [m]
        V        (float): Enclosure volume [m³]
        Pstat    (float): Nominal static opening pressure of the vent [bar-g]
        KSt      (float): Deflagration index [bar·m/s]
        K        (float): Overall duct resistance coefficient from
                          duct_resistance_coefficient() [-]
        K0       (float): Reference resistance = K0_REFERENCE = 1.5 [-]
        tol      (float): Convergence tolerance for Avf [m²]. Default 1e-6.
        max_iter (int):   Maximum iterations before raising. Default 200.

    Returns:
        tuple:
            Avf (float): Required vent area with duct [m²]
            E1  (float): Duct intermediate parameter at the converged Avf [-]
            E2  (float): Duct intermediate parameter at the converged Avf [-]

    Raises:
        RuntimeError: If Avf does not converge within max_iter iterations, or
                      if E1 > 1 at convergence (upper root artifact detected).

    Reference:
        NFPA 68 (2023), §8.5.1, Eq. 8.5.1a–c; Annex A.8.5, A.8.5b
    """
    sqrt_K = math.sqrt(K / K0)
    Avf = Av4   # initial guess — starts on the lower branch

    for i in range(1, max_iter + 1):
        E1, E2  = _e1_e2(Avf, Lduct, V, Pstat, KSt)
        Avf_new = Av4 * (1 + 1.18 * E1 ** 0.8 * E2 ** 0.4) * sqrt_K

        if abs(Avf_new - Avf) < tol:
            # Check we are on the physically meaningful root
            E1_final, E2_final = _e1_e2(Avf_new, Lduct, V, Pstat, KSt)
            if E1_final > 1.0:
                raise RuntimeError(
                    f"Converged on the upper (artifact) root: E1 = {E1_final:.4f} > 1. "
                    "Reduce duct length, increase Pred, or strengthen the vessel. (§8.5.3, A.8.5b)"
                )
            return Avf_new, E1_final, E2_final

        Avf = Avf_new

    raise RuntimeError(
        f"vent_area_duct: Avf did not converge after {max_iter} iterations. "
        f"Last value: {Avf:.6f} m². "
        "Reduce duct length, increase Pred, or check inputs. (§8.5.3)"
    )


def pred_from_vent_area_duct(Avf_installed, Lduct, V, Pstat, KSt, K,
                              Pred_guess=1.0, K0=K0_REFERENCE,
                              tol=1e-6, max_iter=200,
                              av_func=None, av_func_kwargs=None):
    """
    Back-calculate the achieved Pred for an installed vent area when a duct is
    present. This is the inverse of vent_area_duct().

    The approach follows the worked example in Annex A.8.5: assume a Pred,
    compute Av0 → Av4 via the standard correction chain, then solve
    Eq. 8.5.1a–c for Avf; iterate over Pred until Avf matches the installed
    area.

    The caller supplies ``av_func``, a callable that maps ``Pred`` to the
    pre-duct vent area ``Av4`` (i.e., the result of §8.2.1 → §8.2.2 → §8.2.4
    → §8.3 → §8.4 for that Pred). If ``av_func`` is None, the function cannot
    determine Av4 and will raise ValueError.

    Args:
        Avf_installed  (float): Installed vent area [m²]
        Lduct          (float): Overall duct centerline length [m]
        V              (float): Enclosure volume [m³]
        Pstat          (float): Vent static opening pressure [bar-g]
        KSt            (float): Deflagration index [bar·m/s]
        K              (float): Overall duct resistance coefficient [-]
        Pred_guess     (float): Initial guess for Pred [bar-g]. Default 1.0.
        K0             (float): Reference resistance = K0_REFERENCE = 1.5 [-]
        tol            (float): Convergence tolerance for Pred [bar-g]. Default 1e-6.
        max_iter       (int):   Maximum bisection iterations. Default 200.
        av_func        (callable): f(Pred, **av_func_kwargs) → Av4 [m²].
                                   Must be monotonically decreasing in Pred.
        av_func_kwargs (dict):   Extra keyword arguments passed to av_func.

    Returns:
        float: Achieved reduced pressure Pred [bar-g]

    Raises:
        ValueError: If av_func is None.
        RuntimeError: If bisection does not converge within max_iter.

    Reference:
        NFPA 68 (2023), §8.5.1; Annex A.8.5 (worked example, steps 2–8)
    """
    if av_func is None:
        raise ValueError(
            "pred_from_vent_area_duct requires av_func: a callable "
            "f(Pred) → Av4 representing the full §8.2–§8.4 correction chain."
        )
    kw = av_func_kwargs or {}

    def _residual(Pred_try):
        Av4_try = av_func(Pred_try, **kw)
        Avf_try, _, _ = vent_area_duct(Av4_try, Lduct, V, Pstat, KSt, K, K0)
        return Avf_try - Avf_installed

    # Bracket: find Pred_lo (Avf > installed) and Pred_hi (Avf < installed)
    Pred_lo, Pred_hi = 0.01, Pred_guess
    # Expand upper bound until residual changes sign
    for _ in range(50):
        if _residual(Pred_hi) < 0:
            break
        Pred_hi *= 2.0
    else:
        raise RuntimeError(
            "Could not bracket the solution for Pred. "
            "The installed vent area may be too small for any finite Pred."
        )

    for _ in range(max_iter):
        Pred_mid = 0.5 * (Pred_lo + Pred_hi)
        r = _residual(Pred_mid)
        if abs(r) < tol or (Pred_hi - Pred_lo) < tol:
            return Pred_mid
        if r > 0:
            Pred_lo = Pred_mid
        else:
            Pred_hi = Pred_mid

    raise RuntimeError(
        f"pred_from_vent_area_duct: bisection did not converge after "
        f"{max_iter} iterations. Last Pred = {Pred_mid:.6f} bar-g."
    )


def max_duct_length(KSt, Dh, Pmax, Pred, V, Avf):
    """
    Maximum allowable effective vent duct length to avoid DDT conditions (§8.5.9).

    L_eff ≤ min(10000 · Dh / KSt,  11000 / KSt)
    where:
        L_eff  = min(Lduct, Ldusty)
        Ldusty = (Pmax − Pred) · V / Avf

    Args:
        KSt  (float): Deflagration index [bar·m/s]
        Dh   (float): Vent duct hydraulic diameter [m]
        Pmax (float): Maximum pressure of unvented deflagration [bar-g]
        Pred (float): Reduced pressure [bar-g]
        V    (float): Enclosure volume [m³]
        Avf  (float): Final vent area with duct correction applied [m²]

    Returns:
        tuple:
            Leff_max (float): Maximum allowable effective duct length [m]
            Ldusty   (float): Dusty flame length parameter [m]

    Reference:
        NFPA 68 (2023), §8.5.9, Eq. 8.5.9; Annex A.8.5 (example steps 9–10)
    """
    Leff_max = min(10000 * Dh / KSt, 11000 / KSt)
    Ldusty   = (Pmax - Pred) * V / Avf
    return Leff_max, Ldusty

# ──────────────────────────────────────────────────────────────────────────────
# §8.8 — Bucket Elevators
# ──────────────────────────────────────────────────────────────────────────────

def pred_increase_plastic_buckets(Pred, KSt):
    """
    Adjusted design Pred for bucket elevators equipped with plastic buckets,
    per Table 8.8.3.5, before applying vent spacing from Table 8.8.3.3.

    Args:
        Pred (float): Base design reduced pressure (0.2, 0.5, or 1.0 bar-g) [bar-g]
        KSt  (float): Deflagration index [bar·m/s]

    Returns:
        float: Adjusted Pred [bar-g]

    Reference:
        NFPA 68 (2023), §8.8.3.5, Table 8.8.3.5
    """
    if KSt < 100:
        factor = 1.20
    elif KSt <= 150:
        factor = 1.35
    else:   # 151–200 bar·m/s (>200 bar·m/s not covered by table)
        factor = 1.50
    return Pred * factor


# ──────────────────────────────────────────────────────────────────────────────
# §8.9 — Venting Internal to a Building (Building Pressure Rise Estimate)
# ──────────────────────────────────────────────────────────────────────────────

def building_pressure_rise(V1, V0, P0=1.013):
    """
    Estimated pressure increase in an unvented building caused by a
    deflagration vent discharge from internal equipment.

    Args:
        V1 (float): Volume of protected equipment [m³]
        V0 (float): Free volume of the building [m³]
        P0 (float): Ambient pressure [bar-abs]. Default 1.013 bar-abs (14.7 psia).

    Returns:
        float: Pressure rise ΔP [bar] (same units as P0)

    Reference:
        NFPA 68 (2023), §8.9.1.1, item (1)
    """
    return 1.74 * P0 * (V1 / V0)


# ──────────────────────────────────────────────────────────────────────────────
# §8.10 — Silos with Integral Bin Vents
# ──────────────────────────────────────────────────────────────────────────────

def bin_vent_area_split(Av_total, Vsilo, Vtotal):
    """
    Distribution of required vent area between a silo and its integral bin vent
    (air-material separator). Returns the minimum area that must stay on the
    silo and the remainder that may be placed on the bin vent surface.

    Args:
        Av_total (float): Total vent area for the bin vent–silo combination [m²]
        Vsilo    (float): Volume of the silo alone [m³]
        Vtotal   (float): Combined volume of silo + bin vent collector [m³]

    Returns:
        tuple:
            Av_silo_min (float): Minimum explosion vent area required on
                                 the silo [m²]
            Av_bin_vent (float): Vent area permitted on the bin vent surface [m²]

    Reference:
        NFPA 68 (2023), §8.10.1, Eq. 8.10.1a–b
    """
    Av_silo_min = (Vsilo / Vtotal) ** (2 / 3) * Av_total
    Av_bin_vent = Av_total - Av_silo_min
    return Av_silo_min, Av_bin_vent