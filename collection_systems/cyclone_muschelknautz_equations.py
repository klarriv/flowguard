import math

# ──────────────────────────────────────────────────────────────────────────────
# Hoffmann & Stein, "Gas Cyclones and Swirl Tubes" (2nd ed.) — Chapter 6
# The Muschelknautz Method of Modeling (MM)
# ──────────────────────────────────────────────────────────────────────────────
# Scope: raw equations only, one function per numbered equation, SI units
#        throughout (m, s, kg, Pa). Page numbers are the printed page numbers
#        of the 2nd edition. The method is the conventional slot-type inlet,
#        conical-bodied cyclone of §6.1-§6.6; the cylindrical-body friction
#        factors (Eq. 6.1.10), the x_fact cut-size correction of Eq. 6.2.3 and
#        the inner-feed model of Appendix 6.B are not implemented.
#
# Symbols (Figs. 6.1.1, 6.1.2): R body radius, Rx vortex finder radius,
#        Rd dust outlet radius, Rin radial position of the inlet centre,
#        H total height, Hc cone height, S vortex finder length, Q gas flow,
#        co inlet solids loading [kg solids / kg gas].

G = 9.81  # gravitational acceleration [m/s²] as used for Frx in Eq. 6.1.12


# ──────────────────────────────────────────────────────────────────────────────
# §6.1 — Basis of the Model
# ──────────────────────────────────────────────────────────────────────────────

def constriction_coefficient(xi, co):
    """
    Inlet constriction coefficient α for a conventional slot-type inlet.

    Args:
        xi (float): Inlet width ratio ξ = b/R [-]
        co (float): Inlet solids loading co [kg/kg]

    Returns:
        float: Constriction coefficient α [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.1, p. 112
    """
    inner = 1.0 - (1.0 - xi ** 2) * (2.0 * xi - xi ** 2) / (1.0 + co)
    return (1.0 / xi) * (
        1.0 - math.sqrt(1.0 + 4.0 * ((xi / 2.0) ** 2 - xi / 2.0) * math.sqrt(inner))
    )


def inlet_velocity(Q, a, b):
    """
    Mean gas velocity in the rectangular inlet.

    Args:
        Q (float): Gas volumetric flow rate [m³/s]
        a (float): Inlet height [m]
        b (float): Inlet width [m]

    Returns:
        float: Inlet velocity vin [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.1.3, p. 113
    """
    return Q / (a * b)


def wall_tangential_velocity(vin, Rin, alpha, R):
    """
    Tangential gas velocity at the cyclone wall.

    Args:
        vin   (float): Inlet velocity [m/s]
        Rin   (float): Radial position of the inlet centre [m]
        alpha (float): Constriction coefficient α [-]
        R     (float): Body radius [m]

    Returns:
        float: Wall tangential velocity vθw [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.1.2, p. 113
    """
    return vin * Rin / (alpha * R)


def geometric_mean_radius(Rx, R):
    """
    Geometric mean of the vortex finder and body radii.

    Args:
        Rx (float): Vortex finder radius [m]
        R  (float): Body radius [m]

    Returns:
        float: Geometric mean radius Rm [m]

    Reference:
        Hoffmann & Stein, Eq. 6.1.4, p. 113
    """
    return math.sqrt(Rx * R)


def wall_axial_velocity(Q, R, Rm):
    """
    Axial gas velocity at the wall; 10 % of Q is assumed to short-circuit
    along the roof and vortex finder.

    Args:
        Q  (float): Gas volumetric flow rate [m³/s]
        R  (float): Body radius [m]
        Rm (float): Geometric mean radius [m]

    Returns:
        float: Wall axial velocity vzw [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.1.5, p. 113
    """
    return 0.9 * Q / (math.pi * (R ** 2 - Rm ** 2))


