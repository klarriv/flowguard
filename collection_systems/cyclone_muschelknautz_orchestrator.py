"""Muschelknautz Method of Modeling (MM) — cyclone performance orchestrator.

Sequences the equations of ``cyclone_muschelknautz_equations`` (Hoffmann &
Stein, "Gas Cyclones and Swirl Tubes", 2nd ed., Ch. 6) into the full
calculation: swirl velocities and friction → inner-vortex cut size x50 →
limit loading → grade efficiency and overall efficiency → pressure drop →
emission.

Scope: conventional slot-type inlet only (Rin = R − b/2, α from Eq. 6.1.1),
conical-bodied cyclone. SI units throughout, except particle sizes of the
feed distribution, which are in µm (arguments named ``*_um``).

Public entry point: ``cyclone_performance()``.
"""
import math
from dataclasses import dataclass, field

from collection_systems import cyclone_muschelknautz_equations as eq

# Smooth-wall limit of the relative roughness ks/R (H&S p. 115 and p. 117).
KS_OVER_R_MIN = 6e-4
# Rep above which the Stokes form of x50 (Eq. 6.2.3) is not used (p. 120).
STOKES_REP_LIMIT = 0.5
# Validity range of the drag correlation behind Eq. 6.2.6 (Eq. 6.2.7).
NON_STOKES_REP_RANGE = (0.3, 1000.0)
# Tolerance when a PSD's cumulative fraction at the largest size is not 1.
PSD_NORMALISE_TOL = 1e-3
# Fraction of mass outside the measured range above which a warning is raised.
PSD_EXTRAPOLATION_WARN = 0.05
_MAX_ITER = 500
_CONV_TOL = 1e-10


# ──────────────────────────────────────────────────────────────────────────────
# Inputs
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CycloneGeometry:
    """Cylinder-on-cone cyclone with a conventional slot-type inlet [m].

    Attributes:
        D  : body diameter
        a  : inlet height
        b  : inlet width
        Dx : vortex finder diameter
        S  : vortex finder length (below the roof)
        H  : total height (roof to dust outlet)
        Hc : cone height (so the barrel is H − Hc)
        Dd : dust outlet diameter
    """
    D: float
    a: float
    b: float
    Dx: float
    S: float
    H: float
    Hc: float
    Dd: float

    def __post_init__(self):
        for name in ("D", "a", "b", "Dx", "S", "H", "Hc", "Dd"):
            if not getattr(self, name) > 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")
        if self.Dx >= self.D:
            raise ValueError("Vortex finder diameter Dx must be smaller than body diameter D")
        if self.Dd >= self.D:
            raise ValueError("Dust outlet diameter Dd must be smaller than body diameter D")
        if self.b >= self.D / 2:
            raise ValueError("Inlet width b must be smaller than the body radius D/2")
        if self.S >= self.H:
            raise ValueError("Vortex finder length S must be smaller than total height H")
        if self.Hc > self.H:
            raise ValueError("Cone height Hc cannot exceed total height H")

    @property
    def R(self):
        return self.D / 2

    @property
    def Rx(self):
        return self.Dx / 2

    @property
    def Rd(self):
        return self.Dd / 2


@dataclass(frozen=True)
class GasProperties:
    """Carrier gas: density [kg/m³], dynamic viscosity [Pa·s], flow [m³/s]."""
    density: float
    viscosity: float
    flow_rate: float

    def __post_init__(self):
        for name in ("density", "viscosity", "flow_rate"):
            if not getattr(self, name) > 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")


@dataclass(frozen=True)
class SolidProperties:
    """Dust: particle density, bulk density at rest [kg/m³], inlet dust
    loading [kg solids / m³ gas] and wall roughness ks [m] (0.046 mm for
    commercial steel, H&S p. 115)."""
    particle_density: float
    bulk_density: float
    dust_loading: float
    wall_roughness: float = 0.046e-3

    def __post_init__(self):
        for name in ("particle_density", "bulk_density", "dust_loading", "wall_roughness"):
            if not getattr(self, name) > 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")


# ──────────────────────────────────────────────────────────────────────────────
# Feed particle size distribution
# ──────────────────────────────────────────────────────────────────────────────

def _softplus(t):
    return max(t, 0.0) + math.log1p(math.exp(-abs(t)))


