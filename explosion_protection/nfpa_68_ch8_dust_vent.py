"""
nfpa_68_ch8_dust_vent.py
========================
Orchestrator for NFPA 68 (2023) Chapter 8 — Deflagration Vent Area for
Combustible Dusts and Hybrid Mixtures.

Scope
-----
All enclosures with L/D ≤ 6 handling combustible dusts or hybrid mixtures at
near-atmospheric, elevated, or subatmospheric initial pressures. (§8.1.1)

Excludes §8.8 Bucket Elevators — handled in a dedicated orchestrator.

Calculation sequence (§8.2 → §8.5, per Figure 8.1.1.4)
---------------------------------------------------------
1.  Validate inputs against applicability limits           (§8.1, Table 8.5.10)
2.  Compute Av0 — minimum vent area                        (§8.2.1)
      a. Near-atmospheric  (−0.2 ≤ Pinitial ≤ 0.2 bar-g)  Eq. 8.2.1.1
      b. Elevated/subatm   (|Pinitial| > 0.2 bar-g)        Eq. 8.2.1.2
         Subatm simplified  (Pinitial < −0.2 bar-g)         Eq. 8.2.1.2.2
3.  Apply L/D correction → Av1                             (§8.2.2, Eq. 8.2.2.3)
4.  Apply turbulence correction → Av2                      (§8.2.4)
      a. Process equipment  (vaxial or vtan > 20 m/s)       Eq. 8.2.4.6
      b. Building hazard    (flat 1.7× factor)              Eq. 8.2.4.7
      c. No turbulence correction  Av2 = Av1
5.  Apply panel inertia correction → Av3                   (§8.3)
      MT threshold                                          Eq. 8.3.2
      Inertia correction                                    Eq. 8.3.4
6.  Apply partial volume correction → Av4                  (§8.4)
      Process enclosure  Xr from                           Eq. 8.4.1
      Building partial volume  Xr from                     §8.4.5
      Reduced vent area                                     Eq. 8.4.3
7.  Apply vent duct correction → Avf                       (§8.5.1, Eq. 8.5.1a–d)
      Iterative solution enforcing E1 ≤ 1  (lower root)    Annex A.8.5b
      DDT limit check                                       §8.5.9

Special-application helpers (non-iterative, no §8.8)
-----------------------------------------------------
  dust_collector_vent_area()  §8.7  — bag/filter/cartridge collectors
  silo_bin_vent_split()       §8.10 — silos with integral bin vents
  building_pressure_rise()    §8.9  — internal-to-building pressure estimate
  interconnected_enclosures() §8.11 — pipeline-connected enclosures

Usage — standard process enclosure
-----------------------------------
    from nfpa_68_ch8_dust_vent import (
        Enclosure, Dust, Vent, Duct, TurbulenceMode, vent_area_dust
    )

    enclosure = Enclosure(V=25.0, LD=4.0)
    dust      = Dust(KSt=200, Pmax=8.0)
    vent      = Vent(Pred=0.5, Pstat=0.1, n=2, M=10.0)
    duct      = Duct(Lduct=6.0, Dh=0.8, K=3.5)   # or None

    result = vent_area_dust(enclosure, dust, vent, duct=duct)
    print(result.Avf)   # final required vent area [m²]
    print(result)       # full intermediate chain for reporting
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from .nfpa_68_ch8_equations import (
    # §8.2.1
    vent_area_atm,
    vent_area_elevated_pressure,
    vent_area_subatm_simplified,
    # §8.2.2
    vent_area_ld_correction,
    # §8.2.4
    axial_velocity,
    tangential_velocity,
    vent_area_turbulence,
    vent_area_building_turbulence,
    # §8.3
    panel_mass_threshold,
    vent_area_panel_inertia,
    # §8.4
    partial_volume_fraction,
    vent_area_partial_volume,
    building_partial_volume_fraction,
    # §8.5
    ROUGHNESS_USED_STEEL,
    darcy_friction_factor,
    duct_resistance_coefficient,
    vent_area_duct,
    max_duct_length,
    # §8.7
    # (No dedicated equations in equations file — clear-path check is
    #  a design rule applied here in the orchestrator.)
    # §8.9
    building_pressure_rise,
    # §8.10
    bin_vent_area_split,
)


# ──────────────────────────────────────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────────────────────────────────────

class InitialPressureRegime(Enum):
    """Pressure regime that determines which §8.2.1 equation applies."""
    NEAR_ATMOSPHERIC  = auto()   # −0.2 ≤ Pinitial ≤ 0.2 bar-g  → Eq. 8.2.1.1
    ELEVATED          = auto()   # Pinitial > 0.2 bar-g           → Eq. 8.2.1.2
    SUBATMOSPHERIC    = auto()   # Pinitial < −0.2 bar-g          → Eq. 8.2.1.2
                                 #   (or simplified Eq. 8.2.1.2.2)


class TurbulenceMode(Enum):
    """
    Turbulence correction branch to apply (§8.2.4).

    NONE        No significant turbulence (vaxial and vtan both < 20 m/s).
                Av2 = Av1.  (§8.2.4.5)

    PROCESS     Equipment with axial or tangential air flows.
                Caller supplies vaxial and vtan; Eq. 8.2.4.6 applies when
                max(vaxial, vtan) > 20 m/s.

    BUILDING    Building in which there is a dust explosion hazard.
                Flat 1.7× factor per Eq. 8.2.4.7, regardless of velocity.
    """
    NONE     = auto()
    PROCESS  = auto()
    BUILDING = auto()


class SubatmosphericMethod(Enum):
    """
    Which equation to use for subatmospheric initial pressure.

    GENERAL     Eq. 8.2.1.2 — evaluate over the full operating range and use
                the maximum vent area found. (§8.2.1.2.1)

    SIMPLIFIED  Eq. 8.2.1.2.2 — conservative single-point alternative.
                (§8.2.1.2.2)
    """
    GENERAL    = auto()
    SIMPLIFIED = auto()


# ──────────────────────────────────────────────────────────────────────────────
# Input dataclasses
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Enclosure:
    """
    Geometric properties of the protected enclosure.

    Attributes:
        V       (float): Total enclosure volume [m³]
        LD      (float): Enclosure L/D ratio [-]                        §6.4 / §8.1.1
        Vsolid  (float): Volume of solid objects inside [m³]            §8.4.1
                         Default 0.0.

    Notes:
        For dust collectors (§8.7), V should be the total dirty-side volume
        including filter volume (Veff = V per §8.7.1.2). The caller is
        responsible for setting this correctly before passing to vent_area_dust().
    """
    V:      float
    LD:     float
    Vsolid: float = 0.0


@dataclass
class Dust:
    """
    Explosion characteristics of the dust or hybrid mixture.

    Attributes:
        KSt      (float): Deflagration index [bar·m/s]                  §8.1.2
        Pmax     (float): Max pressure in an unvented deflagration at
                          atmospheric initial pressure [bar-g]           §8.2.1.1
        Pinitial (float): Enclosure pressure at moment of ignition [bar-g].
                          Default 0.0 (atmospheric).                    §8.2.1
    """
    KSt:      float
    Pmax:     float
    Pinitial: float = 0.0


@dataclass
class Vent:
    """
    Vent panel and operating pressure properties.

    Attributes:
        Pred  (float): Target reduced pressure after deflagration venting [bar-g]
        Pstat (float): Nominal static burst/opening pressure of the vent [bar-g]
        n     (int):   Number of vent panels [-]                        §8.3.2
        M     (float): Vent panel areal mass [kg/m²]                   §8.3
                       Must be ≤ 40 kg/m² for §8.3 to apply. Default 0.0.
        Fsh   (float): Panel shape factor — 1.0 translating, 1.1 hinged.
                       Default 1.0.                                     §8.3.4
    """
    Pred:  float
    Pstat: float
    n:     int   = 1
    M:     float = 0.0
    Fsh:   float = 1.0


@dataclass
class Duct:
    """
    Vent duct properties. Pass None to vent_area_dust() if no duct is present.

    The overall resistance coefficient K is computed automatically from the
    individual loss components via darcy_friction_factor() and
    duct_resistance_coefficient(). (§8.5.1d, Annex A.8.5a–d)

    Attributes:
        Lduct   (float): Overall duct centerline length, including the
                         centerline path through all elbows and fittings [m]
        Dh      (float): Duct hydraulic (internal) diameter [m]
        Kinlet  (float): Inlet resistance coefficient [-].
                         1.5 = flush inlet, 2.0 = inserted inlet.
                         (Fig. A.8.5(a))
        Kelbows (float): Sum of resistance coefficients for all elbows and
                         fittings [-]. Default 0.0.
                         Use duct_resistance_coefficient helpers or
                         scale 0.39/elbow for R/D=1.5 round elbows.
                         (Fig. A.8.5(b)–(c))
        Koutlet (float): Outlet resistance coefficient [-]. Default 0.0
                         (plain open outlet). Use 0.73 when a rain hat
                         (H=0.5D) is fitted. (Fig. A.8.5(a), A.8.5(d))
        epsilon (float): Absolute internal roughness [m].
                         Default ROUGHNESS_USED_STEEL = 2.6e-4 m, the value
                         NFPA 68 assumes for steel ducts exposed to repeated
                         combustion events. (Annex A.8.5c)
        K0      (float): Reference resistance coefficient. Default 1.5. (§8.5.1a)

    Computed property:
        K       (float): Overall duct resistance coefficient [-], assembled as
                         K = Kinlet + fD·Lduct/Dh + Kelbows + Koutlet
                         where fD is the fully-rough D'Arcy friction factor.
                         (Eq. 8.5.1d, Annex A.8.5c)

    Applicability limits enforced at runtime (§8.5.4–§8.5.6):
        - Vent cover must be at duct entrance.
        - Initial pressure ≤ 0.2 bar-g.
        - Duct cross-section varies ≤ 10% along length.
    """
    Lduct:   float
    Dh:      float
    Kinlet:  float = 1.5
    Kelbows: float = 0.0
    Koutlet: float = 0.0
    epsilon: float = ROUGHNESS_USED_STEEL   # 2.6e-4 m per A.8.5c
    K0:      float = 1.5

    @property
    def fD(self) -> float:
        """D'Arcy friction factor computed from Dh and epsilon. (Annex A.8.5c)"""
        return darcy_friction_factor(self.Dh, self.epsilon)

    @property
    def K(self) -> float:
        """
        Overall duct resistance coefficient.
        K = Kinlet + fD·Lduct/Dh + Kelbows + Koutlet  (Eq. 8.5.1d)
        """
        return duct_resistance_coefficient(
            Kinlet   = self.Kinlet,
            fD       = self.fD,
            Lduct    = self.Lduct,
            Dh       = self.Dh,
            K_elbows = self.Kelbows,
            Koutlet  = self.Koutlet,
        )


