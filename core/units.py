"""Named unit conversions for flow, velocity, length and pressure.

Built on the shared pint registry in ``core.utils``; no conversion factors are
hand-typed. Functions are generated from the unit tables below as
``<from>_to_<to>(value)`` (e.g. ``cfm_to_m3s``, ``inh2o_to_pa``) and listed
explicitly in ``__all__``. No rounding; display precision belongs to the UI.

Pressure references: ``inh2o`` is pint's bare ``inch_H2O`` (conventional water
density, 249.089 Pa per inch) and ``inhg`` is bare ``inch_Hg`` (3386.39 Pa, same
as ``inch_Hg_32F``). Spreadsheets using 60 °F water (248.8 Pa) differ by ~0.1 %.
Conversions are linear, so they apply to gauge and differential pressure alike.
"""
from core.utils import u

_FLOW = {"cfm": "foot**3/minute", "m3h": "meter**3/hour", "m3s": "meter**3/second"}
_VELOCITY = {"fpm": "foot/minute", "ms": "meter/second"}
_LENGTH = {"in": "inch", "mm": "millimeter", "m": "meter"}
_PRESSURE = {
    "inh2o": "inch_H2O", "inhg": "inch_Hg", "psi": "psi",
    "pa": "pascal", "bar": "bar", "atm": "atmosphere",
}

__all__ = ["convert_pressure"]


def _make(src_unit, dst_unit, name):
    def convert(value):
        return u.Quantity(value, src_unit).to(dst_unit).magnitude
    convert.__name__ = name
    convert.__doc__ = f"Convert {src_unit} to {dst_unit} (pint)."
    return convert


for _table in (_FLOW, _VELOCITY, _LENGTH, _PRESSURE):
    for _src, _src_unit in _table.items():
        for _dst, _dst_unit in _table.items():
            if _src != _dst:
                _name = f"{_src}_to_{_dst}"
                globals()[_name] = _make(_src_unit, _dst_unit, _name)
                __all__.append(_name)


def convert_pressure(value, from_unit, to_unit):
    """Convert between the pressure units in the table (keys: inh2o, inhg, psi, pa, bar, atm)."""
    try:
        src, dst = _PRESSURE[from_unit], _PRESSURE[to_unit]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported pressure unit {exc.args[0]!r}; allowed: {sorted(_PRESSURE)}."
        ) from None
    return u.Quantity(value, src).to(dst).magnitude
