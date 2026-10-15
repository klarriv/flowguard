"""
nfpa_68_ch7_orchestrator.py
===========================
Orchestrator for NFPA 68 (2023) Chapter 7 — Deflagration Vent Area for Gas Mixtures and Mists.

Calculation sequence
--------------------
1. Apply duct correction (§7.5)    — substitute P'red for Pred if a duct is present
2. Iterate lambda (§7.2.6)         — lambda depends on Av; Av depends on lambda
3. Compute Av0 (§7.2.1 or §7.2.2) — branch on Pred ≤ or > 0.5 bar-g
4. Apply partial volume (§7.3)     — optional; Av1 = Av0 if disabled or Xr ≥ 1
5. Apply panel inertia (§7.4)      — Av2 = Av1 if M ≤ MT

Usage
-----
    from nfpa_68_ch7_orchestrator import Enclosure, Gas, Vent, Duct, vent_area_gas

    enclosure = Enclosure(As=45.0, Dhe=3.2, Venc=60.0, LD=1.8)
    gas       = Gas(Su=0.45, Pmax=8.0, x_st=0.04)
    vent      = Vent(Pred=0.2, Pstat=0.05)
    duct      = Duct(length=4.0, Dh=0.6)   # or None if no duct

    result = vent_area_gas(enclosure, gas, vent, duct)
    print(result.Av2)   # final required vent area [m²]
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from .nfpa_68_ch7_equations import (
    # constants
    RHO_U_DEFAULT, GU_DEFAULT, GAMMA_B_DEFAULT, MU_U_DEFAULT, A_U_DEFAULT,
    CD_DEFAULT,
    # §7.2.1
    vent_area_low_pred, c_coefficient, c_coefficient_simplified,
    # §7.2.2
    delta_factor, vent_area_high_pred,
    # §7.2.6
    lambda_enhanced,
    # §7.3
    partial_volume_fraction, vent_area_partial_volume,
    # §7.4
    panel_mass_threshold, vent_area_panel_inertia,
    # §7.5
    pred_duct_short, pred_duct_long,
)


# ──────────────────────────────────────────────────────────────────────────────
# Input dataclasses
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Enclosure:
    """
    Geometric and obstruction properties of the protected enclosure.

    Attributes:
        As     (float): Internal surface area [m²]                        §7.2.5
        Dhe    (float): Hydraulic equivalent diameter [m]                 §6.4
        Venc   (float): Total enclosure volume [m³]
        LD     (float): Enclosure L/D ratio [-]                           §6.4
        Vsolid (float): Volume of solid objects inside enclosure [m³]     §7.3.2
        Aobs   (float): Total external surface area of obstructions [m²]  §7.2.6.2
        Vfree  (float): Free volume of the enclosure [m³] 
    """
    As:     float
    Dhe:    float
    Venc:   float
    LD:     float
    Vsolid: float = 0.0
    Aobs:   float = 0.0
    Vfree:  float = field(init=False)
    
    def __post_init__(self):
        self.Vfree = self.Venc - self.Vsolid

@dataclass
class Gas:
    """
    Combustion properties of the gas-air mixture.

    Attributes:
        Su      (float): Fundamental burning velocity [m/s]               §7.2.3.2
        Pmax    (float): Max pressure in a contained deflagration [bar-g] §7.2.1
        x_st    (float): Stoichiometric volume concentration [-]          §7.3.2
        rho_u   (float): Density of unburned gas-air mixture [kg/m³]      §7.2.3.3
        Gu      (float): Sonic flow mass flux [kg/(m²·s)]                 §7.2.3.4
        gamma_b (float): Ratio of specific heats, burned mixture [-]      §7.2.3.5
        mu_u    (float): Dynamic viscosity, unburned mixture [kg/(m·s)]   §7.2.3.6
        a_u     (float): Sound speed, unburned mixture [m/s]              §7.2.3.7
        Vgas    (float): Max volume of gas that can mix with air [m³]     §7.3.2
                         Required when partial_volume=True. Default None
                         (full-volume assumption).
    """
    Su:      float
    Pmax:    float
    x_st:    float
    rho_u:   float = RHO_U_DEFAULT
    Gu:      float = GU_DEFAULT
    gamma_b: float = GAMMA_B_DEFAULT
    mu_u:    float = MU_U_DEFAULT
    a_u:     float = A_U_DEFAULT
    Vgas:    Optional[float] = None


@dataclass
class Vent:
    """
    Vent panel and operating pressure properties.

    Attributes:
        Pred             (float): Max pressure developed in vented enclosure [bar-g] §7.2.1
        Pstat            (float): Nominal vent deployment / burst pressure [bar-g]   §7.2.2
        P0               (float): Enclosure pressure prior to ignition [bar-g]       §7.2.4.2
        n                (int):   Number of vent panels [-]                          §7.4.2
        M                (float): Vent panel areal mass [kg/m²]                      §7.4.1
        Fsh              (float): Shape factor — 1.0 translating, 1.1 hinged [-]    §7.4.3
        Cd               (float): Discharge coefficient [-]                          §7.2.4.1
        use_simplified_C (bool):  Use simplified C (Eq. 7.2.1.1) when Pmax < 9
                                  bar-g and stoich. conc. ≤ ~10 vol%.
    """
    Pred:             float
    Pstat:            float
    P0:               float = 0.0
    n:                int   = 1
    M:                float = 0.0
    Fsh:              float = 1.0
    Cd:               float = CD_DEFAULT
    use_simplified_C: bool  = False


@dataclass
class Duct:
    """
    Vent duct properties. Pass None to vent_area_gas() if no duct is present.

    Attributes:
        length (float): Duct length [m]
        Dh     (float): Duct hydraulic diameter [m]

    Note:
        Ducts < 3 m are treated as 3 m per §7.5.3.
        Ducts > 6 m are outside the scope of Chapter 7 — use test data.
    """
    length: float
    Dh:     float


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class VentAreaResult:
    """
    Full calculation result including all intermediate values for reporting.

    Attributes:
        Av0                   (float): Full-volume vent area before corrections [m²]
        Av1                   (float): Vent area after partial volume correction [m²]
        Av2                   (float): Final vent area after panel inertia correction [m²]
        lambda_               (float): Converged turbulent flame enhancement factor [-]
        lambda_iterations     (int):   Number of iterations to converge lambda
        Pred_eff              (float): Effective Pred used in calculation
                                       (P'red if duct present) [bar-g]
        C                     (float): C-coefficient [bar^0.5]
                                       Low-Pred path only; None for high-Pred.
        delta                 (float): Delta factor [-]
                                       High-Pred path only; None for low-Pred.
        Xr                    (float): Partial volume fill fraction [-]
                                       None if partial volume correction disabled.
        MT                    (float): Panel mass threshold [kg/m²]
        partial_volume_active (bool):  Whether partial volume correction reduced Av.
        panel_inertia_active  (bool):  Whether panel inertia correction increased Av.
        duct_active           (bool):  Whether duct pressure correction was applied.
        pred_path             (str):   Equation path taken: '§7.2.1 (low Pred)'
                                       or '§7.2.2 (high Pred)'.
    """
    Av0:                  float
    Av1:                  float
    Av2:                  float
    lambda_:              float
    lambda_iterations:    int
    Pred_eff:             float
    C:                    Optional[float]
    delta:                Optional[float]
    Xr:                   Optional[float]
    MT:                   float
    partial_volume_active: bool
    panel_inertia_active:  bool
    duct_active:           bool
    pred_path:            str


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _duct_pred(Pred: float, duct: Optional[Duct]) -> tuple[float, bool]:
    """
    Apply duct correction (§7.5) and return (P'red, duct_active).
    Selects Curve A or Curve B based on duct length and hydraulic diameter ratio.
    """
    if duct is None:
        return Pred, False

    n_diameters = duct.length / duct.Dh
    use_curve_b = (duct.length >= 3.0) or (n_diameters >= 4.0)

    if use_curve_b:
        return pred_duct_long(Pred), True
    return pred_duct_short(Pred), True


def _compute_av0(
    enclosure: Enclosure,
    gas: Gas,
    vent: Vent,
    Pred_eff: float,
    lambda_: float,
) -> tuple[float, Optional[float], Optional[float], str]:
    """
    Compute Av0 via the appropriate branch (§7.2.1 or §7.2.2).
    Returns (Av0, C, delta, path_label).
    """
    if Pred_eff <= 0.5:
        # Low-Pred path — §7.2.1
        if vent.use_simplified_C:
            C = c_coefficient_simplified(gas.Su, lambda_)
        else:
            C = c_coefficient(
                gas.Su, gas.rho_u, lambda_, gas.Gu,
                vent.Cd, gas.Pmax, vent.P0, gas.gamma_b
            )
        Av0 = vent_area_low_pred(enclosure.As, C, Pred_eff)
        return Av0, C, None, "§7.2.1 (low Pred)"

    else:
        # High-Pred path — §7.2.2
        d = delta_factor(vent.Pstat, vent.P0, gas.Pmax, gas.gamma_b)
        Av0 = vent_area_high_pred(
            enclosure.As, gas.Su, gas.rho_u, lambda_,
            gas.Gu, vent.Cd, gas.Pmax, Pred_eff, gas.gamma_b, d
        )
        return Av0, None, d, "§7.2.2 (high Pred)"


def _iterate_lambda(
    enclosure: Enclosure,
    gas: Gas,
    vent: Vent,
    Pred_eff: float,
    tol: float,
    max_iter: int,
    partial_volume: bool = False,
    debug: bool = False,
) -> tuple[float, int, float, float, float, Optional[float], float]:
    """
    Iterate lambda over the full correction chain until convergence.
    Returns (lambda_, n_iter, Av0, Av1, Av2, Xr, MT).
    """
    lambda_ = 1.0

    if debug:
        print(f"  {'Iter':>4}  {'lambda':>12}  {'Av0':>12}  {'delta':>12}")
        print(f"  {'-'*4}  {'-'*12}  {'-'*12}  {'-'*12}")
    
    for i in range(1, max_iter + 1):
        Av0, _, _, _ = _compute_av0(enclosure, gas, vent, Pred_eff, lambda_)
        # Partial volume correction (§7.3)
        if partial_volume and gas.Vgas is not None:
            Xr  = partial_volume_fraction(gas.Vgas, enclosure.Venc, enclosure.Vsolid, gas.x_st)
            Av1 = vent_area_partial_volume(Av0, Xr, Pred_eff, gas.Pmax)
        else:
            Xr  = None
            Av1 = Av0

        # Panel inertia correction (§7.4)
        MT  = panel_mass_threshold(Pred_eff, vent.n, enclosure.Vfree, gas.Su, lambda_)
        Av2 = vent_area_panel_inertia(Av1, vent.M, MT, gas.Su, lambda_, vent.n, enclosure.Vfree, Pred_eff, vent.Fsh)
        lambda_new = lambda_enhanced(
            gas.Su, gas.rho_u, enclosure.Dhe, gas.mu_u,
            Pred_eff, Av2, enclosure.Aobs, enclosure.As,
            enclosure.LD, gas.a_u
        )
        if debug:
            print(f"  {i:>4}  {lambda_new:>12.6f}  {Av0:>12.6f}  {abs(lambda_new - lambda_):>12.2e}")
        if abs(lambda_new - lambda_) < tol:
            if debug:
                print(f"  Converged in {i} iterations.")
            return lambda_new, i, Av0, Av1, Av2, Xr, MT
        lambda_ = lambda_new

    raise RuntimeError(
        f"lambda did not converge after {max_iter} iterations. "
        f"Last value: {lambda_:.6f}. Check input parameters."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────────────────────────────────────

def _validate_inputs(
    enclosure: Enclosure,
    gas: Gas,
    vent: Vent,
    duct: Optional[Duct],
    partial_volume: bool,
) -> None:
    """
    Raise ValueError for inputs that violate standard applicability limits.

    Reference:
        NFPA 68 (2023), §7.1.1, §7.2.1.2, §7.2.6.8, §7.4.1, §7.5.3.1
    """
    errors = []

    # §7.1.1 — Chapter 7 scope
    if enclosure.LD > 5:
        errors.append(
            f"Enclosure L/D = {enclosure.LD} exceeds 5. "
            f"Use Chapter 9 for L/D > 5. (§7.1.1)"
        )

    # §7.2.6.8 — Lambda equation limits
    if gas.Su >= 3.0:
        errors.append(f"Su = {gas.Su} m/s must be < 3 m/s. (§7.2.6.8)")
    if gas.Pmax >= 10.0:
        errors.append(f"Pmax = {gas.Pmax} bar-g must be < 10 bar-g. (§7.2.6.8)")

    # §7.2.1.2 — Pstat vs Pred limits
    if vent.Pred <= 0.1:
        if vent.Pstat > (vent.Pred - 0.024):
            errors.append(
                f"Pstat = {vent.Pstat} bar-g must be ≤ Pred − 0.024 = "
                f"{vent.Pred - 0.024:.3f} bar-g when Pred ≤ 0.1 bar-g. (§7.2.1.2)"
            )
    else:
        if vent.Pstat >= 0.75 * vent.Pred:
            errors.append(
                f"Pstat = {vent.Pstat} bar-g must be < 0.75 × Pred = "
                f"{0.75 * vent.Pred:.3f} bar-g when Pred > 0.1 bar-g. (§7.2.1.2)"
            )

    # §7.4.1 — Panel mass upper bound
    if vent.M > 40.0:
        errors.append(
            f"Panel mass M = {vent.M} kg/m² exceeds 40 kg/m². (§7.4.1)"
        )

    # §7.5.3.1 — Duct length upper bound
    if duct is not None and duct.length > 6.0:
        errors.append(
            f"Duct length = {duct.length} m exceeds 6 m. "
            f"Eq. 7.5.2.2 is not valid beyond 6 m — use test data. (§7.5.3.1)"
        )

    # Partial volume — Vgas must be set if correction is requested
    if partial_volume and gas.Vgas is None:
        errors.append(
            "partial_volume=True but gas.Vgas is None. "
            "Provide gas.Vgas or set partial_volume=False."
        )

    if errors:
        raise ValueError(
            "NFPA 68 Ch. 7 input validation failed:\n  - " + "\n  - ".join(errors)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Main orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def vent_area_gas(
    enclosure: Enclosure,
    gas: Gas,
    vent: Vent,
    duct: Optional[Duct] = None,
    partial_volume: bool = True,
    tol: float = 1e-6,
    max_iter: int = 100,
    debug: bool = False,
) -> VentAreaResult:
    """
    Calculate the minimum required deflagration vent area for gas mixtures
    and mists per NFPA 68 (2023), Chapter 7.

    Applies corrections in the order prescribed by the standard:
        1. Duct pressure correction (§7.5)    — if duct is provided
        2. Lambda iteration (§7.2.6)          — converged iteratively
        3. Vent area Av0 (§7.2.1 or §7.2.2)  — branch on Pred ≤ 0.5 bar-g
        4. Partial volume correction (§7.3)   — if partial_volume=True and Xr < 1
        5. Panel inertia correction (§7.4)    — if M > MT

    Args:
        enclosure      (Enclosure):      Enclosure geometry and obstruction data.
        gas            (Gas):            Gas combustion and mixture properties.
        vent           (Vent):           Vent panel and operating pressure properties.
        duct           (Duct, optional): Vent duct properties. None if no duct.
        partial_volume (bool):           Apply partial volume correction (§7.3).
                                         Requires gas.Vgas to be set. Default True.
        tol            (float):          Convergence tolerance for lambda iteration.
                                         Default 1e-6.
        max_iter       (int):            Max lambda iterations before raising.
                                         Default 100.

    Returns:
        VentAreaResult: Dataclass containing Av2 (final vent area [m²]) and all
                        intermediate values for traceability and reporting.

    Raises:
        ValueError:   If input parameters violate standard applicability limits.
        RuntimeError: If lambda iteration does not converge within max_iter.

    Reference:
        NFPA 68 (2023), Chapter 7
    """
    _validate_inputs(enclosure, gas, vent, duct, partial_volume)

    # Step 1 — Duct correction (§7.5)
    Pred_eff, duct_active = _duct_pred(vent.Pred, duct)

    # Step 2 — Iterate lambda with full correction chain (§7.2.6, §7.3, §7.4)
    lambda_, n_iter, Av0, Av1, Av2, Xr, MT = _iterate_lambda(
        enclosure, gas, vent, Pred_eff, tol, max_iter, partial_volume, debug
    )

    # Step 3 — Vent area Av0 (§7.2.1 or §7.2.2) — recompute with converged lambda
    Av0, C, delta, pred_path = _compute_av0(enclosure, gas, vent, Pred_eff, lambda_)

    # Recompute Av1 and Av2 with converged lambda for consistency
    if partial_volume and gas.Vgas is not None:
        Av1 = vent_area_partial_volume(Av0, Xr, Pred_eff, gas.Pmax)
    else:
        Av1 = Av0
    Av2 = vent_area_panel_inertia(Av1, vent.M, MT, gas.Su, lambda_, vent.n, enclosure.Vfree, Pred_eff, vent.Fsh)

    # Correction activity flags
    partial_volume_active = partial_volume and Xr is not None and Xr < 1.0
    panel_inertia_active  = vent.M > MT
    
    return VentAreaResult(
        Av0=Av0,
        Av1=Av1,
        Av2=Av2,
        lambda_=lambda_,
        lambda_iterations=n_iter,
        Pred_eff=Pred_eff,
        C=C,
        delta=delta,
        Xr=Xr,
        MT=MT,
        partial_volume_active=partial_volume_active,
        panel_inertia_active=panel_inertia_active,
        duct_active=duct_active,
        pred_path=pred_path,
    )
