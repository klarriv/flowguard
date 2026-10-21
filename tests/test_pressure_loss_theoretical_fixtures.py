"""Sanity checks for the PLT-01 workbook regression fixtures.

These check that each fixture is internally consistent (the sheet's own bookkeeping), so a bad
extraction is caught. They do not test any library code.
"""
import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pressure_loss_theoretical"
FIXTURES = sorted(FIXTURE_DIR.glob("*.json"))

TERMS = (
    "delta_p_A_solids_acceleration_Pa",
    "delta_p_L_gas_friction_Pa",
    "delta_p_Z_solids_friction_Pa",
    "delta_p_G_gas_elevation_Pa",
    "delta_p_G_solids_elevation_Pa",
    "delta_p_misc_Pa",
)


def _load(path):
    with open(path) as f:
        return json.load(f)


def test_fixtures_present():
    names = {p.name for p in FIXTURES}
    assert {"vacuum_with_solids.json", "pressure_with_solids.json"} <= names


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_section_terms_sum_to_section_total(path):
    for s in _load(path)["sections"]:
        total = sum(s[t] or 0.0 for t in TERMS)
        assert s["delta_p_section_Pa"] == pytest.approx(total, rel=1e-12)


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_pressure_and_state_chain(path):
    data = _load(path)
    secs = data["sections"]
    assert secs[0]["p_in_Pa"] == pytest.approx(data["inputs"]["p_inlet_Pa"], rel=1e-12)
    assert secs[0]["v_in_m_s"] == pytest.approx(data["inputs"]["v_inlet_m_s"], rel=1e-12)
    cumulative = 0.0
    for prev, cur in zip([None] + secs[:-1], secs):
        assert cur["p_out_Pa"] == pytest.approx(cur["p_in_Pa"] - cur["delta_p_section_Pa"], rel=1e-12)
        # velocity follows density at constant mass flow and area
        assert cur["v_out_m_s"] == pytest.approx(cur["v_in_m_s"] * cur["rho_in_kg_m3"] / cur["rho_out_kg_m3"], rel=1e-9)
        if prev is not None:
            for a, b in (("p_in_Pa", "p_out_Pa"), ("v_in_m_s", "v_out_m_s"), ("rho_in_kg_m3", "rho_out_kg_m3")):
                assert cur[a] == pytest.approx(prev[b], rel=1e-12)
        cumulative += cur["delta_p_section_Pa"]
        assert cur["delta_p_cumulative_Pa"] == pytest.approx(cumulative, rel=1e-12)


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_totals_match_sections(path):
    data = _load(path)
    secs = data["sections"]
    totals = data["totals"]
    assert totals["delta_p_total_Pa"] == pytest.approx(sum(s["delta_p_section_Pa"] for s in secs), rel=1e-12)
    assert totals["delta_p_L_Pa"] == pytest.approx(sum(s["delta_p_L_gas_friction_Pa"] for s in secs), rel=1e-12)
    assert totals["p_outlet_Pa"] == pytest.approx(secs[-1]["p_out_Pa"], rel=1e-12)
    assert data["inputs"]["p_inlet_Pa"] - totals["p_outlet_Pa"] == pytest.approx(totals["delta_p_total_Pa"], rel=1e-9)
