import math

# ──────────────────────────────────────────────────────────────────────────────
# NFPA 68 (2023) — Chapter 7
# Venting Deflagrations of Gas Mixtures and Mists
# ──────────────────────────────────────────────────────────────────────────────
# Constants (§7.2.3, permitted defaults for stoich. conc. < 5 vol%, ambient T)
# ──────────────────────────────────────────────────────────────────────────────
RHO_U_DEFAULT   = 1.2       # Unburned gas-air density [kg/m³]             §7.2.3.3
GU_DEFAULT      = 230.1     # Sonic flow mass flux [kg/(m²·s)]             §7.2.3.4
GAMMA_B_DEFAULT = 1.15      # Ratio of specific heats, burned mixture [-]  §7.2.3.5
MU_U_DEFAULT    = 1.8e-5    # Dynamic viscosity, unburned mixture [kg/(m·s)] §7.2.3.6
A_U_DEFAULT     = 343.0     # Sound speed, unburned mixture [m/s]          §7.2.3.7
SU_MIST         = 0.46      # Burning velocity for mists [m/s]             §7.2.3.1
CD_DEFAULT      = 0.70      # Discharge coefficient [-]                    §7.2.4.1
CD_FULL_WALL    = 0.80      # Discharge coefficient, vent = full wall [-]  §7.2.4.1

# Lambda equation constants                                                 §7.2.6.1
_THETA  = 0.39
_BETA1  = 1.23
_BETA2  = 2.37e-3   # [m/s]


# ──────────────────────────────────────────────────────────────────────────────
# §7.2.1 — Vent Area, Low Pred (Pred ≤ 0.5 bar-g)
# ──────────────────────────────────────────────────────────────────────────────

def vent_area_low_pred(As, C, Pred):
    """
    Minimum vent area for low reduced pressure (Pred ≤ 0.5 bar-g).

    Args:
        As   (float): Enclosure internal surface area [m²]
        C    (float): C-coefficient [bar^0.5]
        Pred (float): Maximum pressure developed in a vented enclosure during a vented deflagration [bar-g]

    Returns:
        float: Minimum vent area Av0 [m²]

    Reference:
        NFPA 68 (2023), §7.2.1, Eq. 7.2.1a
    """
    return As * C / math.sqrt(Pred)


def c_coefficient(Su, rho_u, lambda_, Gu, Cd, Pmax, P0, gamma_b):
    """
    C-coefficient for use in the low-Pred vent area equation (general form).

    Args:
        Su      (float): Fundamental burning velocity [m/s]
        rho_u   (float): Mass density of unburned gas-air mixture [kg/m³]
        lambda_ (float): Turbulent flame enhancement factor [-]
        Gu      (float): Unburned gas-air sonic flow mass flux [kg/(m²·s)]
        Cd      (float): Vent flow discharge coefficient [-]
        Pmax    (float): Maximum pressure in a contained deflagration [bar-g]
        P0      (float): Enclosure pressure prior to ignition [bar-g]
        gamma_b (float): Ratio of specific heats for burned gas-air mixture [-]

    Returns:
        float: C-coefficient [bar^0.5]

    Reference:
        NFPA 68 (2023), §7.2.1, Eq. 7.2.1b
    """
    pressure_term = ((Pmax + 1) / (P0 + 1)) ** (1 / gamma_b) - 1
    return (Su * rho_u * lambda_) / (2 * Gu * Cd) * pressure_term * (P0 + 1) ** 0.5


def c_coefficient_simplified(Su, lambda_):
    """
    Simplified C-coefficient permitted when Pmax < 9 bar-g and stoichiometric
    fuel concentration ≤ ~10 vol%.

    Args:
        Su      (float): Fundamental burning velocity [m/s]
        lambda_ (float): Turbulent flame enhancement factor [-]

    Returns:
        float: C-coefficient [bar^0.5]

    Reference:
        NFPA 68 (2023), §7.2.1, Eq. 7.2.1.1
    """
    return 0.0223 * lambda_ * Su


# ──────────────────────────────────────────────────────────────────────────────
# §7.2.2 — Vent Area, High Pred (Pred > 0.5 bar-g)
# ──────────────────────────────────────────────────────────────────────────────