@dataclass(frozen=True)
class ParticleSizeDistribution:
    """Feed particle size distribution held as a cumulative undersize curve
    F(x) at a set of knots; any number of points (≥ 1) is accepted.

    Build one with ``from_cumulative`` (laser-diffraction cumulative output or
    the book's own format), ``from_bins`` (laser-diffraction channels) or
    ``from_sieve`` (Tyler or any sieve stack).

    Efficiency integral
    -------------------
    F is interpolated linearly in ln(x) between knots, i.e. mass is spread
    uniformly in log-size within each interval. With the grade efficiency of
    Eq. 6.3.2, η(x) = 1/(1 + (x50/x)^m), the interval mean has the closed form
    ∫η dln x = (1/m)·ln(1 + (x/x50)^m), so each interval is integrated
    exactly: no representative size per bin has to be chosen and the result
    does not depend on how finely the same distribution is binned.

    Treatment outside the measured range
    ------------------------------------
    Below the smallest size, if F(xmin) > 0: the mass is spread log-uniformly
    over one extra interval with the same log-width as the first measured
    interval (bounded extrapolation, no mass at 0 µm). Example: knots 2, 4 µm
    with F = 0.1, 0.5 put 0.1 of the mass uniformly in ln x between 1 and
    2 µm. The affected fraction is ``extrapolated_mass_fraction``; a warning
    is added when it exceeds 5 %.

    Above the largest size, if F(xmax) < 1 − 1e-3: the remaining mass is a
    point mass at xmax, where η(xmax) is a lower bound for larger particles
    (conservative for emissions). Example: F(xmax) = 0.98 gives 2 % of the
    feed at xmax. For a sieve stack, the mass retained on the coarsest screen
    is treated this way.

    F(xmax) within 1e-3 of 1 is renormalised (sum to exactly 1); F(xmax) above
    1 + 1e-3 is an error.

    A single point is a monodisperse feed: all mass at that size.

    The median is found by the same interpolation (``median_um``).
    """
    sizes_um: tuple
    cumulative: tuple

    def __post_init__(self):
        sizes, cum = tuple(self.sizes_um), tuple(self.cumulative)
        if len(sizes) != len(cum):
            raise ValueError("sizes and cumulative fractions must have the same length")
        if len(sizes) == 0:
            raise ValueError("particle size distribution needs at least one point")
        if any(x <= 0 for x in sizes):
            raise ValueError("particle sizes must be positive")
        if any(b <= a for a, b in zip(sizes, sizes[1:])):
            raise ValueError("particle sizes must be strictly increasing (no duplicates)")
        if any(c < 0 for c in cum):
            raise ValueError("cumulative fractions must not be negative")
        if any(b < a - 1e-12 for a, b in zip(cum, cum[1:])):
            raise ValueError("cumulative fractions must be non-decreasing with size")
        if len(sizes) > 1 and cum[-1] > 1.0 + PSD_NORMALISE_TOL:
            raise ValueError(f"cumulative fraction at the largest size is {cum[-1]:.4f} > 1")
        if len(sizes) > 1 and cum[-1] <= 0:
            raise ValueError("distribution carries no mass")
        object.__setattr__(self, "sizes_um", sizes)
        object.__setattr__(self, "cumulative", cum)

    # ── constructors ─────────────────────────────────────────────────────────

    @classmethod
    def from_cumulative(cls, sizes_um, cumulative_undersize):
        """Cumulative undersize fractions (0-1) at the given sizes [µm].
        Points may be given in any order."""
        if len(sizes_um) != len(cumulative_undersize):
            raise ValueError("sizes and cumulative fractions must have the same length")
        pairs = sorted(zip(sizes_um, cumulative_undersize))
        return cls(tuple(p[0] for p in pairs), tuple(p[1] for p in pairs))

    @classmethod
    def from_bins(cls, lower_um, upper_um, mass_fraction):
        """Laser-diffraction channels: mass fraction (0-1) in each bin
        [lower, upper]. Bins must be contiguous; cover a gap with an explicit
        zero-mass bin."""
        if not len(lower_um) == len(upper_um) == len(mass_fraction):
            raise ValueError("bin edges and mass fractions must have the same length")
        rows = sorted(zip(lower_um, upper_um, mass_fraction))
        if not rows:
            raise ValueError("no bins given")
        for lo, hi, w in rows:
            if not hi > lo:
                raise ValueError(f"bin upper edge {hi} must exceed lower edge {lo}")
            if w < 0:
                raise ValueError("bin mass fractions must not be negative")
        for (_, hi, _), (lo2, _, _) in zip(rows, rows[1:]):
            if not math.isclose(hi, lo2, rel_tol=1e-6):
                raise ValueError(
                    f"bins are not contiguous ({hi} to {lo2} µm); add a zero-mass bin"
                )
        sizes = [rows[0][0]] + [r[1] for r in rows]
        cum, total = [0.0], 0.0
        for _, _, w in rows:
            total += w
            cum.append(total)
        return cls(tuple(sizes), tuple(cum))

    @classmethod
    def from_sieve(cls, apertures_um, retained_fraction, pan_fraction=0.0):
        """Sieve stack: mass fraction (0-1) retained on each screen and in the
        pan. Mass retained on a screen passed the next larger aperture, so it
        lies between the two apertures; mass retained on the coarsest screen
        lies above it. Retained fractions plus pan must sum to 1 (±1e-3)."""
        if len(apertures_um) != len(retained_fraction):
            raise ValueError("apertures and retained fractions must have the same length")
        rows = sorted(zip(apertures_um, retained_fraction))
        if len(rows) < 2:
            raise ValueError("a sieve stack needs at least two screens")
        if pan_fraction < 0 or any(r < 0 for _, r in rows):
            raise ValueError("retained fractions must not be negative")
        total = pan_fraction + sum(r for _, r in rows)
        if abs(total - 1.0) > PSD_NORMALISE_TOL:
            raise ValueError(f"retained fractions plus pan sum to {total:.4f}, expected 1")
        sizes, cum, running = [], [], pan_fraction
        for aperture, retained in rows:
            sizes.append(aperture)
            cum.append(running)
            running += retained
        return cls(tuple(sizes), tuple(cum))

    # ── analysis ─────────────────────────────────────────────────────────────

    def _masses(self):
        """Return (intervals, notes, extrapolated_fraction) where intervals is
        a list of (lo_um, hi_um, mass); lo == hi means a point mass."""
        sizes, cum = self.sizes_um, self.cumulative
        notes = []
        if len(sizes) == 1:
            notes.append(
                f"Single point: monodisperse feed of 100 % at {sizes[0]:g} µm."
            )
            return [(sizes[0], sizes[0], 1.0)], notes, 0.0

        top = cum[-1]
        scale = 1.0
        if abs(1.0 - top) <= PSD_NORMALISE_TOL:
            scale = 1.0 / top
            if top != 1.0:
                notes.append(
                    f"Cumulative fraction at {sizes[-1]:g} µm is {top:.4f}; renormalised to 1."
                )
        cum = [c * scale for c in cum]

        intervals = []
        extrapolated = cum[0]
        if cum[0] > 0:
            width = math.log(sizes[1] / sizes[0])
            lo = sizes[0] * math.exp(-width)
            intervals.append((lo, sizes[0], cum[0]))
            pct = 100.0 * cum[0]
            notes.append(
                f"{pct:.1f} % of the mass lies below the smallest size of {sizes[0]:g} µm "
                f"and was spread log-uniformly over {sizes[0]:g} to {lo:.3g} µm."
            )
            if cum[0] > PSD_EXTRAPOLATION_WARN:
                notes.append(
                    f"Warning: more than {PSD_EXTRAPOLATION_WARN:.0%} of the feed is below the "
                    "measured range; the efficiency depends on this extrapolation."
                )
        for lo, hi, c0, c1 in zip(sizes, sizes[1:], cum, cum[1:]):
            if c1 > c0:
                intervals.append((lo, hi, c1 - c0))
        if cum[-1] < 1.0:
            rest = 1.0 - cum[-1]
            intervals.append((sizes[-1], sizes[-1], rest))
            notes.append(
                f"{100.0 * rest:.1f} % of the mass lies above the largest size of "
                f"{sizes[-1]:g} µm and was treated as a point mass at {sizes[-1]:g} µm."
            )
        return intervals, notes, extrapolated

    @property
    def notes(self):
        """Plain-language statements of the out-of-range treatments applied."""
        return tuple(self._masses()[1])

    @property
    def extrapolated_mass_fraction(self):
        """Mass fraction below the smallest measured size."""
        return self._masses()[2]

    def median_um(self):
        """Mass median size xmed [µm] by log-linear interpolation of F."""
        intervals, _, _ = self._masses()
        running = 0.0
        for lo, hi, w in intervals:
            if running + w >= 0.5:
                if hi == lo:
                    return lo
                t = (0.5 - running) / w
                return math.exp(math.log(lo) + t * (math.log(hi) - math.log(lo)))
            running += w
        return intervals[-1][1]

    def classification_efficiency(self, x50_um, m):
        """Σ ηi·ΔMFi of Eq. 6.3.3, integrated exactly per interval."""
        intervals, _, _ = self._masses()
        total = 0.0
        for lo, hi, w in intervals:
            if hi == lo:
                total += w * eq.grade_efficiency(lo, x50_um, m)
                continue
            g_hi = _softplus(m * math.log(hi / x50_um)) / m
            g_lo = _softplus(m * math.log(lo / x50_um)) / m
            total += w * (g_hi - g_lo) / (math.log(hi) - math.log(lo))
        return total


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CycloneResult:
    """Every intermediate and output of the calculation (SI; sizes in m
    unless the name ends in ``_um``)."""
    # geometry-derived
    R: float
    Rx: float
    Rd: float
    Rin: float
    Rm: float
    A_R: float
    H_CS: float
    # velocities
    xi: float
    alpha: float
    v_in: float
    v_theta_w: float
    v_z_w: float
    v_theta_cs: float
    v_theta_m: float
    v_x: float
    U_t50: float
    # friction
    Re_R: float
    ks_over_R: float
    f_air: float
    f: float
    Fr_x: float
    rho_str: float
    # cut size and loading
    x50: float
    x50_stokes: float
    x50_non_stokes: float
    stokes_regime: bool
    Re_p: float
    co: float
    x_med_um: float
    co_L: float
    saltation: bool
    m: float
    # efficiency
    eta_classification: float
    eta_overall: float
    penetration: float
    emission_kg_h: float
    emission_mg_m3: float
    # pressure drop
    dp_body: float
    dp_core: float
    dp_acc: float
    dp_total: float
    # diagnostics
    iterations: int
    converged: bool
    extrapolated_mass_fraction: float
    psd_notes: tuple = field(default_factory=tuple)
    warnings: tuple = field(default_factory=tuple)

    @property
    def x50_um(self):
        return self.x50 * 1e6

    def classification_grade_efficiency(self, sizes_um):
        """Eq. 6.3.2 evaluated at each size [µm]: classification only."""
        return [eq.grade_efficiency(x, self.x50_um, self.m) for x in sizes_um]

    def total_grade_efficiency(self, sizes_um):
        """Grade efficiency including the mass-loading (saltation) share:
        (1 − coL/co) + (coL/co)·ηi when co > coL, else the classification
        curve (the per-size form of Eq. 6.5.1)."""
        eta_i = self.classification_grade_efficiency(sizes_um)
        if not self.saltation:
            return eta_i
        share = self.co_L / self.co
        return [(1.0 - share) + share * e for e in eta_i]


