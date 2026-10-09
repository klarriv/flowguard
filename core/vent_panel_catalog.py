"""
Vent panel catalog.

Provides nominal-size flameless/mechanical vent panel data (opening
dimensions, vent area, panel density) grouped by manufacturer and panel
type, plus the panel-count selection helper used by the Selection section
of the Dust Vent page.

Catalog data is sourced from manufacturer datasheets and embedded here as
literals (areas converted cm² → m²; panel density is already kg/m²), the
same convention used by core.enclosure_catalog for the Donaldson catalog.
Nominal opening dimensions are stored as raw millimetre width/height so
both metric and imperial display strings are derived consistently rather
than transcribed by hand.
"""

import math
from dataclasses import dataclass
from typing import Optional


def _fmt_mm(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:g}"


def _mm_to_in(v: float) -> int:
    """Nearest whole inch, rounding .5 up (not Python's banker's rounding)."""
    return math.floor(v / 25.4 + 0.5)


@dataclass
class VentPanel:
    """
    A single catalog vent panel size.

    `model` is the manufacturer's product-line code from the source
    datasheet (e.g. "VL", "VD", "VD-HV" for Vigilex; "KER", "GE" for IEP
    Technologies; "CV", "CV-S", "CV-S-HV" for Fike) — one code per
    `panel_type`. `panel_type` is the friendlier name ("Standard",
    "Vacuum", "High Vacuum") used for filtering in the UI.

    `panel_density_kgm2` is optional — not every manufacturer publishes
    areal mass/weight (IEP and Fike don't, as of the sources used to build
    this catalog); `None` means the §8.3 panel-inertia correction can't be
    evaluated for that panel until a real figure is obtained.

    `shape` is `"rectangular"` (default) or `"round"`. Round panels (e.g.
    IEP GE Round) store their diameter in both `w_mm` and `h_mm` — this
    keeps `surf_m2`-based engineering math (panel count, effective area)
    completely unaffected, since neither reads `w_mm`/`h_mm`; `shape` only
    changes how `nominal_metric`/`nominal_imperial` are displayed.

    `rated_vacuum_mbar` is the panel's rated vacuum resistance at ~100 mbar
    burst pressure (the de facto industry-standard Pstat), where published.
    `None` where the manufacturer doesn't publish (or publish unambiguously)
    a vacuum rating for that panel/size.

    `exterior_w_mm`/`exterior_h_mm` are the panel's exterior/frame footprint
    (larger than the nominal vent opening) — `None` where not published.
    """
    manufacturer: str
    panel_type: str
    model: str
    w_mm: float
    h_mm: float
    surf_m2: float
    panel_density_kgm2: Optional[float] = None
    shape: str = "rectangular"
    rated_vacuum_mbar: Optional[float] = None
    exterior_w_mm: Optional[float] = None
    exterior_h_mm: Optional[float] = None

    @property
    def nominal_metric(self) -> str:
        if self.shape == "round":
            return f"⌀{_fmt_mm(self.w_mm)} mm"
        return f"{_fmt_mm(self.w_mm)} x {_fmt_mm(self.h_mm)} mm"

    @property
    def nominal_imperial(self) -> str:
        if self.shape == "round":
            return f"⌀{_mm_to_in(self.w_mm)} in"
        return f"{_mm_to_in(self.w_mm)} x {_mm_to_in(self.h_mm)} in"

    @property
    def exterior_metric(self) -> str:
        if self.exterior_w_mm is None or self.exterior_h_mm is None:
            return "—"
        if self.shape == "round":
            return f"⌀{_fmt_mm(self.exterior_w_mm)} mm"
        return f"{_fmt_mm(self.exterior_w_mm)} x {_fmt_mm(self.exterior_h_mm)} mm"

    @property
    def exterior_imperial(self) -> str:
        if self.exterior_w_mm is None or self.exterior_h_mm is None:
            return "—"
        if self.shape == "round":
            return f"⌀{_mm_to_in(self.exterior_w_mm)} in"
        return f"{_mm_to_in(self.exterior_w_mm)} x {_mm_to_in(self.exterior_h_mm)} in"

    @property
    def is_stocked(self) -> bool:
        return (self.w_mm, self.h_mm) in STOCKED_SIZES_MM.get(self.manufacturer, set())


# Nominal (width, height) sizes normally kept in stock, keyed by
# manufacturer — the sizes actually offered still vary by panel type (e.g.
# not every stocked size exists in High Vacuum), so this is intersected
# against each type's real catalog, not a fixed list per type.
STOCKED_SIZES_MM: dict[str, set[tuple[float, float]]] = {
    "Vigilex": {
        (170, 470), (270, 458), (305, 457), (300, 500), (305, 610), (350, 650),
        (490, 590), (610, 610), (457, 890), (586, 920), (610, 914), (920, 920),
        (915, 1118), (1130, 1130),
    },
    # IEP Technologies "stock" sizes per MC-518W Rev AL (2016), cross-
    # referenced against the live-website dimension tables by matching
    # inch-nominal labels to their exact mm row (not a raw in->mm
    # conversion, which doesn't reliably land on the same row IEP's own
    # engineering tables use). MC-518W's "24 x 36" (both GE and KER) has no
    # exact match in the current website tables and is omitted rather than
    # guessed; MC-518W's KER "12 x 24" matches two different mm rows in the
    # website table (300x600 and 300x620) and is omitted for the same
    # reason — ambiguous, not resolvable without guessing.
    "IEP": {
        # GE stock sizes: 12x24->300x620, 24x24->610x610, 18x35->457x890,
        # 36x36->920x920, 36x44->915x1118, 44x44->1130x1130
        (300, 620), (610, 610), (457, 890), (920, 920), (915, 1118), (1130, 1130),
        # KER stock sizes: 18x35->457x890, 36x44->915x1118 (12x24 ambiguous,
        # 24x36 no match - both omitted, see comment above)
        (457, 890), (915, 1118),
    },
    # Fike "(st)"/"*"-marked stock sizes per the CV/CV-S/CV-S-HV datasheets.
    "Fike": {
        # CV (metric datasheet "(st)" sizes, native mm, no conversion)
        (625, 625), (500, 1000), (566, 900), (625, 1110), (900, 900),
        (1000, 1000), (1110, 1110),
        # CV-S (imperial datasheet "*" sizes) - exact in*25.4 mm, matching
        # how the CV-S catalog entries below store their nominal size
        # (Fike only publishes CV-S nominal sizes in inches, no separate mm
        # table to cross-reference against, unlike IEP above)
        (304.8, 457.2), (457.2, 889.0), (609.6, 609.6), (609.6, 914.4),
        (914.4, 914.4), (914.4, 1117.6),
    },
}


