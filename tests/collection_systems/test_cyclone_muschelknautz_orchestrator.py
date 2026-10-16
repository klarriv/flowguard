"""Tests for collection_systems.cyclone_muschelknautz_orchestrator.

Covers the feed particle size distribution (PSD) handling, the full
calculation against Hoffmann & Stein example 6.A.1 (p. 126), and a comparison
with the Excel workbook "Cyclone Design - Calculation Sheet" (tab
"Muschelknautz Method"), whose inputs and cached outputs are embedded below.
The workbook itself is never committed.
"""
import math

from collection_systems import cyclone_muschelknautz_orchestrator as orch
from collection_systems.cyclone_muschelknautz_orchestrator import (
    CycloneGeometry,
    GasProperties,
    ParticleSizeDistribution,
    SolidProperties,
    cyclone_performance,
)


def close(actual, expected, rel=1e-4):
    assert math.isclose(actual, expected, rel_tol=rel), (actual, expected)


def raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return
    raise AssertionError(f"{fn.__name__} did not raise {exc.__name__}")


# Example 6.A.1: Hoffmann cyclone, p. 126
GEOM = CycloneGeometry(D=0.2, a=0.1, b=0.04, Dx=0.075, S=0.1, H=0.8, Hc=0.5, Dd=0.075)
GAS = GasProperties(density=1.2, viscosity=1.8e-5, flow_rate=0.04)
SOLIDS = SolidProperties(particle_density=2730.0, bulk_density=1365.0, dust_loading=4.5e-3)
BOOK_PSD = ParticleSizeDistribution.from_cumulative(
    [0.3, 1.0, 2.0, 3.0, 3.4, 5.0, 8.0, 15.0, 30.0, 40.0, 60.0],
    [0.0, 0.135, 0.300, 0.440, 0.500, 0.630, 0.750, 0.850, 0.940, 0.975, 1.0],
)

# ── PSD ──────────────────────────────────────────────────────────────────────


def _log_uniform_bins(lo, hi, n, total=1.0):
    edges = [lo * (hi / lo) ** (i / n) for i in range(n + 1)]
    return edges[:-1], edges[1:], [total / n] * n


def test_psd_efficiency_is_independent_of_binning_of_same_distribution():
    # same log-uniform distribution 2-50 µm cut into 4 and into 64 bins
    coarse = ParticleSizeDistribution.from_bins(*_log_uniform_bins(2.0, 50.0, 4))
    fine = ParticleSizeDistribution.from_bins(*_log_uniform_bins(2.0, 50.0, 64))
    close(coarse.classification_efficiency(8.0, 5.0), fine.classification_efficiency(8.0, 5.0), 1e-9)


def test_psd_closed_form_matches_numerical_integration():
    psd = ParticleSizeDistribution.from_cumulative([2.0, 50.0], [0.0, 1.0])
    x50, m, n = 8.0, 5.0, 20000
    lo, hi = math.log(2.0), math.log(50.0)
    numeric = sum(
        1.0 / (1.0 + (x50 / math.exp(lo + (i + 0.5) * (hi - lo) / n)) ** m) for i in range(n)
    ) / n
    close(psd.classification_efficiency(x50, m), numeric, 1e-6)


def test_psd_sieve_and_laser_constructors_agree_on_equivalent_data():
    # sieve: apertures 10, 20, 40 µm; retained 0.3, 0.2, 0.1; pan 0.4
    sieve = ParticleSizeDistribution.from_sieve([10, 20, 40], [0.3, 0.2, 0.1], pan_fraction=0.4)
    # equivalent cumulative: F(10) = 0.4, F(20) = 0.7, F(40) = 0.9, 0.1 above 40
    laser = ParticleSizeDistribution.from_cumulative([10, 20, 40], [0.4, 0.7, 0.9])
    close(sieve.classification_efficiency(15.0, 3.0), laser.classification_efficiency(15.0, 3.0), 1e-12)
    close(sieve.median_um(), laser.median_um(), 1e-12)


