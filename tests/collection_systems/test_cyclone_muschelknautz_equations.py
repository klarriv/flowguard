"""Per-equation tests for collection_systems.cyclone_muschelknautz_equations.

Reference values are hand-computed from the equations as printed in
Hoffmann & Stein (2nd ed.), Ch. 6, using the Hoffmann cyclone of example
6.A.1 (p. 126) as the common input set unless stated otherwise.
"""
import math

from collection_systems import cyclone_muschelknautz_equations as eq

# Example 6.A.1 inputs (p. 126)
D, a, b, Dx, S, H, Hc, Dd = 0.2, 0.1, 0.04, 0.075, 0.1, 0.8, 0.5, 0.075
R, Rx, Rd = D / 2, Dx / 2, Dd / 2
Q, rho, mu, rho_p = 0.04, 1.2, 1.8e-5, 2730.0
CO = 4.5e-3 / rho  # 4.5 g/m³ -> kg/kg


def close(actual, expected, rel=1e-4):
    assert math.isclose(actual, expected, rel_tol=rel), (actual, expected)


def test_eq_6_1_1_constriction_coefficient():
    close(eq.constriction_coefficient(b / R, CO), 0.62274, 1e-4)  # book 0.623


def test_eq_6_1_1_tends_to_one_for_vanishing_inlet_width():
    # xi -> 0: no constriction
    close(eq.constriction_coefficient(1e-4, 0.0), 1.0, 1e-3)


def test_eq_6_1_3_inlet_velocity():
    close(eq.inlet_velocity(Q, a, b), 10.0)


def test_eq_6_1_2_wall_tangential_velocity():
    close(eq.wall_tangential_velocity(10.0, R - b / 2, 0.62274, R), 12.8466, 1e-4)


def test_eq_6_1_4_geometric_mean_radius():
    close(eq.geometric_mean_radius(Rx, R), math.sqrt(0.00375))


def test_eq_6_1_5_wall_axial_velocity():
    Rm = eq.geometric_mean_radius(Rx, R)
    close(eq.wall_axial_velocity(Q, R, Rm), 1.8335, 1e-4)  # book 1.83


def test_eq_6_1_6_body_reynolds_number_reduces_without_axial_term():
    # vz/vθm -> 0 : ReR = Rin Rm vzw rho / (H mu)
    Rin, Rm, vz = 0.08, 0.0612372, 1.8335
    expected = Rin * Rm * vz * rho / (H * mu)
    close(eq.body_reynolds_number(Rin, Rm, vz, rho, H, mu, 1e9), expected)
    # with a finite vθm the (vz/vθm)² term reduces ReR
    assert eq.body_reynolds_number(Rin, Rm, vz, rho, H, mu, 20.0) < expected


def test_eq_6_1_7_mean_rotational_velocity():
    close(eq.mean_rotational_velocity(12.0, 27.0), 18.0)


def test_eq_6_1_9_smooth_wall_friction_at_reR_749():
    close(eq.smooth_wall_friction_conical(749.0), 0.005227, 1e-3)


def test_eq_6_1_9_roughness_friction_at_smooth_wall_limit():
    # ks/R = 6e-4 (smooth limit), ReR = 749: hand value 5.33e-4
    close(eq.roughness_friction_conical(749.0, 6e-4), 5.33e-4, 1e-2)


def test_eq_6_1_9_roughness_friction_rises_with_roughness():
    assert eq.roughness_friction_conical(5000.0, 5e-3) > eq.roughness_friction_conical(5000.0, 1e-3)


def test_eq_6_1_8_gas_friction_factor_matches_book():
    f_air = eq.gas_friction_factor(
        eq.smooth_wall_friction_conical(749.0), eq.roughness_friction_conical(749.0, 6e-4)
    )
    close(f_air, 0.0058, 1e-2)  # book 0.0058


def test_eq_6_1_11_total_friction_factor_no_solids_equals_gas_value():
    close(eq.total_friction_factor(0.0058, R, Rx, 0.95, 0.0, 10.5, rho, 546.0), 0.0058)


def test_eq_6_1_11_total_friction_factor_with_solids():
    # 0.25 (R/Rx)^-0.625 sqrt(eta co Fr rho / rho_str) with R/Rx = 8/3
    f = eq.total_friction_factor(0.0058, R, Rx, 0.95, CO, 10.5556, rho, 546.0)
    close(f, 0.0058 + 0.25 * (R / Rx) ** -0.625 * math.sqrt(0.95 * CO * 10.5556 * rho / 546.0))
    assert 0.0069 < f < 0.0072  # book f = 0.0071


def test_strand_density_default_is_04_bulk():
    close(eq.strand_density(1365.0), 546.0)


def test_eq_6_1_12_froude_number():
    vx = Q / (math.pi * Rx ** 2)
    close(eq.froude_number_vortex_finder(vx, Rx), 10.5556, 1e-3)


def test_eq_6_2_1_inner_core_velocity_without_friction_is_angular_momentum():
    # f = 0 -> vθCS = vθw R / Rx
    close(eq.inner_core_tangential_velocity(12.8466, R, Rx, 0.0, 0.4567, Q), 12.8466 * R / Rx)


def test_eq_6_2_1_inner_core_velocity_matches_book():
    close(eq.inner_core_tangential_velocity(12.8466, R, Rx, 0.0071, 0.4567, Q), 18.6, 1e-2)