VENT_PANEL_CATALOG: dict[str, dict[str, list[VentPanel]]] = {
    "Vigilex": {
        "Standard": [
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=110, h_mm=290, surf_m2=0.031, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=174, exterior_h_mm=354),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=150, h_mm=600, surf_m2=0.0885, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=230, exterior_h_mm=680),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=250, exterior_h_mm=550),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.925, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=300, exterior_h_mm=500),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=310, exterior_h_mm=310),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=310, exterior_h_mm=386),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=327, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=350, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=380, exterior_h_mm=580),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=300, h_mm=600, surf_m2=0.178, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=350, exterior_h_mm=650),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=386, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=386, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=319, h_mm=765, surf_m2=0.2425, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=405, exterior_h_mm=850),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=340, h_mm=385, surf_m2=0.129, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=404, exterior_h_mm=449),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=340, h_mm=440, surf_m2=0.143, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=404, exterior_h_mm=504),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=430, exterior_h_mm=730),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=460, exterior_h_mm=740),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=390, h_mm=620, surf_m2=0.2395, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=470, exterior_h_mm=700),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=400, h_mm=400, surf_m2=0.158, panel_density_kgm2=3.925, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=480, exterior_h_mm=480),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=420, h_mm=520, surf_m2=0.2165, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=500, exterior_h_mm=600),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=420, h_mm=920, surf_m2=0.3835, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=500, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=537, exterior_h_mm=970),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=550, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=480, h_mm=680, surf_m2=0.326, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=570, exterior_h_mm=770),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=520, surf_m2=0.268, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=600, exterior_h_mm=600),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=620, surf_m2=0.32, panel_density_kgm2=3.925, rated_vacuum_mbar=50, exterior_w_mm=600, exterior_h_mm=700),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=1020, surf_m2=0.527, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=600, exterior_h_mm=1100),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=580, h_mm=1180, surf_m2=0.6805, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=670, exterior_h_mm=1270),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=600, h_mm=600, surf_m2=0.3576, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=914, surf_m2=0.5545, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=1118, surf_m2=0.6785, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=690, exterior_h_mm=1198),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=620, h_mm=820, surf_m2=0.5055, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=629, h_mm=1004, surf_m2=0.629, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=645, h_mm=645, surf_m2=0.413, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=645, h_mm=1130, surf_m2=0.725, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=735, exterior_h_mm=1220),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=680, h_mm=680, surf_m2=0.4595, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=770, exterior_h_mm=770),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=720, h_mm=1020, surf_m2=0.7305, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=800, exterior_h_mm=1100),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=780, h_mm=780, surf_m2=0.605, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=870, exterior_h_mm=870),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=780, h_mm=1180, surf_m2=0.916, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=870, exterior_h_mm=1270),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=800, h_mm=800, surf_m2=0.6365, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=800, h_mm=1000, surf_m2=0.796, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=890, exterior_h_mm=1090),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=880, h_mm=880, surf_m2=0.7705, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=970, exterior_h_mm=970),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=915, h_mm=1118, surf_m2=1.02, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=996, exterior_h_mm=1198),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=920, h_mm=920, surf_m2=0.8425, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=980, h_mm=980, surf_m2=0.956, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1070, exterior_h_mm=1070),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=986, h_mm=986, surf_m2=0.968, panel_density_kgm2=6.28, rated_vacuum_mbar=50),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1020, h_mm=1020, surf_m2=1.036, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1100, exterior_h_mm=1100),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1080, h_mm=1080, surf_m2=1.162, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1170, exterior_h_mm=1170),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1130, h_mm=1130, surf_m2=1.272, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1220, exterior_h_mm=1220),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1180, h_mm=1180, surf_m2=1.3875, panel_density_kgm2=6.28, rated_vacuum_mbar=50, exterior_w_mm=1270, exterior_h_mm=1270),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=200, h_mm=200, surf_m2=0.031, shape="round", rated_vacuum_mbar=50, exterior_w_mm=268, exterior_h_mm=268),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=250, h_mm=250, surf_m2=0.048, shape="round", rated_vacuum_mbar=50, exterior_w_mm=330, exterior_h_mm=330),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=300, h_mm=300, surf_m2=0.07, shape="round", rated_vacuum_mbar=50, exterior_w_mm=390, exterior_h_mm=390),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=350, h_mm=350, surf_m2=0.0955, shape="round", rated_vacuum_mbar=50, exterior_w_mm=424, exterior_h_mm=424),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=400, h_mm=400, surf_m2=0.124, shape="round", rated_vacuum_mbar=50, exterior_w_mm=473, exterior_h_mm=473),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=450, h_mm=450, surf_m2=0.157, shape="round", rated_vacuum_mbar=50, exterior_w_mm=545, exterior_h_mm=545),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=500, h_mm=500, surf_m2=0.195, shape="round", rated_vacuum_mbar=50, exterior_w_mm=574, exterior_h_mm=574),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=600, h_mm=600, surf_m2=0.2805, shape="round", rated_vacuum_mbar=50, exterior_w_mm=646, exterior_h_mm=646),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=700, h_mm=700, surf_m2=0.3815, shape="round", rated_vacuum_mbar=50, exterior_w_mm=790, exterior_h_mm=790),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=750, h_mm=750, surf_m2=0.4335, shape="round", rated_vacuum_mbar=50, exterior_w_mm=842, exterior_h_mm=842),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=800, h_mm=800, surf_m2=0.501, shape="round", rated_vacuum_mbar=50, exterior_w_mm=880, exterior_h_mm=880),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=900, h_mm=900, surf_m2=0.6325, shape="round", rated_vacuum_mbar=50, exterior_w_mm=980, exterior_h_mm=980),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=980, h_mm=980, surf_m2=0.7445, shape="round", rated_vacuum_mbar=50, exterior_w_mm=1070, exterior_h_mm=1070),
        ],
        "Vacuum": [
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=150, h_mm=600, surf_m2=0.0885, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=230, exterior_h_mm=680),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=250, exterior_h_mm=550),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=285, exterior_h_mm=370),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=300, exterior_h_mm=500),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=310, exterior_h_mm=310),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=310, exterior_h_mm=386),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=327, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=350, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=386, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=6.28, rated_vacuum_mbar=200, exterior_w_mm=380, exterior_h_mm=580),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=6.28, rated_vacuum_mbar=200, exterior_w_mm=386, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=340, h_mm=385, surf_m2=0.129, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=404, exterior_h_mm=449),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=340, h_mm=440, surf_m2=0.148, panel_density_kgm2=3.925, rated_vacuum_mbar=200, exterior_w_mm=404, exterior_h_mm=504),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=430, exterior_h_mm=730),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=460, exterior_h_mm=740),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=480, exterior_h_mm=480),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=537, exterior_h_mm=970),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=6.28, rated_vacuum_mbar=200, exterior_w_mm=550, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=6.28, rated_vacuum_mbar=200, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=6.28, rated_vacuum_mbar=200, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=525, h_mm=668, surf_m2=0.348, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=630, exterior_h_mm=765),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=558, h_mm=914, surf_m2=0.5109, panel_density_kgm2=6.28, rated_vacuum_mbar=200),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=914, surf_m2=0.5545, panel_density_kgm2=9.42, rated_vacuum_mbar=200),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=1118, surf_m2=0.6785, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=690, exterior_h_mm=1198),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=645, h_mm=645, surf_m2=0.413, panel_density_kgm2=9.42, rated_vacuum_mbar=200, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=645, h_mm=1130, surf_m2=0.725, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=735, exterior_h_mm=1220),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=915, h_mm=1118, surf_m2=1.02, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=996, exterior_h_mm=1198),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=920, h_mm=920, surf_m2=0.8425, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=980, h_mm=980, surf_m2=0.956, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=1070, exterior_h_mm=1070),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=1020, h_mm=1020, surf_m2=1.036, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=1100, exterior_h_mm=1100),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=1130, h_mm=1130, surf_m2=1.272, panel_density_kgm2=11.775, rated_vacuum_mbar=200, exterior_w_mm=1220, exterior_h_mm=1220),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=200, h_mm=200, surf_m2=0.031, shape="round", rated_vacuum_mbar=200, exterior_w_mm=268, exterior_h_mm=268),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=250, h_mm=250, surf_m2=0.048, shape="round", rated_vacuum_mbar=200, exterior_w_mm=330, exterior_h_mm=330),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=300, h_mm=300, surf_m2=0.0685, shape="round", rated_vacuum_mbar=200, exterior_w_mm=390, exterior_h_mm=390),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=350, h_mm=350, surf_m2=0.093, shape="round", rated_vacuum_mbar=200, exterior_w_mm=424, exterior_h_mm=424),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=400, h_mm=400, surf_m2=0.124, shape="round", rated_vacuum_mbar=200, exterior_w_mm=473, exterior_h_mm=473),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=450, h_mm=450, surf_m2=0.157, shape="round", rated_vacuum_mbar=200, exterior_w_mm=545, exterior_h_mm=545),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=500, h_mm=500, surf_m2=0.195, shape="round", rated_vacuum_mbar=200, exterior_w_mm=574, exterior_h_mm=574),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=600, h_mm=600, surf_m2=0.279, shape="round", rated_vacuum_mbar=200, exterior_w_mm=676, exterior_h_mm=676),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=700, h_mm=700, surf_m2=0.3815, shape="round", rated_vacuum_mbar=200, exterior_w_mm=790, exterior_h_mm=790),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=750, h_mm=750, surf_m2=0.438, shape="round", rated_vacuum_mbar=200, exterior_w_mm=842, exterior_h_mm=842),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=800, h_mm=800, surf_m2=0.4985, shape="round", rated_vacuum_mbar=200, exterior_w_mm=880, exterior_h_mm=880),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=900, h_mm=900, surf_m2=0.6325, shape="round", rated_vacuum_mbar=200, exterior_w_mm=980, exterior_h_mm=980),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=980, h_mm=980, surf_m2=0.75, shape="round", rated_vacuum_mbar=200, exterior_w_mm=1070, exterior_h_mm=1070),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=1200, h_mm=1200, surf_m2=1.1165, shape="round", rated_vacuum_mbar=200, exterior_w_mm=1290, exterior_h_mm=1290),
        ],
        "High Vacuum": [
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=250, exterior_h_mm=550),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.93, rated_vacuum_mbar=500),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=6.28, rated_vacuum_mbar=500, exterior_w_mm=300, exterior_h_mm=500),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=6.28, rated_vacuum_mbar=500, exterior_w_mm=310, exterior_h_mm=310),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=6.28, rated_vacuum_mbar=500, exterior_w_mm=310, exterior_h_mm=386),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=327, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=350, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=380, exterior_h_mm=580),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=386, exterior_h_mm=538),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=386, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=340, h_mm=440, surf_m2=0.148, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=404, exterior_h_mm=504),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=430, exterior_h_mm=730),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=460, exterior_h_mm=740),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=9.42, rated_vacuum_mbar=500, exterior_w_mm=480, exterior_h_mm=480),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=550, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=537, exterior_h_mm=970),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=11.78, rated_vacuum_mbar=500, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=200, h_mm=200, surf_m2=0.031, shape="round", rated_vacuum_mbar=500, exterior_w_mm=268, exterior_h_mm=268),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=250, h_mm=250, surf_m2=0.048, shape="round", rated_vacuum_mbar=500, exterior_w_mm=330, exterior_h_mm=330),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=300, h_mm=300, surf_m2=0.0685, shape="round", rated_vacuum_mbar=500, exterior_w_mm=390, exterior_h_mm=390),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=350, h_mm=350, surf_m2=0.093, shape="round", rated_vacuum_mbar=500, exterior_w_mm=424, exterior_h_mm=424),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=400, h_mm=400, surf_m2=0.124, shape="round", rated_vacuum_mbar=500, exterior_w_mm=473, exterior_h_mm=473),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=450, h_mm=450, surf_m2=0.157, shape="round", rated_vacuum_mbar=500, exterior_w_mm=545, exterior_h_mm=545),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=500, h_mm=500, surf_m2=0.195, shape="round", rated_vacuum_mbar=500, exterior_w_mm=574, exterior_h_mm=574),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=600, h_mm=600, surf_m2=0.279, shape="round", rated_vacuum_mbar=500, exterior_w_mm=676, exterior_h_mm=676),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=700, h_mm=700, surf_m2=0.3815, shape="round", rated_vacuum_mbar=500, exterior_w_mm=790, exterior_h_mm=790),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=750, h_mm=750, surf_m2=0.438, shape="round", rated_vacuum_mbar=500, exterior_w_mm=842, exterior_h_mm=842),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=800, h_mm=800, surf_m2=0.4985, shape="round", rated_vacuum_mbar=500, exterior_w_mm=880, exterior_h_mm=880),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=900, h_mm=900, surf_m2=0.6325, shape="round", rated_vacuum_mbar=500, exterior_w_mm=980, exterior_h_mm=980),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=980, h_mm=980, surf_m2=0.75, shape="round", rated_vacuum_mbar=500, exterior_w_mm=1070, exterior_h_mm=1070),
        ],
    },
    "IEP": {
        "Standard": [
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=110, h_mm=290, surf_m2=0.0300, rated_vacuum_mbar=50, exterior_w_mm=170, exterior_h_mm=350),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=229, h_mm=229, surf_m2=0.0510, rated_vacuum_mbar=50, exterior_w_mm=309, exterior_h_mm=309),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=205, h_mm=290, surf_m2=0.0580, rated_vacuum_mbar=50, exterior_w_mm=285, exterior_h_mm=370),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=229, h_mm=305, surf_m2=0.0680, rated_vacuum_mbar=50, exterior_w_mm=309, exterior_h_mm=385),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=150, h_mm=600, surf_m2=0.0880, rated_vacuum_mbar=50, exterior_w_mm=230, exterior_h_mm=680),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=220, h_mm=420, surf_m2=0.0900, rated_vacuum_mbar=50, exterior_w_mm=300, exterior_h_mm=500),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=315, h_mm=410, surf_m2=0.1250, rated_vacuum_mbar=50, exterior_w_mm=365, exterior_h_mm=460),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=340, h_mm=385, surf_m2=0.1280, rated_vacuum_mbar=50, exterior_w_mm=400, exterior_h_mm=445),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=305, h_mm=457, surf_m2=0.1380, rated_vacuum_mbar=50, exterior_w_mm=385, exterior_h_mm=537),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=247, h_mm=610, surf_m2=0.1450, rated_vacuum_mbar=50, exterior_w_mm=327, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=340, h_mm=440, surf_m2=0.1480, rated_vacuum_mbar=50, exterior_w_mm=400, exterior_h_mm=500),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=400, h_mm=400, surf_m2=0.1550, rated_vacuum_mbar=50, exterior_w_mm=500, exterior_h_mm=500),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=410, h_mm=410, surf_m2=0.1650, rated_vacuum_mbar=50, exterior_w_mm=490, exterior_h_mm=490),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=300, h_mm=600, surf_m2=0.1800, rated_vacuum_mbar=50, exterior_w_mm=350, exterior_h_mm=650),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=300, h_mm=620, surf_m2=0.1860, rated_vacuum_mbar=50, exterior_w_mm=380, exterior_h_mm=700),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=320, h_mm=640, surf_m2=0.2000, rated_vacuum_mbar=50, exterior_w_mm=380, exterior_h_mm=700),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=319, h_mm=765, surf_m2=0.2350, rated_vacuum_mbar=50, exterior_w_mm=399, exterior_h_mm=845),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=490, h_mm=490, surf_m2=0.2370, rated_vacuum_mbar=50, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=375, h_mm=655, surf_m2=0.2400, rated_vacuum_mbar=50, exterior_w_mm=455, exterior_h_mm=735),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=390, h_mm=620, surf_m2=0.2400, rated_vacuum_mbar=50, exterior_w_mm=470, exterior_h_mm=700),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=445, h_mm=597, surf_m2=0.2600, rated_vacuum_mbar=50, exterior_w_mm=525, exterior_h_mm=677),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=470, h_mm=610, surf_m2=0.2800, rated_vacuum_mbar=50, exterior_w_mm=550, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=490, h_mm=590, surf_m2=0.2850, rated_vacuum_mbar=50, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=420, h_mm=770, surf_m2=0.3200, rated_vacuum_mbar=50, exterior_w_mm=500, exterior_h_mm=850),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=247, h_mm=1345, surf_m2=0.3300, rated_vacuum_mbar=50, exterior_w_mm=327, exterior_h_mm=1425),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=525, h_mm=668, surf_m2=0.3400, rated_vacuum_mbar=50, exterior_w_mm=645, exterior_h_mm=788),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=600, h_mm=600, surf_m2=0.3600, rated_vacuum_mbar=50, exterior_w_mm=650, exterior_h_mm=650),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=610, h_mm=610, surf_m2=0.3650, rated_vacuum_mbar=50, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=247, h_mm=1645, surf_m2=0.4050, rated_vacuum_mbar=50, exterior_w_mm=327, exterior_h_mm=1725),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=457, h_mm=890, surf_m2=0.4050, rated_vacuum_mbar=50, exterior_w_mm=537, exterior_h_mm=970),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=620, h_mm=670, surf_m2=0.4100, rated_vacuum_mbar=50, exterior_w_mm=680, exterior_h_mm=730),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=645, h_mm=645, surf_m2=0.4100, rated_vacuum_mbar=50, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=653, h_mm=653, surf_m2=0.4200, rated_vacuum_mbar=50, exterior_w_mm=733, exterior_h_mm=733),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=669, h_mm=669, surf_m2=0.4350, rated_vacuum_mbar=50, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=630, h_mm=730, surf_m2=0.4550, rated_vacuum_mbar=50, exterior_w_mm=710, exterior_h_mm=810),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=620, h_mm=820, surf_m2=0.5000, rated_vacuum_mbar=50, exterior_w_mm=675, exterior_h_mm=875),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=520, h_mm=1020, surf_m2=0.5250, rated_vacuum_mbar=50, exterior_w_mm=600, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=586, h_mm=920, surf_m2=0.5350, rated_vacuum_mbar=50, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=500, h_mm=1100, surf_m2=0.5400, rated_vacuum_mbar=50, exterior_w_mm=580, exterior_h_mm=1180),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=750, h_mm=750, surf_m2=0.5600, rated_vacuum_mbar=50, exterior_w_mm=830, exterior_h_mm=830),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=420, h_mm=1420, surf_m2=0.5950, rated_vacuum_mbar=50, exterior_w_mm=500, exterior_h_mm=1500),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=629, h_mm=1004, surf_m2=0.6000, rated_vacuum_mbar=50, exterior_w_mm=689, exterior_h_mm=1064),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=750, h_mm=840, surf_m2=0.6250, rated_vacuum_mbar=50, exterior_w_mm=830, exterior_h_mm=920),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=800, h_mm=800, surf_m2=0.6400, rated_vacuum_mbar=50, exterior_w_mm=850, exterior_h_mm=850),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=801, h_mm=801, surf_m2=0.6400, rated_vacuum_mbar=50, exterior_w_mm=880, exterior_h_mm=880),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=500, h_mm=1350, surf_m2=0.6700, rated_vacuum_mbar=50, exterior_w_mm=580, exterior_h_mm=1430),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=610, h_mm=1118, surf_m2=0.6750, rated_vacuum_mbar=50, exterior_w_mm=690, exterior_h_mm=1198),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=645, h_mm=1130, surf_m2=0.7280, rated_vacuum_mbar=50, exterior_w_mm=725, exterior_h_mm=1210),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=720, h_mm=1020, surf_m2=0.7300, rated_vacuum_mbar=50, exterior_w_mm=800, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=920, h_mm=920, surf_m2=0.8400, rated_vacuum_mbar=50, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=940, h_mm=940, surf_m2=0.8800, rated_vacuum_mbar=50, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=970, h_mm=970, surf_m2=0.9400, rated_vacuum_mbar=50, exterior_w_mm=1050, exterior_h_mm=1050),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1000, h_mm=1000, surf_m2=1.0000, rated_vacuum_mbar=50, exterior_w_mm=1080, exterior_h_mm=1080),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1000, h_mm=1000, surf_m2=1.0000, rated_vacuum_mbar=50, exterior_w_mm=1050, exterior_h_mm=1050),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=586, h_mm=1727, surf_m2=1.0000, rated_vacuum_mbar=50, exterior_w_mm=666, exterior_h_mm=1807),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=915, h_mm=1118, surf_m2=1.0000, rated_vacuum_mbar=50, exterior_w_mm=995, exterior_h_mm=1198),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1020, h_mm=1020, surf_m2=1.0400, rated_vacuum_mbar=50, exterior_w_mm=1100, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=790, h_mm=1340, surf_m2=1.0500, rated_vacuum_mbar=50, exterior_w_mm=870, exterior_h_mm=1420),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=720, h_mm=1670, surf_m2=1.2000, rated_vacuum_mbar=50, exterior_w_mm=800, exterior_h_mm=1750),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1130, h_mm=1130, surf_m2=1.2500, rated_vacuum_mbar=50, exterior_w_mm=1220, exterior_h_mm=1220),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=920, h_mm=1380, surf_m2=1.2500, rated_vacuum_mbar=50, exterior_w_mm=1000, exterior_h_mm=1460),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=940, h_mm=1440, surf_m2=1.3500, rated_vacuum_mbar=50, exterior_w_mm=1000, exterior_h_mm=1500),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1130, h_mm=1520, surf_m2=1.7150, rated_vacuum_mbar=50, exterior_w_mm=1220, exterior_h_mm=1610),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1130, h_mm=1727, surf_m2=1.9200, rated_vacuum_mbar=50, exterior_w_mm=1230, exterior_h_mm=1827),
            VentPanel(manufacturer="IEP", panel_type="Standard", model="KER", w_mm=1000, h_mm=2000, surf_m2=1.9500, rated_vacuum_mbar=50, exterior_w_mm=1080, exterior_h_mm=2080),
        ],
        "Vacuum": [
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=229, h_mm=229, surf_m2=0.0510, exterior_w_mm=309, exterior_h_mm=309),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=205, h_mm=290, surf_m2=0.0580, exterior_w_mm=285, exterior_h_mm=370),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=229, h_mm=305, surf_m2=0.0680, exterior_w_mm=309, exterior_h_mm=385),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=150, h_mm=600, surf_m2=0.0880, exterior_w_mm=230, exterior_h_mm=600),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=220, h_mm=420, surf_m2=0.0900, exterior_w_mm=300, exterior_h_mm=500),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=340, h_mm=385, surf_m2=0.1280, exterior_w_mm=400, exterior_h_mm=445),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=305, h_mm=457, surf_m2=0.1380, exterior_w_mm=385, exterior_h_mm=537),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=247, h_mm=610, surf_m2=0.1450, exterior_w_mm=327, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=340, h_mm=440, surf_m2=0.1480, exterior_w_mm=400, exterior_h_mm=500),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=300, h_mm=620, surf_m2=0.1860, rated_vacuum_mbar=193, exterior_w_mm=380, exterior_h_mm=700),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=320, h_mm=640, surf_m2=0.2000, exterior_w_mm=380, exterior_h_mm=700),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=490, h_mm=490, surf_m2=0.2370, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=375, h_mm=655, surf_m2=0.2400, exterior_w_mm=455, exterior_h_mm=735),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=470, h_mm=610, surf_m2=0.2800, exterior_w_mm=550, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=490, h_mm=590, surf_m2=0.2850, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=525, h_mm=668, surf_m2=0.3400, exterior_w_mm=645, exterior_h_mm=788),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=610, h_mm=610, surf_m2=0.3650, rated_vacuum_mbar=193, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=457, h_mm=890, surf_m2=0.4050, rated_vacuum_mbar=145, exterior_w_mm=537, exterior_h_mm=970),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=620, h_mm=670, surf_m2=0.4100, exterior_w_mm=680, exterior_h_mm=730),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=645, h_mm=645, surf_m2=0.4100, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=653, h_mm=653, surf_m2=0.4200, exterior_w_mm=733, exterior_h_mm=733),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=520, h_mm=1020, surf_m2=0.5250, exterior_w_mm=600, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=586, h_mm=920, surf_m2=0.5350, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=500, h_mm=1100, surf_m2=0.5400, exterior_w_mm=580, exterior_h_mm=1180),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=750, h_mm=750, surf_m2=0.5600, exterior_w_mm=830, exterior_h_mm=830),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=750, h_mm=840, surf_m2=0.6250, exterior_w_mm=830, exterior_h_mm=920),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=801, h_mm=801, surf_m2=0.6400, exterior_w_mm=880, exterior_h_mm=880),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=610, h_mm=1118, surf_m2=0.6750, exterior_w_mm=690, exterior_h_mm=1198),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=645, h_mm=1130, surf_m2=0.7280, exterior_w_mm=725, exterior_h_mm=1210),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=720, h_mm=1020, surf_m2=0.7300, exterior_w_mm=800, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=920, h_mm=920, surf_m2=0.8400, rated_vacuum_mbar=97, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=915, h_mm=1118, surf_m2=1.0000, rated_vacuum_mbar=97, exterior_w_mm=995, exterior_h_mm=1198),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=1020, h_mm=1020, surf_m2=1.0400, exterior_w_mm=1100, exterior_h_mm=1100),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=1130, h_mm=1130, surf_m2=1.2500, rated_vacuum_mbar=97, exterior_w_mm=1220, exterior_h_mm=1220),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=208, h_mm=208, surf_m2=0.0300, shape="round", exterior_w_mm=268, exterior_h_mm=268),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=261, h_mm=261, surf_m2=0.0480, shape="round", exterior_w_mm=341, exterior_h_mm=341),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=310, h_mm=310, surf_m2=0.0680, shape="round", exterior_w_mm=390, exterior_h_mm=390),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=342, h_mm=342, surf_m2=0.0830, shape="round", exterior_w_mm=422, exterior_h_mm=422),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=393, h_mm=393, surf_m2=0.1213, shape="round", exterior_w_mm=473, exterior_h_mm=473),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=465, h_mm=465, surf_m2=0.1600, shape="round", exterior_w_mm=545, exterior_h_mm=545),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=494, h_mm=494, surf_m2=0.1820, shape="round", exterior_w_mm=574, exterior_h_mm=574),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=596, h_mm=596, surf_m2=0.2650, shape="round", exterior_w_mm=676, exterior_h_mm=676),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=616, h_mm=616, surf_m2=0.2650, shape="round", exterior_w_mm=692, exterior_h_mm=692),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=696, h_mm=696, surf_m2=0.3650, shape="round", exterior_w_mm=776, exterior_h_mm=776),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=762, h_mm=762, surf_m2=0.4400, shape="round", exterior_w_mm=842, exterior_h_mm=842),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=768, h_mm=768, surf_m2=0.4421, shape="round", exterior_w_mm=870, exterior_h_mm=870),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=797, h_mm=797, surf_m2=0.4800, shape="round", exterior_w_mm=877, exterior_h_mm=877),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=894, h_mm=894, surf_m2=0.6000, shape="round", exterior_w_mm=974, exterior_h_mm=974),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=920, h_mm=920, surf_m2=0.6000, shape="round", exterior_w_mm=1022, exterior_h_mm=1022),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=995, h_mm=995, surf_m2=0.7600, shape="round", exterior_w_mm=1075, exterior_h_mm=1075),
            VentPanel(manufacturer="IEP", panel_type="Vacuum", model="GE", w_mm=1124, h_mm=1124, surf_m2=0.9850, shape="round", exterior_w_mm=1214, exterior_h_mm=1214),
        ],
    },
    "Fike": {
        "Standard": [
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=200, h_mm=355, surf_m2=0.071, exterior_w_mm=300, exterior_h_mm=455),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=300, h_mm=300, surf_m2=0.09, exterior_w_mm=400, exterior_h_mm=400),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=200, h_mm=500, surf_m2=0.1, exterior_w_mm=300, exterior_h_mm=600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=180, h_mm=580, surf_m2=0.104, exterior_w_mm=290, exterior_h_mm=690),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=320, h_mm=365, surf_m2=0.117, exterior_w_mm=420, exterior_h_mm=465),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=230, h_mm=540, surf_m2=0.124, exterior_w_mm=330, exterior_h_mm=640),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=200, h_mm=720, surf_m2=0.144, exterior_w_mm=300, exterior_h_mm=820),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=250, h_mm=600, surf_m2=0.15, exterior_w_mm=350, exterior_h_mm=700),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=300, h_mm=500, surf_m2=0.15, exterior_w_mm=400, exterior_h_mm=600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=180, h_mm=900, surf_m2=0.162, exterior_w_mm=280, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=350, h_mm=500, surf_m2=0.175, exterior_w_mm=450, exterior_h_mm=600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=230, h_mm=780, surf_m2=0.179, exterior_w_mm=330, exterior_h_mm=880),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=400, h_mm=500, surf_m2=0.2, exterior_w_mm=500, exterior_h_mm=600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=345, h_mm=625, surf_m2=0.216, exterior_w_mm=445, exterior_h_mm=735),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=470, h_mm=470, surf_m2=0.221, exterior_w_mm=570, exterior_h_mm=570),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=350, h_mm=650, surf_m2=0.228, exterior_w_mm=450, exterior_h_mm=750),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=300, h_mm=770, surf_m2=0.231, exterior_w_mm=400, exterior_h_mm=870),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=350, h_mm=700, surf_m2=0.245, exterior_w_mm=450, exterior_h_mm=800),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=500, surf_m2=0.25, exterior_w_mm=600, exterior_h_mm=600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=470, h_mm=570, surf_m2=0.268, exterior_w_mm=570, exterior_h_mm=670),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=300, h_mm=900, surf_m2=0.27, exterior_w_mm=400, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=600, surf_m2=0.3, exterior_w_mm=600, exterior_h_mm=700),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=340, h_mm=900, surf_m2=0.306, exterior_w_mm=440, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=590, h_mm=590, surf_m2=0.348, exterior_w_mm=690, exterior_h_mm=690),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=700, surf_m2=0.35, exterior_w_mm=600, exterior_h_mm=800),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=400, h_mm=900, surf_m2=0.36, exterior_w_mm=500, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=600, h_mm=600, surf_m2=0.36, exterior_w_mm=700, exterior_h_mm=700),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=625, h_mm=625, surf_m2=0.391, exterior_w_mm=735, exterior_h_mm=735),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=800, surf_m2=0.4, exterior_w_mm=600, exterior_h_mm=900),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=900, surf_m2=0.45, exterior_w_mm=600, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=700, h_mm=700, surf_m2=0.49, exterior_w_mm=800, exterior_h_mm=800),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=500, h_mm=1000, surf_m2=0.5, exterior_w_mm=600, exterior_h_mm=1100),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=566, h_mm=900, surf_m2=0.509, exterior_w_mm=666, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=600, h_mm=1000, surf_m2=0.6, exterior_w_mm=700, exterior_h_mm=1100),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=625, h_mm=1110, surf_m2=0.694, exterior_w_mm=735, exterior_h_mm=1220),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=700, h_mm=1000, surf_m2=0.7, exterior_w_mm=800, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=750, h_mm=1005, surf_m2=0.754, exterior_w_mm=860, exterior_h_mm=1115),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=800, h_mm=1000, surf_m2=0.8, exterior_w_mm=900, exterior_h_mm=1100),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=900, h_mm=900, surf_m2=0.81, exterior_w_mm=1000, exterior_h_mm=1000),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=900, h_mm=1000, surf_m2=0.9, exterior_w_mm=1000, exterior_h_mm=1100),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1000, h_mm=1000, surf_m2=1.0, exterior_w_mm=1100, exterior_h_mm=1100),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1110, h_mm=1110, surf_m2=1.232, exterior_w_mm=1220, exterior_h_mm=1220),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1110, h_mm=1320, surf_m2=1.465, exterior_w_mm=1210, exterior_h_mm=1420),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1000, h_mm=1500, surf_m2=1.5, exterior_w_mm=1100, exterior_h_mm=1600),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1110, h_mm=1500, surf_m2=1.665, exterior_w_mm=1220, exterior_h_mm=1610),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1095, h_mm=1600, surf_m2=1.752, exterior_w_mm=1195, exterior_h_mm=1700),
            VentPanel(manufacturer="Fike", panel_type="Standard", model="CV", w_mm=1000, h_mm=2000, surf_m2=2.0, exterior_w_mm=1100, exterior_h_mm=2100),
        ],
        "Vacuum": [
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=228.6, h_mm=304.8, surf_m2=0.05, rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=228.6, h_mm=457.2, surf_m2=0.08, rated_vacuum_mbar=800),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=304.8, h_mm=304.8, surf_m2=0.07, rated_vacuum_mbar=869),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=304.8, h_mm=457.2, surf_m2=0.11, rated_vacuum_mbar=614),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=304.8, h_mm=609.6, surf_m2=0.15, rated_vacuum_mbar=483),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=457.2, h_mm=457.2, surf_m2=0.17, rated_vacuum_mbar=427),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=457.2, h_mm=609.6, surf_m2=0.24, rated_vacuum_mbar=338),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=457.2, h_mm=889.0, surf_m2=0.35, rated_vacuum_mbar=283),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=457.2, h_mm=914.4, surf_m2=0.36, rated_vacuum_mbar=283),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=609.6, h_mm=609.6, surf_m2=0.32, rated_vacuum_mbar=283),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=609.6, h_mm=914.4, surf_m2=0.49, rated_vacuum_mbar=207),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=609.6, h_mm=1117.6, surf_m2=0.61, rated_vacuum_mbar=207),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=609.6, h_mm=1219.2, surf_m2=0.66, rated_vacuum_mbar=207),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=762.0, h_mm=914.4, surf_m2=0.62, rated_vacuum_mbar=207),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=914.4, h_mm=914.4, surf_m2=0.76, rated_vacuum_mbar=207),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=914.4, h_mm=1117.6, surf_m2=0.93, rated_vacuum_mbar=117),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=965.2, h_mm=1168.4, surf_m2=1.04, rated_vacuum_mbar=117),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=1117.6, h_mm=1117.6, surf_m2=1.15, rated_vacuum_mbar=117),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=1117.6, h_mm=1752.6, surf_m2=1.83, rated_vacuum_mbar=48),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=152.4, h_mm=152.4, surf_m2=0.01, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=203.2, h_mm=203.2, surf_m2=0.02, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=254.0, h_mm=254.0, surf_m2=0.04, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=304.8, h_mm=304.8, surf_m2=0.06, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=355.6, h_mm=355.6, surf_m2=0.09, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=406.4, h_mm=406.4, surf_m2=0.11, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=457.2, h_mm=457.2, surf_m2=0.15, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=508.0, h_mm=508.0, surf_m2=0.18, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=558.8, h_mm=558.8, surf_m2=0.22, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=609.6, h_mm=609.6, surf_m2=0.27, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=660.4, h_mm=660.4, surf_m2=0.32, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=762.0, h_mm=762.0, surf_m2=0.43, shape="round", rated_vacuum_mbar=1014),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=812.8, h_mm=812.8, surf_m2=0.49, shape="round", rated_vacuum_mbar=507),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=914.4, h_mm=914.4, surf_m2=0.62, shape="round", rated_vacuum_mbar=507),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=1016.0, h_mm=1016.0, surf_m2=0.77, shape="round", rated_vacuum_mbar=507),
            VentPanel(manufacturer="Fike", panel_type="Vacuum", model="CV-S", w_mm=1117.6, h_mm=1117.6, surf_m2=0.94, shape="round", rated_vacuum_mbar=507),
        ],
        "High Vacuum": [
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=609.6, h_mm=609.6, surf_m2=0.33, rated_vacuum_mbar=700),
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=457.2, h_mm=889.0, surf_m2=0.36, rated_vacuum_mbar=700),
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=457.2, h_mm=914.4, surf_m2=0.37, rated_vacuum_mbar=700),
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=609.6, h_mm=914.4, surf_m2=0.5, rated_vacuum_mbar=700),
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=914.4, h_mm=914.4, surf_m2=0.77, rated_vacuum_mbar=700),
            VentPanel(manufacturer="Fike", panel_type="High Vacuum", model="CV-S-HV", w_mm=914.4, h_mm=1117.6, surf_m2=0.95, rated_vacuum_mbar=700),
        ],
    },
}


