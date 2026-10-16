import math

import pytest

from core.units import cfm_to_m3s, fpm_to_ms, in_to_m, m3s_to_cfm, ms_to_fpm, m_to_in
from fluid_systems.duct_flow import (
    round_duct_area,
    round_duct_diameter,
    round_duct_flow,
    round_duct_velocity,
    solve_round_duct,
)


def test_area():
    assert round_duct_area(2.0) == pytest.approx(math.pi)


def test_velocity():
    assert round_duct_velocity(math.pi, 2.0) == pytest.approx(1.0)


def test_diameter():
    assert round_duct_diameter(math.pi, 1.0) == pytest.approx(2.0)


def test_flow():
    assert round_duct_flow(2.0, 1.0) == pytest.approx(math.pi)


def test_round_trip_all_directions():
    base = solve_round_duct(flow=0.75, diameter=0.4)
    for kwargs in (
        {"flow": base.flow, "diameter": base.diameter},
        {"flow": base.flow, "velocity": base.velocity},
        {"diameter": base.diameter, "velocity": base.velocity},
    ):
        r = solve_round_duct(**kwargs)
        assert r.flow == pytest.approx(base.flow, rel=1e-12)
        assert r.diameter == pytest.approx(base.diameter, rel=1e-12)
        assert r.velocity == pytest.approx(base.velocity, rel=1e-12)
        assert r.area == pytest.approx(base.area, rel=1e-12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"flow": 1.0},
        {"flow": 1.0, "diameter": 1.0, "velocity": 1.0},
        {"flow": 0.0, "diameter": 1.0},
        {"flow": 1.0, "velocity": -2.0},
        {"diameter": float("nan"), "velocity": 1.0},
        {"diameter": float("inf"), "velocity": 1.0},
    ],
)
def test_invalid_input(kwargs):
    with pytest.raises(ValueError):
        solve_round_duct(**kwargs)


def test_workbook_case_1():
    r = solve_round_duct(flow=cfm_to_m3s(2700), diameter=in_to_m(14))
    assert round(ms_to_fpm(r.velocity)) == 2526


def test_workbook_case_2():
    r = solve_round_duct(flow=cfm_to_m3s(3500), velocity=fpm_to_ms(4000))
    assert round(m_to_in(r.diameter), 1) == 12.7


def test_workbook_case_3():
    r = solve_round_duct(diameter=in_to_m(7), velocity=fpm_to_ms(4000))
    assert round(m3s_to_cfm(r.flow)) == 1069