def delta_factor(Pstat, P0, Pmax, gamma_b):
    """
    Vent deployment factor delta for the high-Pred vent area equation.

    Args:
        Pstat   (float): Nominal vent deployment / burst pressure [bar-g]
        P0      (float): Enclosure pressure prior to ignition [bar-g]
        Pmax    (float): Maximum pressure in a contained deflagration [bar-g]
        gamma_b (float): Ratio of specific heats for burned gas-air mixture [-]

    Returns:
        float: Delta factor [-]

    Reference:
        NFPA 68 (2023), §7.2.2, Eq. 7.2.2b
    """
    numerator   = ((Pstat + 1) / (P0 + 1)) ** (1 / gamma_b) - 1
    denominator = ((Pmax  + 1) / (P0 + 1)) ** (1 / gamma_b) - 1
    return numerator / denominator


def vent_area_high_pred(As, Su, rho_u, lambda_, Gu, Cd, Pmax, Pred, gamma_b, delta):
    """
    Minimum vent area for high reduced pressure (Pred > 0.5 bar-g).

    Args:
        As      (float): Enclosure internal surface area [m²]
        Su      (float): Fundamental burning velocity [m/s]
        rho_u   (float): Mass density of unburned gas-air mixture [kg/m³]
        lambda_ (float): Turbulent flame enhancement factor [-]
        Gu      (float): Unburned gas-air sonic flow mass flux [kg/(m²·s)]
        Cd      (float): Vent flow discharge coefficient [-]
        Pmax    (float): Maximum pressure in a contained deflagration [bar-g]
        Pred    (float): Maximum pressure developed in a vented enclosure during a vented deflagration [bar-g]
        gamma_b (float): Ratio of specific heats for burned gas-air mixture [-]
        delta   (float): Vent deployment factor from delta_factor() [-]

    Returns:
        float: Minimum vent area Av0 [m²]

    Reference:
        NFPA 68 (2023), §7.2.2, Eq. 7.2.2a
    """
    R = (Pred + 1) / (Pmax + 1)
    R_exp = R ** (1 / gamma_b)
    pressure_factor = (1 - R_exp) / (R_exp - delta)
    return As * pressure_factor * (Su * rho_u * lambda_) / (Gu * Cd)


# ──────────────────────────────────────────────────────────────────────────────
# §7.2.6 — Turbulent Flame Enhancement Factor λ
# ──────────────────────────────────────────────────────────────────────────────

def reynolds_flame(rho_u, Su, Dhe, mu_u):
    """
    Flame Reynolds number Re_f.

    Args:
        rho_u (float): Mass density of unburned gas-air mixture [kg/m³]
        Su    (float): Fundamental burning velocity [m/s]
        Dhe   (float): Enclosure hydraulic equivalent diameter [m]
        mu_u  (float): Dynamic viscosity of unburned gas-air mixture [kg/(m·s)]

    Returns:
        float: Flame Reynolds number Re_f [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1b
    """
    return rho_u * Su * (Dhe / 2) / mu_u


def phi1_flame_reynolds(Re_f):
    """
    Flame Reynolds enhancement factor phi1.

    Args:
        Re_f (float): Flame Reynolds number [-]

    Returns:
        float: phi1 [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1a
    """
    if Re_f < 4000:
        return 1.0
    return (Re_f / 4000) ** _THETA


def max_vent_velocity(Pred, rho_u, a_u):
    """
    Maximum velocity through the vent opening.

    Args:
        Pred  (float): Maximum pressure in a vented enclosure [bar-g]
        rho_u (float): Mass density of unburned gas-air mixture [kg/m³]
        a_u   (float): Sound speed of unburned gas-air mixture [m/s]

    Returns:
        float: Maximum vent velocity u_v [m/s]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1e
    """
    return min(math.sqrt(2e5 * Pred / rho_u), a_u)


def reynolds_vent(rho_u, u_v, Dv, mu_u):
    """
    Vent flow Reynolds number Re_v.

    Args:
        rho_u (float): Mass density of unburned gas-air mixture [kg/m³]
        u_v   (float): Maximum velocity through the vent [m/s]
        Dv    (float): Vent diameter (iterative) [m]
        mu_u  (float): Dynamic viscosity of unburned gas-air mixture [kg/(m·s)]

    Returns:
        float: Vent Reynolds number Re_v [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1d
    """
    return rho_u * u_v * (Dv / 2) / mu_u


def phi2_vent_reynolds(Re_v, Su):
    """
    Vent Reynolds enhancement factor phi2.

    Args:
        Re_v (float): Vent flow Reynolds number [-]
        Su   (float): Fundamental burning velocity [m/s]

    Returns:
        float: phi2 [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1c
    """
    return max(1.0, _BETA1 * (Re_v / 1e6) ** ((_BETA2 / Su) ** 0.5))