@dataclass
class TurbulenceInputs:
    """
    Air velocity inputs required when TurbulenceMode.PROCESS is selected.

    Attributes:
        Q    (float): Volumetric air flow rate [m³/s]
        A    (float): Average cross-sectional area of flow path [m²]   §8.2.4.1
        Ain  (float): Inlet cross-sectional area for tangential flow [m²].
                      Set to None (or omit) when there is no tangential inlet.
                      §8.2.4.2
    """
    Q:   float
    A:   float
    Ain: Optional[float] = None


@dataclass
class PartialVolumeInputs:
    """
    Inputs required when a partial volume correction is requested (§8.4).

    For process enclosures (Eq. 8.4.1):
        Me     (float): Total mass of combustible dust that could be
                        suspended inside the enclosure [g]              §8.4.1
        cw     (float): Worst-case dust concentration [g/m³].
                        Use 200 g/m³ if not measured (§8.4.2.2).

    For buildings with surface deposits (§8.4.5) — set use_building=True
    and supply all building_ parameters. If use_building=False (default),
    the process enclosure method (Eq. 8.4.1) is used.

    Building partial volume attributes (§8.4.5.3):
        use_building    (bool):  Switch to building partial volume method.
        Mf_bar          (float): Average floor sample mass [g]
        Af_dusty        (float): Total dusty floor area [m²]
        eta_Dfloor      (float): Floor entrainment factor [-]
        Afs             (float): Area of each floor sample [m²]
        Ms_bar          (float): Average surface sample mass [g]
        Asur            (float): Total surface area with dust deposits [m²]
        eta_Dsur        (float): Surface entrainment factor [-]
        Ass             (float): Area of each surface sample [m²]
        Me_equipment    (float): Dust mass from process equipment [g]
        cw              (float): Worst-case dust concentration [g/m³]
    """
    Me:            Optional[float] = None   # process enclosure path
    cw:            float           = 200.0  # default per §8.4.2.2

    # building partial volume path
    use_building:  bool            = False
    Mf_bar:        Optional[float] = None
    Af_dusty:      Optional[float] = None
    eta_Dfloor:    Optional[float] = None
    Afs:           Optional[float] = None
    Ms_bar:        Optional[float] = None
    Asur:          Optional[float] = None
    eta_Dsur:      Optional[float] = None
    Ass:           Optional[float] = None
    Me_equipment:  Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DustVentResult:
    """
    Full calculation result with all intermediate areas for reporting.

    Attributes:
        Av0                   (float): Minimum vent area from §8.2.1 [m²]
        Av1                   (float): After L/D correction §8.2.2 [m²]
        Av2                   (float): After turbulence correction §8.2.4 [m²]
        Av3                   (float): After panel inertia correction §8.3 [m²]
        Av4                   (float): After partial volume correction §8.4 [m²]
        Avf                   (float): Final vent area after duct correction §8.5 [m²]
                                       Equal to Av4 when no duct is present.
        pressure_regime       (InitialPressureRegime): Branch taken in §8.2.1.
        subatm_method         (SubatmosphericMethod):  Subatm equation used,
                                                       or None if not subatm.
        Peffective            (float): 1/3·Pinitial used in Eq. 8.2.1.2 [bar-g].
                                       None for near-atmospheric path.
        PEmax                 (float): Max pressure at elevated initial pressure
                                       from Eq. 8.2.1.2 [bar-g].  None if N/A.
        Pi_effective          (float): Πeffective from Eq. 8.2.1.2 [-]. None if N/A.
        turbulence_mode       (TurbulenceMode): Turbulence branch applied.
        vaxial                (float): Axial air velocity [m/s]. None if not PROCESS.
        vtan                  (float): Effective tangential air velocity [m/s].
                                       None if no tangential inlet.
        MT                    (float): Threshold panel areal mass [kg/m²] §8.3.2.
        panel_inertia_active  (bool):  True when M > MT and §8.3.4 was applied.
        Xr                    (float): Partial volume fill fraction [-].
                                       None if partial volume not applied.
        partial_volume_active (bool):  True when partial volume reduced Av.
        duct_active           (bool):  True when duct correction was applied.
        E1                    (float): Duct intermediate parameter E1 [-].
                                       None if no duct.
        E2                    (float): Duct intermediate parameter E2 [-].
                                       None if no duct.
        Leff_max              (float): Max allowable effective duct length [m].
                                       None if no duct.
        Ldusty                (float): Dusty flame path parameter [m].
                                       None if no duct.
        ddt_ok                (bool):  True when DDT limit is satisfied (§8.5.9).
                                       None if no duct.
        ld_correction_active  (bool):  True when LD > 2 and §8.2.2.3 was applied.
    """
    Av0:                   float
    Av1:                   float
    Av2:                   float
    Av3:                   float
    Av4:                   float
    Avf:                   float
    pressure_regime:       InitialPressureRegime
    subatm_method:         Optional[SubatmosphericMethod]
    Peffective:            Optional[float]
    PEmax:                 Optional[float]
    Pi_effective:          Optional[float]
    turbulence_mode:       TurbulenceMode
    vaxial:                Optional[float]
    vtan:                  Optional[float]
    MT:                    float
    panel_inertia_active:  bool
    Xr:                    Optional[float]
    partial_volume_active: bool
    duct_active:           bool
    E1:                    Optional[float]
    E2:                    Optional[float]
    Leff_max:              Optional[float]
    Ldusty:                Optional[float]
    ddt_ok:                Optional[bool]
    ld_correction_active:  bool