# ──────────────────────────────────────────────────────────────────────────────
# Calculation steps
# ──────────────────────────────────────────────────────────────────────────────

def _step_inlet(geom, gas, co, rin):
    """α → vin → vθw → Rm → vzw (Eqs. 6.1.1-6.1.5)."""
    R, Rx = geom.R, geom.Rx
    xi = geom.b / R
    alpha = eq.constriction_coefficient(xi, co)
    v_in = eq.inlet_velocity(gas.flow_rate, geom.a, geom.b)
    v_theta_w = eq.wall_tangential_velocity(v_in, rin, alpha, R)
    Rm = eq.geometric_mean_radius(Rx, R)
    v_z_w = eq.wall_axial_velocity(gas.flow_rate, R, Rm)
    return xi, alpha, v_in, v_theta_w, Rm, v_z_w


def _step_friction(re_r, ks_over_r, eta, co, fr_x, gas, rho_str, geom):
    """fsm, fr → fair → f (Eqs. 6.1.8, 6.1.9, 6.1.11)."""
    f_sm = eq.smooth_wall_friction_conical(re_r)
    f_r = eq.roughness_friction_conical(re_r, ks_over_r)
    f_air = eq.gas_friction_factor(f_sm, f_r)
    f = eq.total_friction_factor(f_air, geom.R, geom.Rx, eta, co, fr_x, gas.density, rho_str)
    return f_air, f