def test_psd_sieve_is_order_independent():
    a = ParticleSizeDistribution.from_sieve([40, 10, 20], [0.1, 0.3, 0.2], pan_fraction=0.4)
    b = ParticleSizeDistribution.from_sieve([10, 20, 40], [0.3, 0.2, 0.1], pan_fraction=0.4)
    assert a.sizes_um == b.sizes_um and a.cumulative == b.cumulative


def test_psd_below_range_mass_spread_over_one_extra_log_interval():
    # F(2) = 0.2, F(8) = 1: first interval has log-width ln 4, so the extra
    # interval runs 0.5 to 2 µm with 0.2 of the mass.
    psd = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.2, 1.0])
    close(psd.extrapolated_mass_fraction, 0.2)
    intervals, notes, _ = psd._masses()
    close(intervals[0][0], 0.5, 1e-12)
    close(intervals[0][1], 2.0, 1e-12)
    close(intervals[0][2], 0.2)
    assert any("below the smallest size" in n for n in notes)
    # mass fraction above 5 % also raises a warning note
    assert any(n.startswith("Warning") for n in psd.notes)


def test_psd_below_range_efficiency_is_lower_than_if_mass_sat_at_smallest_size():
    psd = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.2, 1.0])
    point = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.0, 1.0])
    assert psd.classification_efficiency(4.0, 5.0) < point.classification_efficiency(4.0, 5.0)


def test_psd_above_range_remaining_mass_is_point_mass_at_largest_size():
    psd = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.0, 0.9])
    intervals, notes, _ = psd._masses()
    close(intervals[-1][2], 0.1, 1e-12)
    assert intervals[-1][0] == intervals[-1][1] == 8.0
    assert any("above the largest size" in n for n in notes)


def test_psd_cumulative_slightly_off_one_is_renormalised():
    psd = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.0, 0.9995])
    intervals, notes, _ = psd._masses()
    close(sum(w for _, _, w in intervals), 1.0, 1e-12)
    assert any("renormalised" in n for n in notes)


def test_psd_cumulative_above_one_by_more_than_tolerance_is_an_error():
    raises(ValueError, ParticleSizeDistribution.from_cumulative, [2.0, 8.0], [0.0, 1.01])


def test_psd_single_point_is_monodisperse():
    psd = ParticleSizeDistribution.from_cumulative([5.0], [1.0])
    close(psd.median_um(), 5.0)
    close(psd.classification_efficiency(5.0, 4.0), 0.5)  # eta(x50) = 0.5
    assert psd.classification_efficiency(50.0, 4.0) < 0.01  # x50 far above 5 µm
    assert any("monodisperse" in n for n in psd.notes)


def test_psd_two_point_distribution_gives_log_linear_median():
    psd = ParticleSizeDistribution.from_cumulative([2.0, 8.0], [0.0, 1.0])
    close(psd.median_um(), 4.0)  # geometric midpoint


def test_psd_median_of_book_distribution_is_3_4_um():
    close(BOOK_PSD.median_um(), 3.4, 1e-9)  # F(3.4) = 0.5 in Fig. 6.A.1


def test_psd_efficiency_limits():
    psd = ParticleSizeDistribution.from_cumulative([10.0, 100.0], [0.0, 1.0])
    assert psd.classification_efficiency(0.01, 5.0) > 0.999999  # all above x50
    assert psd.classification_efficiency(1e6, 5.0) < 1e-9  # all below x50


def test_psd_bad_inputs_are_errors():
    raises(ValueError, ParticleSizeDistribution.from_cumulative, [2.0, 2.0], [0.1, 0.5])
    raises(ValueError, ParticleSizeDistribution.from_cumulative, [2.0, 8.0], [0.6, 0.5])
    raises(ValueError, ParticleSizeDistribution.from_cumulative, [-1.0, 8.0], [0.1, 0.5])
    raises(ValueError, ParticleSizeDistribution.from_cumulative, [2.0], [0.1, 0.5])
    raises(ValueError, ParticleSizeDistribution.from_bins, [1, 3], [2, 4], [0.5, 0.5])  # gap
    raises(ValueError, ParticleSizeDistribution.from_bins, [1], [1], [1.0])
    raises(ValueError, ParticleSizeDistribution.from_sieve, [10, 20], [0.3, 0.3])  # sum 0.6
    raises(ValueError, ParticleSizeDistribution.from_sieve, [10], [1.0])