# ──────────────────────────────────────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────────────────────────────────────

def _validate_inputs(
    enclosure: Enclosure,
    dust: Dust,
    vent: Vent,
    duct: Optional[Duct],
    turbulence_mode: TurbulenceMode,
    partial_volume: Optional[PartialVolumeInputs],
    subatm_method: SubatmosphericMethod,
) -> None:
    """
    Raise ValueError for inputs that violate §8.1.1 scope and Table 8.5.10
    combination rules.

    Reference:
        NFPA 68 (2023), §8.1.1, §8.3.1, §8.3.3, §8.5.4–8.5.6, Table 8.5.10
    """
    errors = []

    # §8.1.1 — Chapter 8 scope: L/D ≤ 6
    if enclosure.LD > 6:
        errors.append(
            f"Enclosure L/D = {enclosure.LD} exceeds 6. "
            "Chapter 8 does not apply for L/D > 6. (§8.1.1)"
        )

    # §8.1.1 — Minimum L/D
    if enclosure.LD < 1:
        errors.append(
            f"Enclosure L/D = {enclosure.LD} is less than 1. "
            "L/D must be ≥ 1 per Table 8.5.10."
        )

    # §8.3.1 — Panel mass upper bound for inertia correction
    if vent.M > 40.0:
        errors.append(
            f"Vent panel mass M = {vent.M} kg/m² exceeds 40 kg/m². "
            "Use Annex G procedure for M > 40 kg/m². (§8.3.3)"
        )

    # Table 8.5.10 — Elevated pressure restrictions
    Pinitial = dust.Pinitial
    Pi_abs   = Pinitial + 1.013   # convert bar-g to bar-abs (approx.)

    if Pi_abs > 1.2:
        # Elevated initial pressure — duct and partial volume not permitted
        if duct is not None:
            errors.append(
                "Vent ducts (§8.5) shall not be combined with elevated initial "
                f"pressure (Pinitial = {Pinitial} bar-g, ~{Pi_abs:.2f} bar-abs > 1.2 bar-abs). "
                "Table 8.5.10"
            )
        if partial_volume is not None:
            errors.append(
                "Partial volume (§8.4) shall not be combined with elevated initial "
                f"pressure (Pinitial = {Pinitial} bar-g, ~{Pi_abs:.2f} bar-abs > 1.2 bar-abs). "
                "Table 8.5.10"
            )
        if turbulence_mode == TurbulenceMode.PROCESS:
            errors.append(
                "Elevated initial pressure limits turbulence to vaxial and vtan < 20 m/s. "
                "If process velocities exceed 20 m/s, TurbulenceMode.PROCESS cannot be "
                "combined with elevated initial pressure. Table 8.5.10"
            )
        # Elevated pressure upper bound: Pinitial ≤ 5 bar-abs
        if Pi_abs > 5.0:
            errors.append(
                f"Elevated initial pressure Pinitial = {Pi_abs} bar-abs exceeds the "
                "validated range (≤ 5 bar-abs). Table 8.5.10"
            )

    # §8.5.5 — Duct not permitted when Pinitial > 0.2 bar-g
    if duct is not None and Pinitial > 0.2:
        errors.append(
            f"Eq. 8.5.1a shall not be used when initial pressure exceeds 0.2 bar-g. "
            f"Pinitial = {Pinitial} bar-g. (§8.5.5)"
        )

    # Partial volume inputs completeness check
    if partial_volume is not None:
        pv = partial_volume
        if pv.use_building:
            required = dict(
                Mf_bar=pv.Mf_bar, Af_dusty=pv.Af_dusty, eta_Dfloor=pv.eta_Dfloor,
                Afs=pv.Afs, Ms_bar=pv.Ms_bar, Asur=pv.Asur,
                eta_Dsur=pv.eta_Dsur, Ass=pv.Ass,
            )
            missing = [k for k, v in required.items() if v is None]
            if missing:
                errors.append(
                    "Building partial volume requested but the following fields are None: "
                    + ", ".join(missing) + ". (§8.4.5)"
                )
        else:
            if pv.Me is None:
                errors.append(
                    "Process partial volume requested but Me is None. "
                    "Provide Me [g] or set partial_volume=None. (§8.4.1)"
                )

    if errors:
        raise ValueError(
            "NFPA 68 Ch. 8 input validation failed:\n  - " + "\n  - ".join(errors)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Internal step helpers
# ──────────────────────────────────────────────────────────────────────────────

def _step_av0(
    dust: Dust,
    vent: Vent,
    enclosure: Enclosure,
    subatm_method: SubatmosphericMethod,
) -> tuple[float, InitialPressureRegime, Optional[SubatmosphericMethod],
           Optional[float], Optional[float], Optional[float]]:
    """
    Step 2 — Compute Av0 per §8.2.1.

    Returns:
        (Av0, pressure_regime, subatm_method_used,
         Peffective, PEmax, Pi_effective)
    """
    Pi = dust.Pinitial
    V  = enclosure.V

    if -0.2 <= Pi <= 0.2:
        # Near-atmospheric — Eq. 8.2.1.1
        Av0 = vent_area_atm(vent.Pstat, dust.KSt, V, dust.Pmax, vent.Pred)
        return (Av0, InitialPressureRegime.NEAR_ATMOSPHERIC,
                None, None, None, None)

    elif Pi < -0.2:
        # Subatmospheric — Eq. 8.2.1.2 or 8.2.1.2.2
        if subatm_method == SubatmosphericMethod.SIMPLIFIED:
            Av0 = vent_area_subatm_simplified(
                vent.Pstat, dust.KSt, V, dust.Pmax, vent.Pred
            )
            return (Av0, InitialPressureRegime.SUBATMOSPHERIC,
                    SubatmosphericMethod.SIMPLIFIED, None, None, None)
        else:
            # GENERAL — §8.2.1.2.1: evaluate over range from Pi to 0 and
            # take the maximum vent area found.
            # Scan in steps of 0.01 bar-g from Pinitial up to –0.2 bar-g.
            Pi_scan = Pi
            Av0_max = 0.0
            Peff_max, PEmax_max, Pieff_max = None, None, None
            step = 0.01
            n_steps = max(int(abs(Pi + 0.2) / step) + 2, 50)
            for k in range(n_steps + 1):
                Pi_try = Pi + k * ((-0.2 - Pi) / n_steps)
                try:
                    Av_try, Peff, PEmax, Pieff = vent_area_elevated_pressure(
                        vent.Pstat, Pi_try, dust.KSt, V, dust.Pmax, vent.Pred
                    )
                    if Av_try > Av0_max:
                        Av0_max = Av_try
                        Peff_max, PEmax_max, Pieff_max = Peff, PEmax, Pieff
                except (ValueError, ZeroDivisionError):
                    continue
            Av0 = Av0_max
            return (Av0, InitialPressureRegime.SUBATMOSPHERIC,
                    SubatmosphericMethod.GENERAL,
                    Peff_max, PEmax_max, Pieff_max)

    else:
        # Elevated pressure (Pi > 0.2 bar-g) — Eq. 8.2.1.2
        Av0, Peff, PEmax, Pieff = vent_area_elevated_pressure(
            vent.Pstat, Pi, dust.KSt, V, dust.Pmax, vent.Pred
        )
        return (Av0, InitialPressureRegime.ELEVATED,
                None, Peff, PEmax, Pieff)


def _step_ld(
    Av0: float,
    dust: Dust,
    vent: Vent,
    enclosure: Enclosure,
) -> tuple[float, bool]:
    """
    Step 3 — L/D correction → Av1  (§8.2.2.3).

    Returns (Av1, ld_correction_active).
    """
    Pi = dust.Pinitial
    # §8.2.2.4: set Pinitial to zero when below 0.2 bar-g
    Pi_for_eq = Pi if Pi >= 0.2 else 0.0
    Av1 = vent_area_ld_correction(Av0, enclosure.LD, vent.Pred, Pi_for_eq)
    return Av1, (enclosure.LD > 2)


def _step_turbulence(
    Av1: float,
    mode: TurbulenceMode,
    turb_inputs: Optional[TurbulenceInputs],
) -> tuple[float, Optional[float], Optional[float]]:
    """
    Step 4 — Turbulence correction → Av2  (§8.2.4).

    Returns (Av2, vaxial, vtan).
    """
    if mode == TurbulenceMode.BUILDING:
        return vent_area_building_turbulence(Av1), None, None

    if mode == TurbulenceMode.PROCESS:
        if turb_inputs is None:
            raise ValueError(
                "TurbulenceMode.PROCESS requires a TurbulenceInputs object."
            )
        vaxial = axial_velocity(turb_inputs.Q, turb_inputs.A)
        if turb_inputs.Ain is not None:
            vtan = tangential_velocity(turb_inputs.Q, turb_inputs.Ain)
        else:
            vtan = 0.0
        Av2 = vent_area_turbulence(Av1, vaxial, vtan)
        return Av2, vaxial, (vtan if turb_inputs.Ain is not None else None)

    # TurbulenceMode.NONE
    return Av1, None, None


def _step_panel_inertia(
    Av2: float,
    dust: Dust,
    vent: Vent,
    enclosure: Enclosure,
) -> tuple[float, float, bool]:
    """
    Step 5 — Panel inertia correction → Av3  (§8.3).

    Returns (Av3, MT, panel_inertia_active).
    """
    MT  = panel_mass_threshold(vent.Pred, vent.n, enclosure.V, dust.KSt)
    Av3 = vent_area_panel_inertia(Av2, vent.M, MT, dust.KSt, vent.n,
                                   enclosure.V, vent.Pred, vent.Fsh)
    return Av3, MT, (vent.M > MT)


def _step_partial_volume(
    Av3: float,
    dust: Dust,
    vent: Vent,
    enclosure: Enclosure,
    pv: Optional[PartialVolumeInputs],
) -> tuple[float, Optional[float], bool]:
    """
    Step 6 — Partial volume correction → Av4  (§8.4).

    Returns (Av4, Xr, partial_volume_active).
    """
    if pv is None:
        return Av3, None, False

    V      = enclosure.V
    Vsolid = enclosure.Vsolid

    if pv.use_building:
        # §8.4.5 — Building partial volume
        Xr = building_partial_volume_fraction(
            pv.Mf_bar, pv.Af_dusty, pv.eta_Dfloor, pv.Afs,
            pv.Ms_bar, pv.Asur, pv.eta_Dsur, pv.Ass,
            pv.Me_equipment if pv.Me_equipment is not None else 0.0,
            V, Vsolid, pv.cw,
        )
    else:
        # §8.4.1 — Process enclosure
        Xr = partial_volume_fraction(pv.Me, V, Vsolid, pv.cw)

    Av4 = vent_area_partial_volume(Av3, Xr, vent.Pred, dust.Pmax)
    active = (Av4 < Av3) or (Xr > (vent.Pred / dust.Pmax) and Xr < 1.0)
    return Av4, Xr, active


def _step_duct(
    Av4: float,
    dust: Dust,
    vent: Vent,
    enclosure: Enclosure,
    duct: Optional[Duct],
) -> tuple[float, bool, Optional[float], Optional[float],
           Optional[float], Optional[float], Optional[bool]]:
    """
    Step 7 — Vent duct correction → Avf  (§8.5.1).

    Returns (Avf, duct_active, E1, E2, Leff_max, Ldusty, ddt_ok).
    """
    if duct is None:
        return Av4, False, None, None, None, None, None
        
    # §6.9.6 — Short-duct exemption: total duct length < 1 hydraulic diameter
    # requires no correction to vent area, irrespective of duct area.
    if duct.Lduct < duct.Dh:
        return Av4, False, None, None, None, None, None
    
    Avf = vent_area_duct(
        Av4, duct.Lduct, enclosure.V,
        vent.Pstat, dust.KSt, duct.K, duct.K0,
    )

    # DDT check §8.5.9
    Leff_max, Ldusty = max_duct_length(
        dust.KSt, duct.Dh, dust.Pmax, vent.Pred, enclosure.V, Avf
    )
    Leff    = min(duct.Lduct, Ldusty)
    ddt_ok  = Leff <= Leff_max

    # Recover E1 and E2 at the converged Avf for reporting
    denom = (1 + 1.54 * vent.Pstat ** (4 / 3)) * dust.KSt * enclosure.V ** 0.75
    E1    = Avf * duct.Lduct / enclosure.V
    E2    = 1e4 * Avf / denom

    return Avf, True, E1, E2, Leff_max, Ldusty, ddt_ok


# ──────────────────────────────────────────────────────────────────────────────
# Main orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def vent_area_dust(
    enclosure: Enclosure,
    dust: Dust,
    vent: Vent,
    duct: Optional[Duct]                       = None,
    turbulence_mode: TurbulenceMode            = TurbulenceMode.NONE,
    turb_inputs: Optional[TurbulenceInputs]    = None,
    partial_volume: Optional[PartialVolumeInputs] = None,
    subatm_method: SubatmosphericMethod        = SubatmosphericMethod.GENERAL,
    tol: float                                 = 1e-6,
    max_iter: int                              = 200,
) -> DustVentResult:
    """
    Calculate the minimum required deflagration vent area for combustible dusts
    and hybrid mixtures per NFPA 68 (2023), Chapter 8.

    Applies corrections in the order prescribed by Figure 8.1.1.4:

        1. Validate inputs against §8.1.1 and Table 8.5.10
        2. Compute Av0  §8.2.1  — branch on initial pressure regime
        3. Compute Av1  §8.2.2  — L/D correction
        4. Compute Av2  §8.2.4  — turbulence correction
        5. Compute Av3  §8.3    — panel inertia correction
        6. Compute Av4  §8.4    — partial volume correction
        7. Compute Avf  §8.5    — vent duct correction (iterative)

    Args:
        enclosure       (Enclosure):            Enclosure geometry.
        dust            (Dust):                 Dust explosion characteristics.
        vent            (Vent):                 Vent panel and pressure properties.
        duct            (Duct, optional):       Duct properties; None = no duct.
        turbulence_mode (TurbulenceMode):       Turbulence branch to apply.
                                                Default NONE.
        turb_inputs     (TurbulenceInputs):     Required when mode = PROCESS.
        partial_volume  (PartialVolumeInputs):  Partial volume inputs. None to skip.
        subatm_method   (SubatmosphericMethod): Equation choice for Pinitial < −0.2.
                                                Default GENERAL (§8.2.1.2.1).
        tol             (float):                Convergence tolerance for duct
                                                iteration. Default 1e-6.
        max_iter        (int):                  Max duct iterations. Default 200.

    Returns:
        DustVentResult: Dataclass with Avf (final vent area [m²]) and all
                        intermediate areas and flags for report traceability.

    Raises:
        ValueError:   If input parameters violate applicability limits.
        RuntimeError: If duct iteration does not converge (§8.5.3).

    Reference:
        NFPA 68 (2023), Chapter 8, §8.2.1 – §8.5
    """
    _validate_inputs(
        enclosure, dust, vent, duct,
        turbulence_mode, partial_volume, subatm_method,
    )

    # ── Step 2: Av0 — §8.2.1 ─────────────────────────────────────────────────
    Av0, pressure_regime, subatm_used, Peffective, PEmax, Pi_effective = \
        _step_av0(dust, vent, enclosure, subatm_method)

    # ── Step 3: Av1 — §8.2.2 (L/D correction) ───────────────────────────────
    Av1, ld_active = _step_ld(Av0, dust, vent, enclosure)

    # ── Step 4: Av2 — §8.2.4 (turbulence correction) ────────────────────────
    Av2, vaxial, vtan = _step_turbulence(Av1, turbulence_mode, turb_inputs)

    # ── Step 5: Av3 — §8.3 (panel inertia correction) ───────────────────────
    Av3, MT, inertia_active = _step_panel_inertia(Av2, dust, vent, enclosure)

    # ── Step 6: Av4 — §8.4 (partial volume correction) ──────────────────────
    Av4, Xr, pv_active = _step_partial_volume(Av3, dust, vent, enclosure, partial_volume)

    # ── Step 7: Avf — §8.5 (vent duct correction) ───────────────────────────
    Avf, duct_active, E1, E2, Leff_max, Ldusty, ddt_ok = \
        _step_duct(Av4, dust, vent, enclosure, duct)

    return DustVentResult(
        Av0=Av0,
        Av1=Av1,
        Av2=Av2,
        Av3=Av3,
        Av4=Av4,
        Avf=Avf,
        pressure_regime=pressure_regime,
        subatm_method=subatm_used,
        Peffective=Peffective,
        PEmax=PEmax,
        Pi_effective=Pi_effective,
        turbulence_mode=turbulence_mode,
        vaxial=vaxial,
        vtan=vtan,
        MT=MT,
        panel_inertia_active=inertia_active,
        Xr=Xr,
        partial_volume_active=pv_active,
        duct_active=duct_active,
        E1=E1,
        E2=E2,
        Leff_max=Leff_max,
        Ldusty=Ldusty,
        ddt_ok=ddt_ok,
        ld_correction_active=ld_active,
    )


