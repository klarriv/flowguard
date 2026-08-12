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
    datasheet (e.g. "VL", "VD", "VD-HV" for Vigilex) — one code per
    `panel_type`. `panel_type` is the friendlier name ("Standard",
    "Vacuum", "High Vacuum") used for filtering in the UI.
    """
    manufacturer: str
    panel_type: str
    model: str
    w_mm: float
    h_mm: float
    surf_m2: float
    panel_density_kgm2: float

    @property
    def nominal_metric(self) -> str:
        return f"{_fmt_mm(self.w_mm)} x {_fmt_mm(self.h_mm)} mm"

    @property
    def nominal_imperial(self) -> str:
        return f"{_mm_to_in(self.w_mm)} x {_mm_to_in(self.h_mm)} in"

    @property
    def is_stocked(self) -> bool:
        return (self.w_mm, self.h_mm) in STOCKED_SIZES_MM


# Nominal (width, height) sizes normally kept in stock, applied uniformly
# across every manufacturer/panel type — the sizes actually offered still
# vary by panel type (e.g. not every stocked size exists in High Vacuum),
# so this is intersected against each type's real catalog, not a fixed list
# per type.
STOCKED_SIZES_MM: set[tuple[float, float]] = {
    (170, 470), (270, 458), (305, 457), (300, 500), (305, 610), (350, 650),
    (490, 590), (610, 610), (457, 890), (586, 920), (610, 914), (920, 920),
    (915, 1118), (1130, 1130),
}


VENT_PANEL_CATALOG: dict[str, dict[str, list[VentPanel]]] = {
    "Vigilex": {
        "Standard": [
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=110, h_mm=290, surf_m2=0.031, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=150, h_mm=600, surf_m2=0.0885, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=300, h_mm=600, surf_m2=0.178, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=319, h_mm=765, surf_m2=0.2425, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=340, h_mm=385, surf_m2=0.129, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=340, h_mm=440, surf_m2=0.148, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=390, h_mm=620, surf_m2=0.2395, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=400, h_mm=400, surf_m2=0.158, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=420, h_mm=520, surf_m2=0.2165, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=420, h_mm=920, surf_m2=0.3835, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=480, h_mm=680, surf_m2=0.326, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=520, surf_m2=0.268, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=620, surf_m2=0.32, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=520, h_mm=1020, surf_m2=0.527, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=580, h_mm=1180, surf_m2=0.6805, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=600, h_mm=600, surf_m2=0.3576, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=914, surf_m2=0.5545, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=610, h_mm=1118, surf_m2=0.6785, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=620, h_mm=820, surf_m2=0.5055, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=629, h_mm=1004, surf_m2=0.629, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=645, h_mm=645, surf_m2=0.413, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=645, h_mm=1130, surf_m2=0.725, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=680, h_mm=680, surf_m2=0.4595, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=720, h_mm=1020, surf_m2=0.7305, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=780, h_mm=780, surf_m2=0.605, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=780, h_mm=1180, surf_m2=0.916, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=800, h_mm=800, surf_m2=0.6365, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=800, h_mm=1000, surf_m2=0.796, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=880, h_mm=880, surf_m2=0.7705, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=915, h_mm=1118, surf_m2=1.02, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=920, h_mm=920, surf_m2=0.8425, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=980, h_mm=980, surf_m2=0.956, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=986, h_mm=986, surf_m2=0.968, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1020, h_mm=1020, surf_m2=1.036, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1080, h_mm=1080, surf_m2=1.162, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1130, h_mm=1130, surf_m2=1.272, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Standard", model="VL", w_mm=1180, h_mm=1180, surf_m2=1.3875, panel_density_kgm2=6.28),
        ],
        "Vacuum": [
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=150, h_mm=600, surf_m2=0.0885, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=340, h_mm=385, surf_m2=0.129, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=340, h_mm=440, surf_m2=0.148, panel_density_kgm2=3.925),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=525, h_mm=668, surf_m2=0.348, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=558, h_mm=914, surf_m2=0.5109, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=914, surf_m2=0.5545, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=610, h_mm=1118, surf_m2=0.6785, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=645, h_mm=645, surf_m2=0.413, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=645, h_mm=1130, surf_m2=0.725, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=915, h_mm=1118, surf_m2=1.02, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=920, h_mm=920, surf_m2=0.8425, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=980, h_mm=980, surf_m2=0.956, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=1020, h_mm=1020, surf_m2=1.036, panel_density_kgm2=11.775),
            VentPanel(manufacturer="Vigilex", panel_type="Vacuum", model="VD", w_mm=1130, h_mm=1130, surf_m2=1.272, panel_density_kgm2=11.775),
        ],
        "High Vacuum": [
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=170, h_mm=470, surf_m2=0.0785, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=205, h_mm=290, surf_m2=0.058, panel_density_kgm2=3.93),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=220, h_mm=420, surf_m2=0.091, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=229, h_mm=229, surf_m2=0.0515, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=229, h_mm=305, surf_m2=0.069, panel_density_kgm2=6.28),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=247, h_mm=610, surf_m2=0.1485, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=270, h_mm=458, surf_m2=0.122, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=300, h_mm=500, surf_m2=0.148, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=305, h_mm=457, surf_m2=0.1385, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=305, h_mm=610, surf_m2=0.1845, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=340, h_mm=440, surf_m2=0.148, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=350, h_mm=650, surf_m2=0.2255, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=375, h_mm=655, surf_m2=0.2445, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=410, h_mm=410, surf_m2=0.166, panel_density_kgm2=9.42),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=490, h_mm=490, surf_m2=0.238, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=490, h_mm=590, surf_m2=0.2865, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=470, h_mm=610, surf_m2=0.2845, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=457, h_mm=890, surf_m2=0.404, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=586, h_mm=920, surf_m2=0.536, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=610, h_mm=610, surf_m2=0.3695, panel_density_kgm2=11.78),
            VentPanel(manufacturer="Vigilex", panel_type="High Vacuum", model="VD-HV", w_mm=653, h_mm=653, surf_m2=0.426, panel_density_kgm2=11.78),
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