# ── geometry / inputs ────────────────────────────────────────────────────────


def test_geometry_validation():
    raises(ValueError, CycloneGeometry, 0.2, 0.1, 0.04, 0.25, 0.1, 0.8, 0.5, 0.075)  # Dx >= D
    raises(ValueError, CycloneGeometry, 0.2, 0.1, 0.04, 0.075, 0.9, 0.8, 0.5, 0.075)  # S >= H
    raises(ValueError, CycloneGeometry, 0.2, 0.1, 0.04, 0.075, 0.1, 0.8, 0.9, 0.075)  # Hc > H
    raises(ValueError, CycloneGeometry, 0.2, 0.1, 0.04, 0.075, 0.1, 0.8, 0.5, 0.2)  # Dd >= D
    raises(ValueError, CycloneGeometry, 0.2, 0.1, 0.0, 0.075, 0.1, 0.8, 0.5, 0.075)  # b = 0
    raises(ValueError, GasProperties, -1.0, 1.8e-5, 0.04)
    raises(ValueError, SolidProperties, 2730.0, 1365.0, 0.0)


def test_psd_or_x_med_is_required():
    raises(ValueError, cyclone_performance, GEOM, GAS, SOLIDS)


# ── example 6.A.1 (p. 126) ───────────────────────────────────────────────────


def test_example_6_A_1_intermediates_and_results():
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    assert r.converged
    close(r.alpha, 0.623, 1e-2)
    close(r.A_R, 0.46, 1e-2)  # book prints 0.46 (0.4567)
    close(r.v_z_w, 1.83, 1e-2)
    close(r.v_x, 9.05, 1e-2)
    close(r.U_t50, 0.243, 1e-2)
    close(r.Re_p, 0.027, 1e-2)
    close(r.f_air, 0.0058, 1e-2)
    close(r.ks_over_R, 0.0006, 1e-9)  # 0.00046 -> 0.0006 (p. 126)
    close(r.v_theta_cs, 18.6, 1e-2)
    close(r.x50_um, 1.68, 1e-2)
    close(r.dp_body, 198.0, 1.5e-2)
    close(r.dp_core, 689.0, 1.5e-2)
    close(r.dp_total, 887.0, 1e-2)
    assert r.stokes_regime and r.saltation and r.dp_acc == 0.0


def test_example_6_A_1_total_friction_factor_within_book_rounding():
    # book f = 0.0071 comes from its own (unstated) η; ours is converged
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    close(r.f, 0.0071, 3e-2)


def test_example_6_A_1_known_mismatch_body_reynolds_number():
    # The book prints ReR ≈ 749, neglecting the (vzw/vθm)² term of Eq. 6.1.6
    # (p. 114-115). With the term kept, as the equation is written, ReR = 738.
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    close(r.Re_R, 738.2, 2e-3)
    assert r.Re_R < 749.0


def test_example_6_A_1_known_mismatch_limit_loading():
    # Book prints coL = 0.00332 kg/kg; Eq. 6.4.2 with the stated inputs
    # (x50 = 1.68 µm, xmed = 3.4 µm, co = 0.00375) gives 0.00283. Both the
    # book's inputs and our converged x50 give ~0.0028.
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    close(r.co_L, 0.00281, 2e-2)
    assert r.co_L < 0.00332