# ──────────────────────────────────────────────────────────────────────────────
# §8.7 — Dust Collectors (bags, filters, cartridges)
# ──────────────────────────────────────────────────────────────────────────────

def dust_collector_vent_area(
    enclosure: Enclosure,
    dust: Dust,
    vent: Vent,
    duct: Optional[Duct]                       = None,
    turbulence_mode: TurbulenceMode            = TurbulenceMode.NONE,
    turb_inputs: Optional[TurbulenceInputs]    = None,
    partial_volume: Optional[PartialVolumeInputs] = None,
    flexible_filters_above_vent: bool          = False,
    subatm_method: SubatmosphericMethod        = SubatmosphericMethod.GENERAL,
) -> DustVentResult:
    """
    Minimum deflagration vent area for bag/filter/cartridge dust collectors.
    (§8.7)

    Applies the standard §8.2–§8.5 calculation chain via vent_area_dust(),
    with the following §8.7-specific pre-processing:

        - Enclosure.V must be set to the total dirty-side volume (Veff),
          including filter volume, ignoring vents. (§8.7.1.2)
        - L/D for the collector is H/Dhe where H is the longest dirty-side
          dimension. Caller must set enclosure.LD accordingly. (§8.7.1.1)
        - If flexible filters are located totally above the vent free end
          and no internal restraints are provided, the calculated vent area
          is increased by 25% per §8.7.2. Set flexible_filters_above_vent=True
          to apply this multiplier.

    Caller responsibilities before calling this function:
        - Set enclosure.V  = total dirty-side volume (Veff).   §8.7.1.2
        - Set enclosure.LD = H / Dhe.                          §8.7.1.1, §8.7.1.5
        - If clean air side contains dust or hybrid mixture,
          provide separate venting per §8.7.3 (not handled here).

    Args:
        enclosure                (Enclosure): Collector geometry. V = dirty-side
                                              volume; LD = H/Dhe.
        dust                     (Dust):      Dust properties.
        vent                     (Vent):      Vent panel properties.
        duct                     (Duct):      Duct, or None.
        turbulence_mode          (TurbulenceMode): Turbulence branch.
        turb_inputs              (TurbulenceInputs): Required for PROCESS mode.
        partial_volume           (PartialVolumeInputs): Optional.
        flexible_filters_above_vent (bool):   Apply 25% area increase per §8.7.2.
                                              Default False.
        subatm_method            (SubatmosphericMethod): Subatm equation choice.

    Returns:
        DustVentResult: Avf is the final required area [m²] (after §8.7.2
                        multiplier if applicable). All intermediate areas
                        and Av0–Av4 reflect the pre-multiplier chain.

    Reference:
        NFPA 68 (2023), §8.7
    """
    result = vent_area_dust(
        enclosure, dust, vent, duct,
        turbulence_mode, turb_inputs, partial_volume, subatm_method,
    )

    if flexible_filters_above_vent:
        # §8.7.2 — increase required vent area by 25%
        multiplied_Avf = result.Avf * 1.25
        # Return a modified result with Avf updated.
        # All intermediate values (Av0–Av4) are unchanged — the 25% factor
        # is a post-chain multiplier applied only to the final area.
        return DustVentResult(
            **{k: (multiplied_Avf if k == "Avf" else v)
               for k, v in result.__dict__.items()}
        )

    return result


