"""Tests for the Donaldson DLMC entries in core.enclosure_catalog."""

import pytest

from core.enclosure_catalog import (
    list_families, list_models, list_hoppers, get_model, get_segments,
)
from core.geometry import (
    enclosure_volume_and_length, vol_cuboid, vol_truncated_rect_pyramid,
)

IN = 0.0254  # test oracle only; the catalog itself converts via core.units


def test_dlmc_is_only_family():
    assert list_families() == ["DLMC"]


def test_dlmc_models():
    models = list_models("DLMC")
    assert len(models) == 16
    assert models[0] == "DLMC 1/2/15" and models[-1] == "DLMC 4/8/15"
    # 7-high models wait on a body height that the sheet leaves blank
    assert "DLMC 1/7/15" not in models and "DLMC 3/7/15" not in models


@pytest.mark.parametrize("model, expected", [
    ("DLMC 1/3/15", ["single outlet"]),
    ("DLMC 2/6/15", ["dual outlet", "single outlet", "through hopper"]),
    ("DLMC 3/8/15", ["triple outlet", "single outlet", "through hopper"]),
    ("DLMC 4/5/15", ["four outlets", "dual outlet", "through hopper"]),
])
def test_hopper_options_by_width(model, expected):
    assert list_hoppers("DLMC", model) == expected


@pytest.mark.parametrize("model", list_models("DLMC"))
def test_hoppers_tile_under_body(model):
    body = get_model("DLMC", model).body
    for hopper in list_hoppers("DLMC", model):
        seg = get_segments("DLMC", model, hopper)[1]
        assert seg.get("cols", 1) * seg["A"] == pytest.approx(body["a"], rel=1e-6)
        assert seg["B"] == pytest.approx(body["b"], rel=1e-6)
        assert seg.get("rows", 1) == 1


def test_volume_2_4_dual_outlet():
    # Hand calc from the sheet values (inches): body 78.95218 x 68.8421 x 123.57,
    # two hoppers 39.47609 x 68.8421 -> 9.88 x 9.88, h 60.
    body = vol_cuboid(78.95218 * IN, 68.8421 * IN, 123.57 * IN)
    hopper = vol_truncated_rect_pyramid(39.47609 * IN, 68.8421 * IN, 9.88 * IN, 9.88 * IN, 60 * IN)
    V, L = enclosure_volume_and_length(get_segments("DLMC", "DLMC 2/4/15", "dual outlet"))
    assert V == pytest.approx(body + 2 * hopper, rel=1e-9)
    assert L == pytest.approx((123.57 + 60) * IN, rel=1e-9)


def test_get_segments_returns_copies():
    segs = get_segments("DLMC", "DLMC 1/2/15", "single outlet")
    segs[0]["a"] = 999.0
    segs[1]["h"] = 999.0
    fresh = get_segments("DLMC", "DLMC 1/2/15", "single outlet")
    assert fresh[0]["a"] != 999.0 and fresh[1]["h"] != 999.0