def test_eq_6_2_2_total_inside_area():
    close(eq.total_inside_area(R, Rx, Rd, H, Hc, S), 0.45672, 1e-4)  # book 0.46


def test_control_surface_height_wide_dust_outlet():
    close(eq.control_surface_height(H, S, Hc, Rx, Rd, R), 0.7)  # Rd == Rx


def test_control_surface_height_narrow_dust_outlet_is_shorter():
    # Rd = 0.0125: (0.7) - 0.5 (0.0375-0.0125)/(0.1-0.0125)
    close(eq.control_surface_height(H, S, Hc, Rx, 0.0125, R), 0.7 - 0.5 * 0.025 / 0.0875)


def test_eq_6_2_3_cut_size_stokes_matches_book():
    close(eq.cut_size_stokes(mu, Q, rho_p, rho, 18.6, H, S) * 1e6, 1.68, 1e-2)


def test_eq_6_2_4_particle_reynolds_number_matches_book():
    close(eq.particle_reynolds_number(rho, 0.2425, 1.676e-6, mu), 0.0271, 1e-2)  # book 0.027


def test_eq_6_2_5_cut_point_terminal_velocity_matches_book():
    close(eq.cut_point_terminal_velocity(Q, Rx, 0.7), 0.2425, 1e-3)  # book 0.243


def test_eq_6_2_6_non_stokes_cut_size_hand_value():
    # mu^0.375 rho^0.25 U^0.875 / ((rp-rho) v²/Rx)^0.625 * 5.18
    expected = 5.18 * (mu ** 0.375 * rho ** 0.25 * 0.2425 ** 0.875) / (
        ((rho_p - rho) * 18.6 ** 2 / Rx) ** 0.625
    )
    close(eq.cut_size_non_stokes(mu, rho, 0.2425, rho_p, 18.6, Rx), expected)
    # cross-check: workbook G44 gives 0.4487 µm at vθCS = 24.02 m/s; x50 scales
    # as vθCS^-1.25, so at 18.6 m/s it is 0.4487 * (24.02/18.6)^1.25 = 0.618 µm
    close(expected * 1e6, 0.4487 * (24.0235 / 18.6) ** 1.25, 1e-2)


def test_eq_6_3_2_grade_efficiency_limits():
    close(eq.grade_efficiency(2.0, 2.0, 5.0), 0.5)  # eta(x50) = 0.5
    assert eq.grade_efficiency(100.0, 2.0, 5.0) > 0.9999
    assert eq.grade_efficiency(0.01, 2.0, 5.0) < 1e-6


def test_eq_6_3_2_grade_efficiency_hand_value():
    # x/x50 = 2, m = 3 -> 1 / (1 + 0.5^3) = 8/9
    close(eq.grade_efficiency(2.0, 1.0, 3.0), 8.0 / 9.0)


def test_eq_6_3_3_overall_efficiency_classification():
    close(eq.overall_efficiency_classification([0.5, 1.0], [0.4, 0.6]), 0.8)


def test_eq_6_4_3_limit_loading_exponent():
    close(eq.limit_loading_exponent(0.00375), 0.44860, 1e-4)  # workbook G51
    close(eq.limit_loading_exponent(math.exp(-1.0)), 0.0 - 0.11 + 0.10)


def test_eq_6_4_2_limit_loading_low_co_branch():
    close(eq.limit_loading(1.676, 3.4, 0.00375), 0.0028250, 1e-3)


def test_eq_6_4_1_limit_loading_high_co_branch():
    close(eq.limit_loading(2.0, 4.0, 0.2), 0.025 * 0.5 * (10 * 0.2) ** 0.15)


def test_eq_6_4_1_applies_at_co_equal_to_0_1():
    # (10 co) = 1 at co = 0.1, so coL = 0.025 x50/xmed on either branch
    close(eq.limit_loading(2.0, 4.0, 0.1), 0.025 * 0.5)


def test_eq_6_5_1_overall_efficiency_saltation():
    close(eq.overall_efficiency_saltation(0.01, 0.0025, 0.9), 0.75 + 0.25 * 0.9)
    # at co == coL the result reduces to the classification efficiency
    close(eq.overall_efficiency_saltation(0.01, 0.01, 0.9), 0.9)


def test_eq_6_6_1_pressure_drop_body_matches_book():
    close(eq.pressure_drop_body(0.0071, 0.4567, rho, 12.8466, 18.6, Q), 198.0, 1e-2)


def test_eq_6_6_2_pressure_drop_core_matches_book():
    vx = Q / (math.pi * Rx ** 2)
    close(eq.pressure_drop_core(18.6, vx, rho), 689.0, 1e-2)


def test_eq_6_6_3_pressure_drop_acceleration():
    close(eq.pressure_drop_acceleration(0.00375, 1.2, 10.0, 2.0), 1.00375 * 1.2 * 96.0 / 2.0)
    assert eq.pressure_drop_acceleration(0.0, 1.2, 10.0, 10.0) == 0.0


def test_eq_6_6_4_total_pressure_drop():
    close(eq.pressure_drop_total(198.0, 689.0), 887.0)
    close(eq.pressure_drop_total(198.0, 689.0, 12.0), 899.0)