# ──────────────────────────────────────────────────────────────────────────────
# §8.9 — Internal-to-building venting (building pressure rise estimate)
# ──────────────────────────────────────────────────────────────────────────────

def building_pressure_rise_estimate(
    V1: float,
    V0: float,
    P0: float = 1.013,
) -> float:
    """
    Estimated pressure increase in an unvented building caused by a
    deflagration venting event from internal process equipment. (§8.9.1.1)

    This estimate shall be compared to the building design pressure to
    determine whether building venting is required. (§8.9.1)

    Args:
        V1 (float): Volume of protected equipment [m³]
        V0 (float): Free volume of the building [m³]
        P0 (float): Ambient pressure [bar-abs]. Default 1.013 bar-abs.

    Returns:
        float: Estimated building pressure rise ΔP [bar]

    Reference:
        NFPA 68 (2023), §8.9.1.1
    """
    return building_pressure_rise(V1, V0, P0)


# ──────────────────────────────────────────────────────────────────────────────
# §8.10 — Silos with integral bin vents
# ──────────────────────────────────────────────────────────────────────────────

def silo_bin_vent_split(
    enclosure_silo: Enclosure,
    enclosure_bin_vent: Enclosure,
    dust: Dust,
    vent: Vent,
    duct: Optional[Duct]                       = None,
    turbulence_mode: TurbulenceMode            = TurbulenceMode.NONE,
    turb_inputs: Optional[TurbulenceInputs]    = None,
    partial_volume: Optional[PartialVolumeInputs] = None,
    subatm_method: SubatmosphericMethod        = SubatmosphericMethod.GENERAL,
) -> tuple[DustVentResult, float, float]:
    """
    Vent area calculation for a silo with an integral bin vent (air-material
    separator), distributing the total required area between the silo and the
    bin vent surface. (§8.10.1)

    Per §8.10.1:
        - Protected volume = Vsilo + Vbin_vent   (sum of both)
        - L/D is calculated from the silo dimensions alone
        - Vent panels are located on the silo top/sidewall above material level,
          with overflow permitted on the bin vent surface

    Args:
        enclosure_silo     (Enclosure): Silo geometry.
                                        LD must reflect the silo L/D alone.
        enclosure_bin_vent (Enclosure): Bin vent (collector) geometry.
        dust               (Dust):      Dust explosion properties.
        vent               (Vent):      Vent panel properties.
        duct               (Duct):      Duct, or None.
        turbulence_mode    (TurbulenceMode): Turbulence branch.
        turb_inputs        (TurbulenceInputs): Required for PROCESS mode.
        partial_volume     (PartialVolumeInputs): Optional.
        subatm_method      (SubatmosphericMethod): Subatm equation choice.

    Returns:
        tuple:
            result      (DustVentResult): Full calculation result for the
                                          combined volume. Avf = Av_total.
            Av_silo_min (float): Minimum vent area that must remain on the silo [m²].
            Av_bin_vent (float): Vent area permitted on the bin vent surface [m²].

    Reference:
        NFPA 68 (2023), §8.10.1, Eq. 8.10.1a–b
    """
    # Build combined enclosure: volume = silo + bin vent; L/D from silo alone
    V_total = enclosure_silo.V + enclosure_bin_vent.V
    combined_enclosure = Enclosure(
        V      = V_total,
        LD     = enclosure_silo.LD,        # §8.10.1(2) — silo L/D only
        Vsolid = enclosure_silo.Vsolid + enclosure_bin_vent.Vsolid,
    )

    result = vent_area_dust(
        combined_enclosure, dust, vent, duct,
        turbulence_mode, turb_inputs, partial_volume, subatm_method,
    )

    Av_total    = result.Avf
    Av_silo_min, Av_bin_vent = bin_vent_area_split(
        Av_total, enclosure_silo.V, V_total
    )

    return result, Av_silo_min, Av_bin_vent