def lambda_baseline(phi1, phi2):
    """
    Baseline turbulent flame enhancement factor lambda0, before obstruction
    and L/D corrections.

    Args:
        phi1 (float): Flame Reynolds enhancement factor [-]
        phi2 (float): Vent Reynolds enhancement factor [-]

    Returns:
        float: Baseline enhancement factor lambda0 [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1f
    """
    return phi1 * phi2


def lambda_obstruction(lambda0, Aobs, As):
    """
    Obstruction-adjusted turbulent flame enhancement factor lambda1.
    Only applied when Aobs > 0.2 * As; otherwise lambda1 = lambda0.

    Args:
        lambda0 (float): Baseline enhancement factor [-]
        Aobs    (float): Total external surface area of obstructions [m²]
        As      (float): Enclosure internal surface area [m²]

    Returns:
        float: Obstruction-adjusted enhancement factor lambda1 [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.4
    """
    if Aobs <= 0.2 * As:
        return lambda0
    return lambda0 * math.exp(math.sqrt(Aobs / As - 0.2))


def lambda_ld_correction(lambda1, LD):
    """
    L/D-corrected turbulent flame enhancement factor lambda.
    Only applied when 2.5 ≤ L/D ≤ 5 and Pred ≤ 2 bar-g; otherwise lambda = lambda1.

    Args:
        lambda1 (float): Obstruction-adjusted enhancement factor [-]
        LD      (float): Enclosure L/D ratio [-]

    Returns:
        float: L/D-corrected enhancement factor lambda [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.7
    """
    if LD < 2.5:
        return lambda1
    return lambda1 * (1 + (LD / 2.5 - 1) ** 2)


def lambda_enhanced(Su, rho_u, Dhe, mu_u, Pred, Av, Aobs, As, LD, a_u=A_U_DEFAULT):
    """
    Orchestrator: computes the final turbulent flame enhancement factor lambda
    by applying all sub-equations in sequence (§7.2.6.1a–f, §7.2.6.4, §7.2.6.7).

    Note:
        Pred is accepted in bar-g here and converted to Pa internally for u_v.

    Args:
        Su    (float): Fundamental burning velocity [m/s]
        rho_u (float): Mass density of unburned gas-air mixture [kg/m³]
        Dhe   (float): Enclosure hydraulic equivalent diameter [m]
        mu_u  (float): Dynamic viscosity of unburned gas-air mixture [kg/(m·s)]
        Pred  (float): Maximum pressure in a vented enclosure [bar-g]
        Av    (float): Current vent area estimate used to derive Dv [m²]
        Aobs  (float): Total external surface area of obstructions [m²]
        As    (float): Enclosure internal surface area [m²]
        LD    (float): Enclosure L/D ratio [-]
        a_u   (float): Sound speed of unburned gas-air mixture [m/s]

    Returns:
        float: Final turbulent flame enhancement factor lambda [-]

    Reference:
        NFPA 68 (2023), §7.2.6, Eq. 7.2.6.1a–f, 7.2.6.4, 7.2.6.7
    """
    Dv    = math.sqrt(4 * Av / math.pi)
    Re_f  = reynolds_flame(rho_u, Su, Dhe, mu_u)
    phi1  = phi1_flame_reynolds(Re_f)
    u_v   = max_vent_velocity(Pred, rho_u, a_u)  # convert bar-g → Pa
    Re_v  = reynolds_vent(rho_u, u_v, Dv, mu_u)
    phi2  = phi2_vent_reynolds(Re_v, Su)
    lam0  = lambda_baseline(phi1, phi2)
    lam1  = lambda_obstruction(lam0, Aobs, As)
    return  lambda_ld_correction(lam1, LD)


# ──────────────────────────────────────────────────────────────────────────────
# §7.3 — Partial Volume Effects
# ──────────────────────────────────────────────────────────────────────────────

def partial_volume_fraction(Vgas, Venc, Vsolid, x_st):
    """
    Partial volume fill fraction Xr.

    Args:
        Vgas   (float): Maximum volume of gas that can be mixed with air [m³]
        Venc   (float): Enclosure volume [m³]
        Vsolid (float): Volume of solid objects in the enclosure [m³]
        x_st   (float): Stoichiometric volume concentration of gas [-]

    Returns:
        float: Fill fraction Xr [-]

    Reference:
        NFPA 68 (2023), §7.3, Eq. 7.3.2
    """
    return (Vgas / (Venc - Vsolid)) / x_st