def body_reynolds_number(Rin, Rm, vz_w, rho, H, mu, v_theta_m):
    """
    Cyclone body Reynolds number.

    Args:
        Rin       (float): Radial position of the inlet centre [m]
        Rm        (float): Geometric mean radius [m]
        vz_w      (float): Wall axial velocity vzw [m/s]
        rho       (float): Gas density [kg/m³]
        H         (float): Total cyclone height [m]
        mu        (float): Gas dynamic viscosity [Pa·s]
        v_theta_m (float): Geometric mean rotational velocity vθm [m/s]

    Returns:
        float: Body Reynolds number ReR [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.6, p. 114
    """
    return Rin * Rm * vz_w * rho / (H * mu * (1.0 + (vz_w / v_theta_m) ** 2))


def mean_rotational_velocity(v_theta_w, v_theta_cs):
    """
    Geometric mean of the wall and inner-core tangential velocities.

    Args:
        v_theta_w  (float): Wall tangential velocity vθw [m/s]
        v_theta_cs (float): Inner-core tangential velocity vθCS [m/s]

    Returns:
        float: Mean rotational velocity vθm [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.1.7, p. 114
    """
    return math.sqrt(v_theta_w * v_theta_cs)


def smooth_wall_friction_conical(ReR):
    """
    Smooth-wall component of the gas friction factor, conical body.

    Args:
        ReR (float): Body Reynolds number [-]

    Returns:
        float: fsm [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.9 (first line), p. 116
    """
    return 0.323 * ReR ** -0.623


def roughness_friction_conical(ReR, ks_over_R):
    """
    Wall-roughness component of the gas friction factor, conical body.

    The relative roughness must not be below the smooth-wall limit of
    6×10⁻⁴ (p. 115 and p. 117); the caller is responsible for clamping.

    Args:
        ReR       (float): Body Reynolds number [-]
        ks_over_R (float): Relative wall roughness ks/R [-]

    Returns:
        float: fr [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.9 (second line), p. 116
    """
    d = ks_over_R - 0.000599
    return (
        math.log10((1.60 / d) ** 2.38) ** -2
        * (1.0 + 2.25e5 / (ReR ** 2 * d ** 0.213)) ** -1
    )


def gas_friction_factor(f_sm, f_r):
    """
    Gas-phase wall friction factor, sum of smooth-wall and roughness terms.

    Args:
        f_sm (float): Smooth-wall component [-]
        f_r  (float): Roughness component [-]

    Returns:
        float: fair [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.8, p. 116
    """
    return f_sm + f_r


def total_friction_factor(f_air, R, Rx, eta, co, Fr_x, rho, rho_str):
    """
    Total friction factor including the drag of the moving solids strand.

    Args:
        f_air  (float): Gas friction factor [-]
        R      (float): Body radius [m]
        Rx     (float): Vortex finder radius [m]
        eta    (float): Overall collection efficiency (guess/iterate) [-]
        co     (float): Inlet solids loading [kg/kg]
        Fr_x   (float): Froude number of the vortex finder flow [-]
        rho    (float): Gas density [kg/m³]
        rho_str (float): Density of the wall strand of solids [kg/m³]

    Returns:
        float: Total friction factor f [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.11, p. 117
    """
    return f_air + 0.25 * (R / Rx) ** -0.625 * math.sqrt(
        eta * co * Fr_x * rho / rho_str
    )


def strand_density(rho_bulk, fraction=0.4):
    """
    Density of the solids strand at the wall, 0.3-0.5 × bulk density
    (0.4 recommended "lacking better information").

    Args:
        rho_bulk (float): Bulk density of the solids at rest [kg/m³]
        fraction (float): Fraction of bulk density [-], default 0.4

    Returns:
        float: ρstr [kg/m³]

    Reference:
        Hoffmann & Stein, text following Eq. 6.1.11, p. 118
    """
    return fraction * rho_bulk


def froude_number_vortex_finder(vx, Rx):
    """
    Froude number of the flow out of the vortex tube.

    Args:
        vx (float): Superficial axial velocity in the vortex finder [m/s]
        Rx (float): Vortex finder radius [m]

    Returns:
        float: Frx [-]

    Reference:
        Hoffmann & Stein, Eq. 6.1.12, p. 118
    """
    return vx / math.sqrt(2.0 * Rx * G)