def test_outputs_are_internally_consistent():
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    close(r.penetration, 1.0 - r.eta_overall, 1e-12)
    close(r.dp_total, r.dp_body + r.dp_core + r.dp_acc, 1e-12)
    close(r.emission_mg_m3, 4.5e-3 * 1e6 * r.penetration, 1e-9)
    close(r.emission_kg_h, 0.04 * 4.5e-3 * r.penetration * 3600.0, 1e-9)
    assert r.eta_overall >= r.eta_classification  # saltation adds capture
    # per-size total curve reduces to Eq. 6.5.1 when integrated over the PSD
    share = r.co_L / r.co
    close(r.eta_overall, (1 - share) + share * r.eta_classification, 1e-12)


def test_grade_efficiency_curves():
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, slope_m=5.0)
    close(r.classification_grade_efficiency([r.x50_um])[0], 0.5)
    total = r.total_grade_efficiency([0.1, r.x50_um, 100.0])
    assert total[0] > 0.0 and total[2] <= 1.0 + 1e-12
    share = r.co_L / r.co
    close(total[1], (1 - share) + share * 0.5)


def test_acceleration_loss_only_when_upstream_velocity_below_inlet():
    base = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD)
    slow = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, upstream_velocity_m_s=2.0)
    close(slow.dp_acc, (1 + base.co) * 1.2 * (10.0 ** 2 - 2.0 ** 2) / 2.0, 1e-9)
    close(slow.dp_total, base.dp_total + slow.dp_acc, 1e-9)
    fast = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, upstream_velocity_m_s=50.0)
    assert fast.dp_acc == 0.0


def test_below_limit_loading_uses_classification_efficiency_only():
    # a very fine feed (xmed 0.1 µm) has coL = 0.025 (x50/xmed)(10 co)^k ≈ 0.1
    # kg/kg, far above co = 0.00375, so no saltation occurs
    r = cyclone_performance(GEOM, GAS, SOLIDS, BOOK_PSD, x_med_um=0.1)
    assert not r.saltation and r.co_L > r.co
    close(r.eta_overall, r.eta_classification, 1e-12)


def test_monodisperse_feed_from_explicit_median():
    r = cyclone_performance(GEOM, GAS, SOLIDS, x_med_um=10.0)
    assert r.x_med_um == 10.0 and r.converged
    assert any("monodisperse" in n for n in r.psd_notes)


def test_non_stokes_branch_is_selected_for_large_particle_reynolds_number():
    # a large, fast cyclone: x50 large enough that Rep > 0.5
    geom = CycloneGeometry(D=1.0, a=0.5, b=0.2, Dx=0.5, S=0.5, H=4.0, Hc=2.0, Dd=0.3)
    gas = GasProperties(1.2, 1.8e-5, 12.0)
    r = cyclone_performance(geom, gas, SOLIDS, BOOK_PSD)
    assert r.converged
    assert r.stokes_regime == (r.Re_p < 0.5)


# ── workbook comparison ──────────────────────────────────────────────────────
# Workbook inputs (tab "Muschelknautz Method", cells C10:C27, G16:G17, G54,
# X10:Z40) and cached outputs. "Scroll" inlet: Rin = R + b/2 = 0.12 m together
# with the slot constriction coefficient, which is the combination the book
# does not give (see the plan's Workbook discrepancies table).

