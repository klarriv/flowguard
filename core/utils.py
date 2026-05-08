from pint import UnitRegistry

u = UnitRegistry()

def si(value):
    """Convert a pint unit-aware value to its SI base unit magnitude (float)."""
    return value.to_base_units().magnitude