# ──────────────────────────────────────────────────────────────────────────────
# §6.2 — Computation of the Inner Vortex Cut-Point, x50
# ──────────────────────────────────────────────────────────────────────────────

def inner_core_tangential_velocity(v_theta_w, R, Rx, f, A_R, Q):
    """
    Tangential gas velocity at the inner-core radius RCS (= Rx).

    Args:
        v_theta_w (float): Wall tangential velocity vθw [m/s]
        R         (float): Body radius [m]
        Rx        (float): Vortex finder radius [m]
        f         (float): Total friction factor [-]
        A_R       (float): Total inside area AR [m²]
        Q         (float): Gas volumetric flow rate [m³/s]

    Returns:
        float: vθCS [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.2.1, p. 118
    """
    return v_theta_w * (R / Rx) / (
        1.0 + f * A_R * v_theta_w * math.sqrt(R / Rx) / (2.0 * Q)
    )


def total_inside_area(R, Rx, Rd, H, Hc, S):
    """
    Inside area of the cyclone contributing to frictional drag: roof, barrel,
    cone and the external surface of the vortex tube.

    Args:
        R  (float): Body radius [m]
        Rx (float): Vortex finder radius [m]
        Rd (float): Dust outlet radius [m]
        H  (float): Total height [m]
        Hc (float): Cone height [m]
        S  (float): Vortex finder length [m]

    Returns:
        float: AR [m²]

    Reference:
        Hoffmann & Stein, Eq. 6.2.2, p. 119
    """
    return math.pi * (
        R ** 2
        - Rx ** 2
        + 2.0 * R * (H - Hc)
        + (R + Rd) * math.sqrt(Hc ** 2 + (R - Rd) ** 2)
        + 2.0 * Rx * S
    )


def control_surface_height(H, S, Hc, Rx, Rd, R):
    """
    Height HCS of the control cylinder CS (width Dx) below the vortex finder.
    Helper, not a numbered Chapter 6 equation: H − S when the dust outlet is
    at least as wide as the vortex finder, shorter when Rd < Rx because the
    cylinder then ends where the cone radius equals Rx.

    Args:
        H  (float): Total height [m]
        S  (float): Vortex finder length [m]
        Hc (float): Cone height [m]
        Rx (float): Vortex finder radius [m]
        Rd (float): Dust outlet radius [m]
        R  (float): Body radius [m]

    Returns:
        float: HCS [m]

    Reference:
        Hoffmann & Stein, definition of HCS in Ch. 4, p. 65 (Eq. 4.2.1);
        general form in the Ch. 5 worked example, p. 104. Used in Eq. 6.2.5.
    """
    if Rd >= Rx:
        return H - S
    return (H - S) - Hc * (Rx - Rd) / (R - Rd)


def cut_size_stokes(mu, Q, rho_p, rho, v_theta_cs, H, S):
    """
    Cut size x50 of the inner vortex, Stokes regime.

    Args:
        mu         (float): Gas dynamic viscosity [Pa·s]
        Q          (float): Gas volumetric flow rate [m³/s]
        rho_p      (float): Particle density [kg/m³]
        rho        (float): Gas density [kg/m³]
        v_theta_cs (float): Inner-core tangential velocity [m/s]
        H          (float): Total height [m]
        S          (float): Vortex finder length [m]

    Returns:
        float: x50 [m]

    Reference:
        Hoffmann & Stein, Eq. 6.2.3 with x_fact = 1, p. 119
    """
    return math.sqrt(
        18.0 * mu * (0.9 * Q) / (2.0 * math.pi * (rho_p - rho) * v_theta_cs ** 2 * (H - S))
    )


def particle_reynolds_number(rho, U_t50, x50, mu):
    """
    Reynolds number of the cut-sized particle.

    Args:
        rho   (float): Gas density [kg/m³]
        U_t50 (float): Terminal (radial) velocity of the cut-sized particle [m/s]
        x50   (float): Cut size [m]
        mu    (float): Gas dynamic viscosity [Pa·s]

    Returns:
        float: Rep [-]

    Reference:
        Hoffmann & Stein, Eq. 6.2.4, p. 120
    """
    return rho * U_t50 * x50 / mu