def vent_area_partial_volume(Av0, Xr, Pred, Pmax):
    """
    Vent area adjusted for partial volume fill. Only applied when Xr < 1;
    otherwise Av1 = Av0.

    Args:
        Av0  (float): Full-volume vent area from §7.2.1 or §7.2.2 [m²]
        Xr   (float): Partial volume fill fraction [-]
        Pred (float): Maximum pressure developed in a vented enclosure during a vented deflagration [bar-g]
        Pmax (float): Maximum pressure in a contained deflagration [bar-g]

    Returns:
        float: Partial-volume-adjusted vent area Av1 [m²]

    Reference:
        NFPA 68 (2023), §7.3, Eq. 7.3.3
    """
    if Xr >= 1:
        return Av0
    Pi = Pred / Pmax
    return Av0 * Xr ** (-1/3) * math.sqrt((Xr - Pi) / (1 - Pi))


# ──────────────────────────────────────────────────────────────────────────────
# §7.4 — Effects of Panel Inertia
# ──────────────────────────────────────────────────────────────────────────────

def panel_mass_threshold(Pred, n, V, Su, lambda_):
    """
    Threshold panel areal mass MT below which no inertia correction is needed.

    Args:
        Pred    (float): Maximum pressure developed in a vented enclosure during a vented deflagration [bar-g]
        n       (int):   Number of vent panels [-]
        V       (float): Enclosure volume [m³] (must be > 1 m³)
        Su      (float): Fundamental burning velocity [m/s]
        lambda_ (float): Turbulent flame enhancement factor [-]

    Returns:
        float: Threshold panel areal mass MT [kg/m²]

    Reference:
        NFPA 68 (2023), §7.4, Eq. 7.4.2
    """
    return (Pred**0.2 * n**0.3 * V / (Su * lambda_)**0.5) ** 1.67


def vent_area_panel_inertia(Av1, M, MT, Su, lambda_, n, V, Pred, Fsh):
    """
    Vent area adjusted for panel inertia. Only applied when M > MT;
    otherwise Av2 = Av1.

    Args:
        Av1     (float): Vent area from §7.3 [m²]
        M       (float): Actual vent panel areal mass [kg/m²] (must be ≤ 40 kg/m²)
        MT      (float): Threshold panel areal mass from panel_mass_threshold() [kg/m²]
        Su      (float): Fundamental burning velocity [m/s]
        lambda_ (float): Turbulent flame enhancement factor [-]
        n       (int):   Number of vent panels [-]
        V       (float): Enclosure volume [m³]
        Pred    (float): Maximum pressure developed in a vented enclosure during a vented deflagration [bar-g]
        Fsh     (float): Shape factor — 1.0 for translating panels, 1.1 for hinged [-]

    Returns:
        float: Panel-inertia-adjusted vent area Av2 [m²]

    Reference:
        NFPA 68 (2023), §7.4, Eq. 7.4.3
    """
    if M <= MT:
        return Av1
    inertia_factor = 1 + (0.05 * M**0.6 * (Su * lambda_)**0.5) / (n**0.3 * V * Pred**0.2)
    return Av1 * Fsh * inertia_factor


# ──────────────────────────────────────────────────────────────────────────────
# §7.5 — Effects of Vent Ducts
# ──────────────────────────────────────────────────────────────────────────────

def pred_duct_short(Pred):
    """
    Reduced effective Pred accounting for a short vent duct (Curve A).
    Use when duct length < 3 m AND < 4 hydraulic diameters.
    Ducts shorter than 3 m are treated as 3 m per §7.5.3.

    Args:
        Pred (float): Target maximum reduced pressure without duct [bar]

    Returns:
        float: Effective reduced pressure with duct P'red [bar]

    Reference:
        NFPA 68 (2023), §7.5, Eq. 7.5.2.1
    """
    return 0.779 * Pred ** 1.161


def pred_duct_long(Pred):
    """
    Reduced effective Pred accounting for a longer vent duct (Curve B).
    Use when duct length is 3–6 m OR ≥ 4 hydraulic diameters.
    Not valid for duct lengths exceeding 6 m.

    Args:
        Pred (float): Target maximum reduced pressure without duct [bar]

    Returns:
        float: Effective reduced pressure with duct P'red [bar]

    Reference:
        NFPA 68 (2023), §7.5, Eq. 7.5.2.2
    """
    return 0.172 * Pred ** 1.936