WB_BINS = [
    (1.945, 2.312, 0.44), (2.312, 2.75, 0.54), (2.75, 3.27, 0.70), (3.27, 3.89, 0.64),
    (3.89, 4.62, 1.42), (4.62, 5.5, 2.32), (5.5, 6.54, 1.88), (6.54, 7.78, 2.42),
    (7.78, 9.25, 3.20), (9.25, 11, 3.17), (11, 13.08, 3.38), (13.08, 15.56, 4.28),
    (15.56, 18.5, 5.08), (18.5, 22, 5.51), (22, 26.16, 5.53), (26.16, 31.11, 4.96),
    (31.11, 37, 4.76), (37, 44, 5.06), (44, 52.32, 5.75), (52.32, 62.23, 6.40),
    (62.23, 74, 6.24), (74, 88, 4.36), (88, 104.6, 2.44), (104.6, 124.5, 1.37),
    (124.5, 148, 1.07), (148, 176, 1.56), (176, 209.3, 3.21), (209.3, 248.9, 5.53),
    (248.9, 296, 4.71), (296, 352, 1.70), (352, 418.6, 0.37),
]
WB_PSD = ParticleSizeDistribution.from_bins(
    [b[0] for b in WB_BINS], [b[1] for b in WB_BINS], [b[2] / 100.0 for b in WB_BINS]
)
WB_X_MED_UM = 3.4  # typed into C27, independent of the PSD
WB_X50_UM = 1.2976666861930608  # G49
WB_DP_TOTAL = 1467.3580465399714  # T13
WB_PENETRATION = 4.4557058782231947e-4  # sum of AF10:AF40
WB_CO_L = 0.00218743297074501  # G52
WB_V_THETA_W = 19.269629987217403  # G20


def test_workbook_comparison_with_scroll_radius():
    # Differences to the workbook's cached values, all explained by the plan's
    # discrepancy table: ReR goal-seek (workbook x50 0.05 % low), η fixed at
    # 0.95 in the friction factor (x50 +0.27 %, Δp -0.27 %), so x50 differs by
    # +0.32 % in total; and the exact log-interval integral instead of the
    # geometric bin midpoint (penetration).
    r = orch._run(GEOM, GAS, SOLIDS, WB_PSD, 5.0, WB_X_MED_UM, None, rin=0.12)
    assert r.converged
    close(r.alpha, 0.6227415891203025, 1e-9)
    close(r.v_theta_w, WB_V_THETA_W, 1e-9)
    close(r.x50_um, WB_X50_UM, 4e-3)
    close(r.dp_total, WB_DP_TOTAL, 3e-3)
    close(r.co_L, WB_CO_L, 1e-2)
    assert r.saltation
    close(r.penetration, WB_PENETRATION, 5e-2)


def test_workbook_penetration_difference_is_the_integration_scheme():
    # Evaluate the workbook's geometric-midpoint scheme at the library's own
    # x50 and limit loading: it must be within 2.5 % of the workbook value
    # (only the η/ReR iteration differs), leaving the rest of the difference
    # to the exact log-interval integral.
    r = orch._run(GEOM, GAS, SOLIDS, WB_PSD, 5.0, WB_X_MED_UM, None, rin=0.12)
    share = r.co_L / r.co
    midpoint = sum(
        w / 100.0 * (1.0 - ((1.0 - share) + share / (1.0 + (r.x50_um / math.sqrt(lo * hi)) ** 5.0)))
        for lo, hi, w in WB_BINS
    )
    close(midpoint, WB_PENETRATION, 2.5e-2)
    # exact integral is higher because uniform-in-log mass sits more in the
    # lower half of each bin than the geometric midpoint suggests
    assert r.penetration > midpoint
    close(r.penetration, midpoint, 5e-2)


def test_workbook_inputs_with_book_slot_inlet_give_the_large_deltas():
    # Same workbook inputs with the slot inlet of Ch. 6 (the public entry
    # point): vθw 12.85 instead of 19.27 m/s, x50 1.68 µm, Δp 887 Pa, and
    # roughly four times the workbook's emission.
    r = cyclone_performance(GEOM, GAS, SOLIDS, WB_PSD, slope_m=5.0, x_med_um=WB_X_MED_UM)
    close(r.v_theta_w, 12.846, 1e-3)
    close(r.x50_um, 1.679, 3e-3)
    close(r.dp_total, 887.4, 3e-3)
    close(r.penetration, 1.909e-3, 2e-2)
    assert r.penetration > 3.5 * WB_PENETRATION


def test_workbook_psd_sums_to_one_and_has_placeholder_median():
    close(sum(b[2] for b in WB_BINS) / 100.0, 1.0, 1e-6)
    close(WB_PSD.median_um(), 36.7, 1e-2)  # not 3.4 µm: placeholder data