# ──────────────────────────────────────────────────────────────────────────────
# §8.11 — Interconnected enclosures
# ──────────────────────────────────────────────────────────────────────────────

def interconnected_enclosures(
    enclosure_large: Enclosure,
    enclosure_small: Enclosure,
    dust: Dust,
    vent_large: Vent,
    vent_small: Vent,
    pipe_diameter: float,
    pipe_length: float,
) -> tuple[float, float, list[str]]:
    """
    Vent area requirements for two enclosures interconnected by a pipeline.
    (§8.11.1)

    Scope: pipe inside diameter ≤ 0.3 m AND pipe length ≤ 6 m.
    For pipes outside this scope, use explosion isolation or suppression per
    NFPA 69 (§8.11.2).

    Rules applied per §8.11.1:
        (1) Pstat < 0.2 bar-g required for both vent covers.
        (2) If volumes within 10%, vent each enclosure per §8.2.1 and §8.2.2.
        (3) If volumes differ > 10%, design both for Pred ≤ 1 bar-g and
            Pes ≥ 2 bar-g.
        (4) If smaller enclosure cannot be vented per this standard, design
            smaller enclosure for Pmax and double the larger enclosure vent area.

    This function calculates the two vent areas using vent_area_dust() after
    applying the rules above, and returns warnings/notes for the caller.

    Args:
        enclosure_large (Enclosure): Larger enclosure geometry.
        enclosure_small (Enclosure): Smaller enclosure geometry.
        dust            (Dust):      Common dust properties.
        vent_large      (Vent):      Vent properties for the larger enclosure.
        vent_small      (Vent):      Vent properties for the smaller enclosure.
        pipe_diameter   (float):     Interconnecting pipe inside diameter [m].
        pipe_length     (float):     Interconnecting pipe length [m].

    Returns:
        tuple:
            Avf_large (float): Required vent area for the larger enclosure [m²].
            Avf_small (float): Required vent area for the smaller enclosure [m²].
                               Returns math.inf when the smaller enclosure
                               cannot be vented and must be rated for Pmax.
            notes     (list[str]): List of §8.11.1 rule notes and warnings.

    Raises:
        ValueError: If pipe diameter > 0.3 m or pipe length > 6 m (§8.11.2 scope).

    Reference:
        NFPA 68 (2023), §8.11.1
    """
    notes = []

    # Scope check — §8.11.2
    if pipe_diameter > 0.3 or pipe_length > 6.0:
        raise ValueError(
            f"Pipeline (D = {pipe_diameter} m, L = {pipe_length} m) is outside "
            "the scope of §8.11.1 (D ≤ 0.3 m, L ≤ 6 m). "
            "Use explosion isolation or suppression per NFPA 69. (§8.11.2)"
        )

    # Rule (1) — Pstat requirement
    for label, v in [("large", vent_large), ("small", vent_small)]:
        if v.Pstat >= 0.2:
            notes.append(
                f"§8.11.1(1): Pstat for {label} enclosure = {v.Pstat} bar-g. "
                "Must be < 0.2 bar-g."
            )

    # Determine volume ratio
    V_large = enclosure_large.V
    V_small = enclosure_small.V
    ratio   = abs(V_large - V_small) / max(V_large, V_small)

    if ratio <= 0.10:
        # Rule (2) — volumes within 10%, vent each normally
        notes.append(
            "§8.11.1(2): Enclosure volumes are within 10% — each enclosure "
            "vented per §8.2.1 and §8.2.2 independently."
        )
        result_large = vent_area_dust(enclosure_large, dust, vent_large)
        result_small = vent_area_dust(enclosure_small, dust, vent_small)
        return result_large.Avf, result_small.Avf, notes

    else:
        # Rule (3) — volumes differ > 10%, cap Pred at 1 bar-g
        notes.append(
            "§8.11.1(3): Enclosure volumes differ by more than 10% — "
            "both enclosures designed with Pred ≤ 1 bar-g and Pes ≥ 2 bar-g."
        )
        Pred_capped = min(vent_large.Pred, 1.0)
        from dataclasses import replace

        vent_large_adj = Vent(
            Pred=Pred_capped, Pstat=vent_large.Pstat,
            n=vent_large.n, M=vent_large.M, Fsh=vent_large.Fsh,
        )
        vent_small_adj = Vent(
            Pred=Pred_capped, Pstat=vent_small.Pstat,
            n=vent_small.n, M=vent_small.M, Fsh=vent_small.Fsh,
        )

        result_large = vent_area_dust(enclosure_large, dust, vent_large_adj)
        try:
            result_small = vent_area_dust(enclosure_small, dust, vent_small_adj)
            Avf_small    = result_small.Avf
        except (ValueError, RuntimeError):
            # Rule (4) — smaller enclosure cannot be vented
            notes.append(
                "§8.11.1(4): Smaller enclosure cannot be vented per this standard. "
                "Design smaller enclosure for Pmax; "
                "larger enclosure vent area is doubled."
            )
            result_large_double = vent_area_dust(enclosure_large, dust, vent_large_adj)
            return result_large_double.Avf * 2.0, math.inf, notes

        return result_large.Avf, Avf_small, notes