def cut_point_terminal_velocity(Q, Rx, H_CS):
    """
    Radial velocity at the control surface = terminal velocity of the
    cut-sized particle.

    Args:
        Q    (float): Gas volumetric flow rate [m³/s]
        Rx   (float): Vortex finder radius [m]
        H_CS (float): Control cylinder height [m]

    Returns:
        float: U't50 = vrCS [m/s]

    Reference:
        Hoffmann & Stein, Eq. 6.2.5, p. 120
    """
    return Q / (2.0 * math.pi * Rx * H_CS)


def cut_size_non_stokes(mu, rho, U_t50, rho_p, v_theta_cs, Rx):
    """
    Cut size x50 outside the Stokes regime (Rep > ~0.5; drag coefficient
    CD = 18.5/Rep^0.6 per Eq. 6.2.7, valid for 0.3 < Rep < 1000).

    Args:
        mu         (float): Gas dynamic viscosity [Pa·s]
        rho        (float): Gas density [kg/m³]
        U_t50      (float): Terminal velocity of the cut-sized particle [m/s]
        rho_p      (float): Particle density [kg/m³]
        v_theta_cs (float): Inner-core tangential velocity [m/s]
        Rx         (float): Vortex finder radius [m]

    Returns:
        float: x50 [m]

    Reference:
        Hoffmann & Stein, Eq. 6.2.6, p. 120
    """
    return 5.18 * (mu ** 0.375 * rho ** 0.25 * U_t50 ** 0.875) / (
        (rho_p - rho) * v_theta_cs ** 2 / Rx
    ) ** 0.625


# ──────────────────────────────────────────────────────────────────────────────
# §6.3 — Efficiency at Low Solids Loadings
# ──────────────────────────────────────────────────────────────────────────────

def grade_efficiency(x, x50, m):
    """
    Grade-efficiency (classification) curve value for particle size x.

    Args:
        x   (float): Particle size [m, same unit as x50]
        x50 (float): Cut size [m]
        m   (float): Slope of the grade-efficiency curve [-] (book range 2-7,
                     typical 3, p. 121)

    Returns:
        float: ηi [-]

    Reference:
        Hoffmann & Stein, Eq. 6.3.2, p. 120
    """
    return 1.0 / (1.0 + (x50 / x) ** m)


def overall_efficiency_classification(eta_i, delta_mf):
    """
    Overall efficiency from classification only (co < coL): mass-weighted sum
    of the grade efficiencies of N size fractions.

    Args:
        eta_i    (sequence of float): Grade efficiency of each fraction [-]
        delta_mf (sequence of float): Mass fraction of each fraction [-]

    Returns:
        float: η [-]

    Reference:
        Hoffmann & Stein, Eq. 6.3.3, p. 121
    """
    return sum(e * w for e, w in zip(eta_i, delta_mf))


# ──────────────────────────────────────────────────────────────────────────────
# §6.4 — Mass-Loading (Saltation) Effect
# ──────────────────────────────────────────────────────────────────────────────

def limit_loading_exponent(co):
    """
    Exponent k of the limit-loading correlation for co < 0.1.

    Args:
        co (float): Inlet solids loading [kg/kg]

    Returns:
        float: k [-]

    Reference:
        Hoffmann & Stein, Eq. 6.4.3, p. 122
    """
    return -0.11 - 0.10 * math.log(co)


