import pytest

import core.units as units
from core.units import (
    atm_to_pa,
    bar_to_pa,
    cfm_to_m3h,
    cfm_to_m3s,
    convert_pressure,
    fpm_to_ms,
    inh2o_to_inhg,
    inh2o_to_pa,
    inh2o_to_psi,
    m3h_to_cfm,
    m3h_to_m3s,
    ms_to_fpm,
)
from core.utils import u


def test_case_4_flow():
    assert round(cfm_to_m3h(3400)) == 5777
    assert round(cfm_to_m3s(3400), 3) == 1.605


def test_case_5_flow():
    assert round(m3h_to_cfm(72000)) == 42378
    assert round(m3h_to_m3s(72000), 3) == 20.000


def test_case_6_velocity():
    assert round(fpm_to_ms(4400), 2) == 22.35


def test_case_7_velocity():
    assert round(ms_to_fpm(22.68)) == 4465


def test_case_8_pressure_bare_inch_h2o():
    # Workbook (60 °F water) shows 16.90 / 8.30 / 57224; bare inch_H2O is intended.
    assert round(inh2o_to_inhg(230), 2) == 16.92
    assert round(inh2o_to_psi(230), 2) == 8.31
    assert round(inh2o_to_pa(230)) == 57290


def test_bar_and_atm():
    assert bar_to_pa(1) == pytest.approx(100000)
    assert atm_to_pa(1) == pytest.approx(101325)


def test_inch_hg_is_32f():
    assert u.Quantity(1, "inch_Hg").to("Pa").magnitude == pytest.approx(
        u.Quantity(1, "inch_Hg_32F").to("Pa").magnitude
    )


def test_convert_pressure_rejects_unknown_unit():
    with pytest.raises(ValueError):
        convert_pressure(1, "kpa", "pa")
    assert convert_pressure(1, "bar", "pa") == pytest.approx(100000)


def test_all_names_defined():
    assert all(hasattr(units, name) for name in units.__all__)


def test_length_ft_in_um():
    assert units.ft_to_m(1) == pytest.approx(0.3048, rel=1e-12)
    assert units.in_to_mm(1) == pytest.approx(25.4, rel=1e-12)
    assert units.in_to_m(1) == pytest.approx(0.0254, rel=1e-12)
    assert units.mm_to_in(25.4) == pytest.approx(1.0, rel=1e-12)
    assert units.m_to_um(1e-6) == pytest.approx(1.0, rel=1e-12)
    assert units.um_to_m(25.58) == pytest.approx(25.58e-6, rel=1e-12)
    assert units.m_to_ft(units.ft_to_m(12.5)) == pytest.approx(12.5, rel=1e-12)


def test_mass_flow():
    assert units.kgs_to_kgh(1) == pytest.approx(3600, rel=1e-12)
    assert units.kgh_to_kgs(units.kgs_to_kgh(0.37)) == pytest.approx(0.37, rel=1e-12)


def test_concentration():
    assert units.kgm3_to_mgm3(1) == pytest.approx(1e6, rel=1e-12)
    assert units.mgm3_to_kgm3(units.kgm3_to_mgm3(4.6e-5)) == pytest.approx(4.6e-5, rel=1e-12)