def list_manufacturers() -> list[str]:
    """Names of all manufacturers in the vent panel catalog."""
    return list(VENT_PANEL_CATALOG.keys())


def list_panel_types(manufacturer: str) -> list[str]:
    """Panel type names available for a given manufacturer."""
    return list(VENT_PANEL_CATALOG[manufacturer].keys())


def list_panels(manufacturer: str, panel_type: str) -> list[VentPanel]:
    """Catalog panels for a given manufacturer and panel type."""
    return VENT_PANEL_CATALOG[manufacturer][panel_type]


@dataclass
class PanelSelection:
    """Panel-count result for one catalog panel against a target vent area."""
    panel: VentPanel
    panels_required: int
    total_effective_area_m2: float


def compute_panel_selection(
    avf_m2: float,
    manufacturers: list[str],
    panel_types: list[str],
    efficiency: float,
    stocked_only: bool = False,
) -> list[PanelSelection]:
    """
    For every catalog panel whose manufacturer is in `manufacturers` and
    whose panel type is in `panel_types` (and, if `stocked_only`, whose
    nominal size is in STOCKED_SIZES_MM), compute the whole-panel count
    needed to meet `avf_m2` at the given `efficiency` (0-1 fraction), and
    the resulting total effective vent area. Results are sorted ascending
    by panels_required.
    """
    results = []
    for manufacturer in manufacturers:
        types_available = VENT_PANEL_CATALOG.get(manufacturer, {})
        for panel_type in panel_types:
            for panel in types_available.get(panel_type, []):
                if stocked_only and not panel.is_stocked:
                    continue
                eff_area_per_panel = panel.surf_m2 * efficiency
                n = math.ceil(avf_m2 / eff_area_per_panel) if eff_area_per_panel > 0 else 0
                total = n * eff_area_per_panel
                results.append(PanelSelection(panel=panel, panels_required=n, total_effective_area_m2=total))
    results.sort(key=lambda r: r.panels_required)
    return results