def limit_loading(x50, x_med, co):
    """
    Limit loading coL: the solids loading the gas can carry in turbulent
    suspension on entering the cyclone. Uses Eq. 6.4.1 for co >= 0.1 and
    Eq. 6.4.2 (with k from Eq. 6.4.3) for co < 0.1.

    Args:
        x50   (float): Cut size [m]
        x_med (float): Mass median size of the feed [m, same unit as x50]
        co    (float): Inlet solids loading [kg/kg]

    Returns:
        float: coL [kg/kg]

    Reference:
        Hoffmann & Stein, Eqs. 6.4.1-6.4.3, p. 122
    """
    if co >= 0.1:
        return 0.025 * (x50 / x_med) * (10.0 * co) ** 0.15
    return 0.025 * (x50 / x_med) * (10.0 * co) ** limit_loading_exponent(co)


# ──────────────────────────────────────────────────────────────────────────────
# §6.5 — Overall Efficiency when co > coL
# ──────────────────────────────────────────────────────────────────────────────

def overall_efficiency_saltation(co, co_L, classification_efficiency):
    """
    Overall efficiency when saltation occurs: mass loading in the inlet plus
    classification of the remainder in the inner vortex.

    Args:
        co                        (float): Inlet solids loading [kg/kg]
        co_L                      (float): Limit loading [kg/kg]
        classification_efficiency (float): Σ ηi·ΔMFi from Eq. 6.3.3 [-]

    Returns:
        float: η [-]

    Reference:
        Hoffmann & Stein, Eq. 6.5.1, p. 123
    """
    return (1.0 - co_L / co) + (co_L / co) * classification_efficiency


# ──────────────────────────────────────────────────────────────────────────────
# §6.6 — Pressure Drop
# ──────────────────────────────────────────────────────────────────────────────

def pressure_drop_body(f, A_R, rho, v_theta_w, v_theta_cs, Q):
    """
    Wall friction loss in the cyclone body.

    Args:
        f          (float): Total friction factor [-]
        A_R        (float): Total inside area [m²]
        rho        (float): Gas density [kg/m³]
        v_theta_w  (float): Wall tangential velocity [m/s]
        v_theta_cs (float): Inner-core tangential velocity [m/s]
        Q          (float): Gas volumetric flow rate [m³/s]

    Returns:
        float: Δpbody [Pa]

    Reference:
        Hoffmann & Stein, Eq. 6.6.1, p. 124
    """
    return f * A_R * rho * (v_theta_w * v_theta_cs) ** 1.5 / (2.0 * 0.9 * Q)


def pressure_drop_core(v_theta_cs, vx, rho):
    """
    Loss in the vortex core and vortex finder.

    Args:
        v_theta_cs (float): Inner-core tangential velocity [m/s]
        vx         (float): Axial velocity in the vortex finder [m/s]
        rho        (float): Gas density [kg/m³]

    Returns:
        float: Δpx [Pa]

    Reference:
        Hoffmann & Stein, Eq. 6.6.2, p. 124
    """
    r = v_theta_cs / vx
    return (2.0 + r ** 2 + 3.0 * r ** (4.0 / 3.0)) * 0.5 * rho * vx ** 2


def pressure_drop_acceleration(co, rho, v2, v1):
    """
    Acceleration loss of the gas-solids mixture from upstream velocity v1 to
    the cyclone inlet velocity v2 (no slip between solids and gas).

    Args:
        co  (float): Inlet solids loading [kg/kg]
        rho (float): Gas density [kg/m³]
        v2  (float): Downstream (cyclone inlet) velocity [m/s]
        v1  (float): Upstream velocity [m/s]

    Returns:
        float: Δpacc [Pa]

    Reference:
        Hoffmann & Stein, Eq. 6.6.3, p. 125
    """
    return (1.0 + co) * rho * (v2 ** 2 - v1 ** 2) / 2.0


def pressure_drop_total(dp_body, dp_core, dp_acc=0.0):
    """
    Total pressure loss from inlet to gas outlet.

    Args:
        dp_body (float): Body wall loss [Pa]
        dp_core (float): Core and vortex finder loss [Pa]
        dp_acc  (float): Inlet acceleration loss [Pa], 0 if none

    Returns:
        float: Δp [Pa]

    Reference:
        Hoffmann & Stein, Eq. 6.6.4, p. 125
    """
    return dp_body + dp_core + dp_acc