def _step_cut_size(geom, gas, solids, v_theta_cs):
    """x50 by Eq. 6.2.3 (Stokes), switching to Eq. 6.2.6 when Rep ≥ 0.5."""
    H_CS = eq.control_surface_height(geom.H, geom.S, geom.Hc, geom.Rx, geom.Rd, geom.R)
    U_t50 = eq.cut_point_terminal_velocity(gas.flow_rate, geom.Rx, H_CS)
    x50_stokes = eq.cut_size_stokes(
        gas.viscosity, gas.flow_rate, solids.particle_density, gas.density,
        v_theta_cs, geom.H, geom.S,
    )
    re_p = eq.particle_reynolds_number(gas.density, U_t50, x50_stokes, gas.viscosity)
    x50_non_stokes = eq.cut_size_non_stokes(
        gas.viscosity, gas.density, U_t50, solids.particle_density, v_theta_cs, geom.Rx
    )
    stokes = re_p < STOKES_REP_LIMIT
    x50 = x50_stokes if stokes else x50_non_stokes
    if not stokes:
        re_p = eq.particle_reynolds_number(gas.density, U_t50, x50, gas.viscosity)
    return H_CS, U_t50, x50_stokes, x50_non_stokes, stokes, x50, re_p


def _run(geometry, gas, solids, psd, m, x_med_um, upstream_velocity_m_s, rin=None):
    """Full calculation. ``rin`` overrides the radial position of the inlet
    centre; it exists only so the tests can reproduce a workbook that used a
    scroll-inlet radius, and is deliberately not exposed by the public entry
    point (Ch. 6 covers the slot inlet only)."""
    R, Rx, Rd = geometry.R, geometry.Rx, geometry.Rd
    Q, rho, mu = gas.flow_rate, gas.density, gas.viscosity
    co = solids.dust_loading / rho
    if rin is None:
        rin = R - geometry.b / 2

    xi, alpha, v_in, v_theta_w, Rm, v_z_w = _step_inlet(geometry, gas, co, rin)
    A_R = eq.total_inside_area(R, Rx, Rd, geometry.H, geometry.Hc, geometry.S)
    v_x = Q / (math.pi * Rx ** 2)
    fr_x = eq.froude_number_vortex_finder(v_x, Rx)
    rho_str = eq.strand_density(solids.bulk_density)
    ks_over_r = max(solids.wall_roughness / R, KS_OVER_R_MIN)
    clamped = solids.wall_roughness / R < KS_OVER_R_MIN
    x_med = x_med_um if x_med_um is not None else psd.median_um()

    # Fixed-point iteration on (ReR, η): ReR starts from Eq. 6.1.6 with the
    # (vzw/vθm)² term neglected (footnote 1, p. 115); η starts at 0.95.
    re_r = eq.body_reynolds_number(rin, Rm, v_z_w, rho, geometry.H, mu, 1e12)
    eta = 0.95
    converged = False
    iterations = 0
    for iterations in range(1, _MAX_ITER + 1):
        f_air, f = _step_friction(re_r, ks_over_r, eta, co, fr_x, gas, rho_str, geometry)
        v_theta_cs = eq.inner_core_tangential_velocity(v_theta_w, R, Rx, f, A_R, Q)
        v_theta_m = eq.mean_rotational_velocity(v_theta_w, v_theta_cs)
        re_r_new = eq.body_reynolds_number(rin, Rm, v_z_w, rho, geometry.H, mu, v_theta_m)
        H_CS, U_t50, x50_st, x50_ns, stokes, x50, re_p = _step_cut_size(
            geometry, gas, solids, v_theta_cs
        )
        co_L = eq.limit_loading(x50 * 1e6, x_med, co)
        saltation = co > co_L
        eta_class = psd.classification_efficiency(x50 * 1e6, m)
        eta_new = (
            eq.overall_efficiency_saltation(co, co_L, eta_class) if saltation else eta_class
        )
        done = (
            abs(re_r_new - re_r) <= _CONV_TOL * re_r and abs(eta_new - eta) <= _CONV_TOL
        )
        re_r, eta = re_r_new, eta_new
        if done:
            converged = True
            break

    # Final consistent pass with the converged ReR and η.
    f_air, f = _step_friction(re_r, ks_over_r, eta, co, fr_x, gas, rho_str, geometry)
    v_theta_cs = eq.inner_core_tangential_velocity(v_theta_w, R, Rx, f, A_R, Q)
    v_theta_m = eq.mean_rotational_velocity(v_theta_w, v_theta_cs)

    dp_body = eq.pressure_drop_body(f, A_R, rho, v_theta_w, v_theta_cs, Q)
    dp_core = eq.pressure_drop_core(v_theta_cs, v_x, rho)
    dp_acc = 0.0
    if upstream_velocity_m_s is not None and upstream_velocity_m_s < v_in:
        dp_acc = eq.pressure_drop_acceleration(co, rho, v_in, upstream_velocity_m_s)
    dp_total = eq.pressure_drop_total(dp_body, dp_core, dp_acc)

    penetration = 1.0 - eta
    loading = solids.dust_loading
    warnings = []
    if clamped:
        warnings.append(
            f"ks/R = {solids.wall_roughness / R:.2e} is below the smooth-wall limit; "
            f"{KS_OVER_R_MIN:.0e} was used (H&S p. 115)."
        )
    if not stokes and not (NON_STOKES_REP_RANGE[0] <= re_p <= NON_STOKES_REP_RANGE[1]):
        warnings.append(
            f"Rep = {re_p:.3g} is outside 0.3-1000, the validity range of the drag "
            "correlation behind Eq. 6.2.6."
        )
    if not converged:
        warnings.append(f"Iteration on ReR and η did not converge in {_MAX_ITER} steps.")
    notes = psd.notes
    warnings.extend(n for n in notes if n.startswith("Warning"))

    return CycloneResult(
        R=R, Rx=Rx, Rd=Rd, Rin=rin, Rm=Rm, A_R=A_R, H_CS=H_CS,
        xi=xi, alpha=alpha, v_in=v_in, v_theta_w=v_theta_w, v_z_w=v_z_w,
        v_theta_cs=v_theta_cs, v_theta_m=v_theta_m, v_x=v_x, U_t50=U_t50,
        Re_R=re_r, ks_over_R=ks_over_r, f_air=f_air, f=f, Fr_x=fr_x, rho_str=rho_str,
        x50=x50, x50_stokes=x50_st, x50_non_stokes=x50_ns, stokes_regime=stokes,
        Re_p=re_p, co=co, x_med_um=x_med, co_L=co_L, saltation=saltation, m=m,
        eta_classification=eta_class, eta_overall=eta, penetration=penetration,
        emission_kg_h=Q * loading * penetration * 3600.0,
        emission_mg_m3=loading * penetration * 1e6,
        dp_body=dp_body, dp_core=dp_core, dp_acc=dp_acc, dp_total=dp_total,
        iterations=iterations, converged=converged,
        extrapolated_mass_fraction=psd.extrapolated_mass_fraction,
        psd_notes=notes, warnings=tuple(warnings),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def cyclone_performance(
    geometry,
    gas,
    solids,
    psd=None,
    slope_m=5.0,
    x_med_um=None,
    upstream_velocity_m_s=None,
):
    """Cut size, efficiency, pressure drop and emission of a cyclone by the
    Muschelknautz method (H&S Ch. 6), slot-type inlet.

    Args:
        geometry (CycloneGeometry): Cyclone dimensions [m]
        gas (GasProperties): Gas density, viscosity and flow
        solids (SolidProperties): Dust properties, loading and wall roughness
        psd (ParticleSizeDistribution | None): Feed distribution. Optional
            only when ``x_med_um`` is given; the feed is then treated as
            monodisperse at that size.
        slope_m (float): Grade-efficiency slope m of Eq. 6.3.2 (book range
            2-7, typical 3, 4-6 for well-designed smooth cyclones; 5 used in
            the book's examples; p. 121)
        x_med_um (float | None): Explicit mass median size of the feed [µm]
            for the limit loading (Eqs. 6.4.1/6.4.2). Defaults to the median
            of ``psd``.
        upstream_velocity_m_s (float | None): Gas velocity upstream of the
            inlet for the acceleration loss of Eq. 6.6.3. None, or a value not
            below the inlet velocity, gives Δpacc = 0.

    Returns:
        CycloneResult
    """
    if not slope_m > 0:
        raise ValueError("slope_m must be positive")
    if psd is None:
        if x_med_um is None:
            raise ValueError("give a particle size distribution or an explicit x_med_um")
        psd = ParticleSizeDistribution((x_med_um,), (1.0,))
    if x_med_um is not None and not x_med_um > 0:
        raise ValueError("x_med_um must be positive")
    return _run(geometry, gas, solids, psd, slope_m, x_med_um, upstream_velocity_m_s)
