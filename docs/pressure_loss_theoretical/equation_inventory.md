# Pressure Loss (Theoretical): equation inventory (PLT-01)

Cell-referenced inventory of Keven's dilute-phase pressure-drop workbook, matched against Agarwal (2005) and
Klinzing et al. (2010). Foundation for PLT-02 to PLT-08. Written 2026-10-20 from flowguard `main` @ 3e14de4.

Conventions used in this file:

- **Units in the tables are the sheet's own** (rule 4 of the item). SI conversion happens in the library items; the
  fixtures in `tests/fixtures/pressure_loss_theoretical/` are already in SI (Pa, m, m/s, kg/s, K).
- Math forms use the Klinzing symbols of section 11 (the binding nomenclature).
- "Match" = same physical relation. "Partial" = same relation, different form or constants (difference stated).
  "No match" = not in Klinzing. Where Agarwal, the sheet and Klinzing differ, all are recorded, none is picked.
- Equation and page numbers are the printed ones. The PDF text layer of Klinzing garbles Greek symbols and some
  exponents; every symbol or exponent marked **(verify)** was read from context and should be checked against the page
  image when the item that uses it is implemented.
- No prose is copied from the sources; equation forms, numbers and references only.

## 1. Sources

| Ref | Source | Notes |
|---|---|---|
| WB | `2026-02-27 Calculation_Dilute_Phase_Pressure_Drop_Zenz_Othmer_Method.xlsm` (folder `~/flowguard-app/docs_for_claude_code/Pressure drop theoretical/`) | sheets Pressure, Vacuum, Notes, Changelog. Last changelog entry 2026-02-27 |
| DOC | `Air-Systems Pressure Drop Calcultion.docx` | Keven's partial write-up, sections 1 to 4, 19 numbered equations, 2 figures (one is a variable-relation diagram) |
| AG | A. T. Agarwal, "Theory and Design of Dilute Phase Pneumatic Conveying Systems", *Powder Handling & Processing* **17**(1), pp. 18-23, **January/February 2005** | the PDF header and DOC reference [1] both say Jan/Feb; the item text says April 2005 (see open question 12) |
| KL | G. E. Klinzing, F. Rizk, R. Marcus, L. S. Leung, *Pneumatic Conveying of Solids: A Theoretical and Practical Approach*, **Third edition**, Particle Technology Series vol. 8, Springer, 2010. ISBN 978-90-481-3608-7, DOI 10.1007/978-90-481-3609-4 | Keven confirmed this edition is the one to cite (comment 2026-10-21) |
| ZO | F. A. Zenz and D. F. Othmer, *Fluidization and Fluid-Particle Systems*, Reinhold, 1960 | cited by AG and KL; not in the folder, not read |

The workbook cites its own sources in cells B1:B2: "Zenz Othmer method described by Agarwal" and "Solid friction based on
Klinzing & Rizk and S.S. Mallick". Mallick is not cited or listed anywhere in KL (searched).

## 2. Sheet map

Both calculation sheets (`Pressure`, `Vacuum`, both B1:AP53) have the same layout. The formulas of the section table
are identical (checked cell by cell); the differences are listed in section 2.5.

### 2.1 Blocks

| Block | Cells | Content |
|---|---|---|
| Header notes | B1:B3 | method, source, "no temperature change; all calculations at 25 °C" |
| Instructions | H5:H6 | Pressure sheet only: "press Goal Seek; solves the inlet pressure for atmospheric pressure at the outlet" |
| Inputs and constants | B9:F38 | labels in B, values in C, unit in D, alternative-unit display in E:F |
| Results | B39:F44 | Pressure: C40 total ΔP, C42 outlet gas velocity, C43 airflow at blower exit. Vacuum: C40 total ΔP, C42 outlet gas velocity, C43 material velocity at outlet (`C42*C25`), C44 inlet airflow |
| Inlet air density calc | B49:D53 | p_sat (C50), x_w (C51), M (C52), ρ (C53) |
| Layout table | H10:N33 | 23 fixed section rows: section #, component, orientation, length, ID, equivalent length, cumulative equivalent length |
| Pressure-drop table | P10:AF33 | 23 rows of terms and gas state; row 34 holds column totals (`Q34:W34`) and the outputs `AC34`/`AE34` (Pressure) or `AD34` (Vacuum) |
| Charts | one per sheet | gas velocity and cumulative ΔP against equivalent distance. Ranges: x = `N11:N30`, ΔP = `AF11:AF30`, velocity = `AD11:AD34` (24 points against 20 x values), so sections 21-23 are not plotted |
| Notes sheet | B64:E70 plus pasted pictures | pipe ID table (see 2.4) and six pictures (section 2.4) |
| Changelog sheet | B2:D5 | four entries, 2024-12-17 to 2026-02-27, author KMLF |

Named ranges: `InletPressure` = `Pressure!$C$33`, `outletPressure` = `Pressure!$AC$34`. Only `InletPressure` is used in a formula
(`Pressure!C51`, `C53`). The Vacuum sheet uses `C33` directly.

Cell comments (the workbook's own validity limits; see section 12): B21 "Rizk method better suited for fine powders below
200 microns"; B27 "Should be between 0.4 & 4"; B31 "Temperature limitation between 1 and 100 °C" (Pressure sheet
only); B34 "https://tlk-energy.de/en/tools/air-density"; B35 "1.84E-05 @ 25 °C"; B50 "Antoine Equation" (Pressure only).

### 2.2 Inputs (column C), with units as in the sheet

| Cell | Label | Pressure sheet | Vacuum sheet | Unit |
|---|---|---|---|---|
| C9 | Type of conveying | Pressure | Vacuum | drop-down; **no formula reads it**, it is a label only |
| C11 | I.D. | `=(8-(2*0.12))*25.4/1000` = 0.197104 | `=(3-(2*0.12))*25.4/1000` = 0.070104 | m (OD in and wall in typed into the formula) |
| C12 | Material (pipe) | Galv. | Galv. | text, unused |
| C13 | Roughness (ε) | 4.6e-5 | 4.6e-5 | m |
| C15 | Eq. length of bend | 6 | 6 | m |
| C18 | Mass flow rate (solids) | 800 | 800 | kg/h |
| C19 | Bulk density | 178 | 200 | kg/m³ |
| C20 | Particle diameter | 0.00015 | 0.00015 | m |
| C25 | Slip ratio | 0.9 | 0.9 | - |
| C26 | Solids friction factor | correlation (E07) = 0.08445 | typed 0.009 | - |
| C29 | Gas | Air | Air | text, unused |
| C30 | Inlet velocity | 35 | 25 | m/s |
| C31 | Temperature | 25 | 25 | °C |
| C32 | % RH | 50 | 50 | % |
| C33 | Inlet pressure | 121567.118... (pasted by Goal Seek) | 100700 (typed) | Pa |
| C35 | Dynamic viscosity | `=18.37*10^-6` | same | Pa·s |

Derived cells: C14 (k/D), C21 (δ, "Gamma"), C22 (χ, "Beta"), C23 (v_s, "Usalt"), C24 ("Pickup velocity" = `C30*C25`),
C27 (K), C34 (`=C53`), C36 (Re), C37 (f_L), C38 (μ, solid loading ratio), C50:C53.

### 2.3 State handed from section to section

Row r (section r-10) reads its inlet state from row r-1 and writes its outlet state:

```
X_r = Y_{r-1}                      (T in; X11 = C31)
Z_r = AA_{r-1}                     (rho in; Z11 = C34)
AB_r = AC_{r-1}                    (p in; AB11 = C33)
AD_r = AE_{r-1}                    (v in; AD11 = C30)
AC_r = AB_r - W_r                  (p out)
AA_r = AC_r / (287.05*(273.15+Y_r))(rho out)
AE_r = AD_r * Z_r / AA_r           (v out)
AF_r = AF_{r-1} + W_r              (cumulative ΔP)
```

Y (outlet temperature, column Y) is **typed 25 in every row**, not linked to C31 (see section 9).
Each section is a single explicit step: every term of the section is evaluated at the section's **inlet** density and
velocity (no averaging, no sub-steps). Rows whose equivalent length `M` is 0 return 0 for every term.

### 2.4 Notes sheet

- B64:E70: pipe ID = (nominal OD in − 2 × wall in) × 25.4/1000 for 3, 3.5, 4 in at 16 ga (wall 0.065 in) and 11 ga
  (wall 0.12 in). Not linked to any calculation. The 0.12 in wall used in C11 matches the 11 ga row.
- Pasted pictures (viewed): (a) pipe roughness design values table, "Table 8.2" (commercial or welded steel
  4.6e-5 m, galvanized iron 1.5e-4 m, etc.; the book is not named in the picture, DOC cites Munson et al.); (b) equivalent-length table: short radius 90° bend 12 m,
  long radius 90° bend 6 m, 45° diverter valve 6 m, 30° diverter valve 3 m, rubber flexible hose 5 × pipe length, bends
  under 90°: 12·angle/90, special bends (Hammertek, Gamma) over 12 m (12×1.1 to 12×1.2); (c) material/air ratio
  ranges: dilute phase 5-15, intermediary 10-30, dense phase > 30; (d) AG §2.4 text on the slip factor
  (0.8 coarse, 0.9 fine, range 0.7-0.95); (e) AG §2.2 text on K (0.4 to 4.0); (f) a screenshot of a video comment thread
  stating Ve(-) = 1.8·Ve(+), vacuum systems needing higher velocity than pressure systems (not used by any formula).
- Two embedded Paint objects (OLE, `PBrush`) and two EMF previews are the same kind of picture; not decoded.

### 2.5 Differences between the Pressure and Vacuum sheets (besides the Goal Seek)

1. C11 pipe ID (8 in OD vs 3 in OD, same wall).
2. C19 bulk density 178 vs 200; C30 inlet velocity 35 vs 25.
3. **C26 solids friction factor: correlation (Pressure) vs constant 0.009 (Vacuum).**
4. C33: Pressure value is pasted by Goal Seek, Vacuum typed 100700.
5. C51 uses the named range `InletPressure` (Pressure) or `C33` (Vacuum): same cell.
6. Result block: Pressure reports outlet pressure (`AC34`) and airflow at blower exit; Vacuum reports material velocity and
   has no outlet-pressure cell (the pump suction pressure is `AC33`, row 33, not summarised).
7. Section tables (rows 11-33): different component, orientation and length entries (section 2.6); formulas identical.
8. Pressure!B31 and B50 have a cell comment, Vacuum does not.

### 2.6 Layouts in the cached cases

| Section | Pressure sheet | Vacuum sheet |
|---|---|---|
| 1 | Pipe, Horizontal, 1.5 m | Pipe, Vertical, `=20/3.3` = 6.0606 m |
| 2 | 90° Bend, Horizontal to Vertical (6 m) | 90° Bend, Horizontal to Vertical (6 m) |
| 3 | Pipe, Vertical, 5 m | Pipe, Vertical, 5 m |
| 4 | 90° Bend, Vertical to Horizontal (6 m) | 90° Bend, Vertical to Horizontal (6 m) |
| 5 | Pipe, Horizontal, 2 m | Pipe, Horizontal, `=10/3.3` = 3.0303 m |
| 6-23 | empty (equivalent length 0) | empty |

The Vacuum lengths are typed as feet divided by 3.3 (3.28084 in reality, so 20 ft becomes 6.0606 m rather than 6.096 m).

## 3. Equation table

Sheet units. "Target" is the PLT item that implements the relation. Row numbers r run 11-33; examples cite row 11.

### 3.1 Inputs and gas state

| ID | Description | Excel (cell) | Math form | Units in sheet | Source | Klinzing match | Target |
|---|---|---|---|---|---|---|---|
| E01 | Pipe inner diameter | `=(OD-2*0.12)*25.4/1000` (C11) | D = D_outer − 2 t_w | in → m | DOC Eq. 18; Keven | no equation (D defined in nomenclature, p. xiii) | PLT-06 input |
| E02 | Relative roughness | `=C13/C11` (C14) | k/D | m/m | Keven | match (k/D axis of Fig. 2.2, p. 47) | PLT-03 |
| E03 | Rizk exponent δ ("Gamma") | `=1440*C20+1.96` (C21) | δ = 1.44 d + 1.96 with d in mm | d in m (so 1440) | AG: not in AG; cell comment cites Rizk | **match** KL Eq. 5.41 (p. 182); the sheet's 1440 is 1.44 × 1000 for d in m | PLT-05 |
| E04 | Rizk exponent χ ("Beta") | `=(1100*C20)+2.5` (C22) | χ = 1.1 d + 2.5 with d in mm | d in m | as E03 | **match** KL Eq. 5.41 (p. 182) (χ glyph garbled, verify) | PLT-05 |
| E05 | Saltation gas velocity v_s ("Usalt") | `=((4*(C18/3600)*10^C21*9.81^(C22/2)*C11^(C22/2-2))/(PI()*C34))^(1/(C22+1))` (C23) | v_s = [4 ṁ_s 10^δ g^(χ/2) D^(χ/2−2) / (π ρ)]^(1/(χ+1)) | m/s | Keven (algebraic solution of Rizk for v_s) | **match** KL Eq. 5.41 solved for v_s with μ = 4 ṁ_s/(π D² ρ v); identical algebra. **Not used by any pressure-drop term** | PLT-05 |
| E06 | Solids velocity at pickup | `=C30*C25` (C24, "Pickup Velocity") | c = (c/v) v | m/s | AG §2.4 (c = 0.8-0.9 v) | partial: KL defines slip w = v − c (Eq. 4.43, p. 96) and c/v (§6.7.4, p. 222), no fixed ratio. Not used by any term (the terms use `AD*C25` directly) | PLT-05 |
| E07 | Solids friction factor, correlation (Pressure) | `=(55.5*C11^1.1)/(C30^0.64*C20^0.26*C19^0.91)` (C26) | λ*_z = 55.5 D^1.1 / (v^0.64 d^0.26 ρ_b^0.91) | D m, v m/s, d m, ρ_b kg/m³ (empirical, not dimensionless-consistent) | Keven ("Klinzing & Rizk and S.S. Mallick", B2) | **no match.** KL Table 4.5 (p. 97) lists other correlations (Stemerding 0.003, Konno-Saito, Yang, Stegmaier, ...) none of this form | PLT-05 |
| E08 | Solids friction factor, constant (Vacuum) | typed 0.009 (C26) | λ*_z = 0.009 | - | Keven | no match (for reference: Stemerding's λ*_z/4 = 0.003 in KL Table 4.5; the basis of the sheet's λ_s relative to λ*_z is unknown, open question 6) | PLT-05 |
| E09 | "Friction multiplier K (Agarwal)" | `=C26*C25/C37` (C27) | K = λ_s (c/v) / f_L | - | AG §2.2, Eq. 3 (K defined as experimental constant, 0.4-4.0) | no match (KL has no K). **Not used by any term** (see D03). Pressure value 19.31 is far outside the 0.4-4 range of its own cell comment; Vacuum 1.557 is inside | PLT-05 |
| E10 | Water saturation pressure | `=(10^(8.07131-(1730.63/(233.42+C31))))*133.3` (C50) | p_sat = 133.3 · 10^(A − B/(C + t)), A = 8.07131, B = 1730.63, C = 233.42, t in °C | Pa (mmHg × 133.3) | cell comment "Antoine Equation"; coefficient source not recorded | no match | PLT-02 |
| E11 | Water vapour fraction | `=(C32/100)*(C50/C33)` (C51, label "mass fraction") | x_w = (φ/100) p_sat / p | - | DOC Eq. 11 (same form, same wrong label) | no match. This is a mole fraction, not a mass fraction | PLT-02 |
| E12 | Mixture molar mass | `=(28.96/1000)*(1-C51)+(18.02/1000)*C51` (C52) | M_w = (1 − x_w) M_air + x_w M_water | kg/mol | DOC Eq. 12 | partial (KL lists M_w, no humid-air formula) | PLT-02 |
| E13 | Inlet gas density (humid) | `=C33*C52/(8.314*(C31+273.15))` (C53, C34) | ρ = p M_w / (R_u T) | kg/m³ | DOC Eq. 13; AG §3.2 uses 28 p /(19.32 T) (imperial, M = 28) | **match** KL ideal-gas form ρ = p/(R T), Eq. 6.58 (p. 218) with R = R_u/M_w; humid M_w is an addition | PLT-02 |
| E14 | Dynamic viscosity | `=18.37*10^-6` (C35) | η = 18.37e-6 (constant, "1.84E-05 @ 25 °C") | Pa·s | Keven; DOC Eq. 9 gives Sutherland (μ0 1.716e-5, T0 273 K, S 111 K) = 1.838e-5 at 25 °C | no match (KL gives no air viscosity correlation in the sections read) | PLT-02 |
| E15 | Reynolds number | `=C34*C30*C11/C35` (C36) | Re = ρ v D / η at the **line inlet**, then kept constant | - | AG §2.1 and §3.4.1 ("keep this factor constant", p. 21) | **match** (KL nomenclature Re = v D ρ/η, p. xv) | PLT-03 |
| E16 | Fanning friction factor | `=(IF(C36>4000,0.25/(LOG10(C13/(3.7*C11)+5.74/C36^0.9))^2,64/C36))/4` (C37) | f_L = λ_L / 4; turbulent λ_L = 0.25 / [log10(k/(3.7 D) + 5.74/Re^0.9)]² (Swamee-Jain); laminar λ_L = 64/Re | - | DOC Eq. 19 (Swamee-Jain, Darcy form; validity 1e-6 ≤ k/D ≤ 1e-2, 5e3 ≤ Re ≤ 1e8); AG Eq. 7 | **partial**: KL gives Darcy λ_L (Eq. 2.41 p. 46) with laminar 64/Re (Eq. 2.42 p. 46), Blasius (Eq. 2.44 p. 47), Koo (Eq. 2.45 p. 47: f_L = 0.0014 + 0.125 Re^−0.32), smooth-pipe only, no roughness. Sheet formula is roughness-dependent. Sheet vs AG Eq. 7: numerically the same relation (see D01) | PLT-03 |
| E17 | Solids loading ratio | `=(C18/3600)/(((PI()*C11^2)/4)*C30*C34)` (C38) | μ = ṁ_s / (A v ρ) = ṁ_s/ṁ_f at inlet | kg/kg | AG §2.5 (R) | **match** KL μ = ṁ_s/ṁ_f (nomenclature, p. xv). Constant along the line, correct because ṁ_f is constant | PLT-05 |

### 3.2 Section table terms (row 11 shown)

| ID | Description | Excel (cell) | Math form (section k, L_eq = M) | Units | Source | Klinzing match | Target |
|---|---|---|---|---|---|---|---|
| E18 | Equivalent length of section | `=IF(I11="90° Bend",$C$15,IF(I11="45° Bend",$C$15/2,IF(I11="30° Bend",$C$15/3,K11)))` (M11) | L_eq = 6 m (90°), 3 m (45°), 2 m (30°), else the typed length | m | AG §2.3 (40 D or 20 ft, whichever is more, for 90° long radius; angle/90 scaling for bends under 90°) | **partial**: KL Table 2.8 (p. 49) gives equivalent lengths in m by size for compressed-air fittings, about 12 D for a 50 mm long 90° bend (different basis); KL Eq. 6.45c (p. 221) has a separate bend term with 2R_b/D | PLT-03, PLT-07 |
| E19 | Cumulative equivalent length | `=M11`, then `=N11+M12` (N) | L_eq,cum,k = Σ L_eq | m | Keven (x-axis of the charts) | no match | PLT-06 |
| E20 | Solids acceleration Δp_A | section 1: `=IF(M11>0,(($C$18/3600)/((PI()*L11^2)/4))*(AD11*$C$25),0)`; sections 2+: `...*((AD12-AD11)*$C$25)` (Q) | k = 1: Δp_A = G_s (c/v) v_in,1; k > 1: Δp_A = G_s (c/v) (v_in,k − v_in,k−1); G_s = ṁ_s/A | Pa | AG Eq. 1 (p. 19) and worksheet 3 (p. 23); DOC Eq. 5 | **match** (form): KL Eq. 6.69 (p. 219) integrated to Eq. 6.70/6.71 (p. 220), Δp_A = μ ρ v c = G_s c; KL Eq. 6.47: Δp_A = 0 in steady state, Eq. 4.54 (p. 102) is a simplified form (verify glyphs). **Departure D05** (inlet-based and lagged by one section) | PLT-05 |
| E21 | Gas friction Δp_L | `=IF(M11>0,(4*$C$37*M11*Z11*AD11^2)/(2*L11),0)` (R) | Δp_L = 4 f_L L_eq ρ v² / (2 D) = λ_L L_eq ρ v²/(2 D) | Pa | AG Eq. 2 (p. 19, imperial); DOC Eq. 1 | **match** KL Eq. 2.41 (p. 46) and Eq. 6.50 (p. 216), Darcy λ_L; Fanning f_L: Eq. 2.45 note and Eq. 4.47 note (p. 99) | PLT-03 |
| E22 | Solids friction Δp_Z | `=IF(M11>0,(C$38*C$26*Z11*AD11^2*M11)/(2*L11),0)` (S) | Δp_Z = μ λ_s ρ v² L_eq / (2 D), λ_s = value of C26 | Pa | DOC Eq. 3; AG Eq. 3 is different (D02, D03) | **partial**: same form as KL Eq. 4.48 (p. 99) / Eq. 6.38 (p. 213), Δp_Z = λ_Z ρ v² L/(2D), if λ_Z is taken as μ λ_s. KL Eq. 4.49 (p. 99) builds λ_Z from λ*_z with c/v and Froude terms (verify glyphs); the sheet uses none of them. KL Eq. 4.37 (p. 94) uses c² (or slip velocity), the sheet uses v² | PLT-05 |
| E23 | Gas elevation | `=IF(M11>0,IF(J11="Vertical",Z11*9.81*M11,0),0)` (T) | Δp_G,gas = ρ g L_eq if orientation = "Vertical", else 0 | Pa | AG Eq. 4 (p. 19); DOC Eq. 2 | **match** KL Eq. 6.72 (p. 220) dp = ρ g dZ (static fluid term also in Eq. 4.37, p. 94). Departures: D09, D10 | PLT-03 |
| E24 | Solids elevation | `=IF(M11>0,IF(J11="Vertical",(M11*($C$18/3600)*9.81)/(((PI()*L11^2)/4)*(AD11*0.8)),0),0)` (U) | Δp_G,solids = G_s g L_eq / (0.8 v) | Pa | AG Eq. 5 (p. 19, V_p = 0.8 V_g typical); DOC Eq. 4 | **match** (form): KL Eq. 6.53/6.54 (p. 217), weight of suspended solids, ρ′ g Z with ρ′ = ρ_p (1 − ε) = G_s/c (Eq. 4.40-4.41, p. 96). The 0.8 is hard-coded, not C25 (D07) | PLT-05 |
| E25 | Miscellaneous (inline equipment) | column V is empty (header "Misc.") | Δp_misc | Pa | AG Eq. 6 (p. 19; example 0.2 psi dust collector, p. 21); DOC Eq. 7 | **partial**: KL Eq. 6.45 (p. 215) has Δp_separator + Δp_valves | PLT-06 |
| E26 | Section total | `=SUM(Q11:V11)` (W) | Δp_k = Δp_A + Δp_L + Δp_Z + Δp_G,gas + Δp_G,solids + Δp_misc | Pa | AG ΔP_T equation (p. 19); DOC Eq. 8 | **match** KL Eq. 6.46 / 6.45a (pp. 216, 221): Δp_transport = Δp_L + Δp_A + (Δp_Z + Δp_G) + Δp_B. The sheet has no separate bend term (bends are equivalent length inside Δp_L and Δp_Z). Total corrected in the 2026-02-27 changelog | PLT-06 |
| E27 | Outlet pressure | `=AB11-W11` (AC) | p_out = p_in − Δp_k | Pa | AG §3.4.2 (p. 22) | match (KL Eq. 6.65 integrated, p. 219) | PLT-06 |
| E28 | Outlet gas density | `=AC11/(287.05*(273.15+Y11))` (AA) | ρ_out = p_out / (R T), R = 287.05 J/(kg K) (dry air) | kg/m³ | AG §3.4.2 (p. 22) uses 28 p/(19.32 T) | **match** isothermal ρ = ρ1 p/p1 (KL Eq. 6.60, p. 218) in form. **Departure D08**: dry-air R here vs humid M_w in E13 | PLT-02 |
| E29 | Outlet gas velocity | `=AD11*(Z11/AA11)` (AE) | v_out = v_in ρ_in / ρ_out | m/s | AG §3.4.2 (p. 22); DOC Eq. 15 | **match** KL Eq. 6.59 (p. 218) v = v1 p1/p (same as continuity at constant ṁ_f, A) | PLT-06 |
| E30 | Cumulative ΔP and totals | `=AF10+W11` (AF); `=SUM(Q11:Q33)` etc. (row 34) | Σ over sections | Pa | AG §3.5 | match | PLT-06 |
| E31 | Goal seek | VBA `GoalSeekPressure` (section 7) | p_in such that p_out(AC34) = 100700 Pa | Pa | Keven | no match | PLT-06 |
| E32 | Display conversions | `E`/`F` columns, e.g. `=C40/248.8` | Pa → in. w.g. (248.8), psi (6895), m/s → fpm (196.85, changed from 196.9 on 2026-02-20), kg/h → lb/h (2.205), kg/m³ → lb/ft³ (/16.018), m³/s → ACFM (×2118.88) | - | Keven | n/a (display only) | PLT-08 |

## 4. Departures from, and additions to, Agarwal (AG)

One line each. D = departure, A = addition, M = Keven tweak recorded in the changelog or cell comments.

| ID | Type | Departure |
|---|---|---|
| D01 | D | Fanning factor is Swamee-Jain / 4 (E16). AG Eq. 7 (p. 20) is f = 0.331 / [ln(k/(3.7 D) + (7/Re)^0.9)]² (exponent 0.9 verify). Numerically the same relation: 0.331 ≈ ln(10)²/16 = 0.33137 and 7^0.9 = 5.762 against 5.74 in the sheet. Both recorded, neither chosen |
| D02 | D | Solids friction is Δp_Z = μ λ_s ρ v² L_eq/(2D) (E22), not AG Eq. 3, Δp_s = Δp_g K R. The sheet's own K (E09, C27) is displayed but unused |
| D03 | D | If K of C27 were used in AG Eq. 3: Δp_g K R = 4 (c/v) × (sheet's Δp_Z) = **3.6 ×** the sheet's solids friction (K = λ_s (c/v)/f_L, so Δp_g K R = 4 f L ρ v²/(2D) · λ_s (c/v)/f · μ). Same factor in both cached cases |
| D04 | A | Laminar branch 64/Re for Re ≤ 4000 (E16); AG has no laminar case (KL Eq. 2.42 uses 2300 as the limit, p. 46) |
| D05 | D | Solids acceleration: AG worksheet 3 (p. 23) charges section 1 with G_s·c at the section **outlet** velocity (0.372 psi for outlet 67.71 ft/s × 0.8) and later sections with the same-section outlet − inlet change. The sheet uses the section **inlet** velocity for section 1 and the difference of inlet velocities for the rest, i.e. lagged by one section. Total ΔP_A is G_s (c/v) v_in,last instead of G_s (c/v) v_out,last. Effect in the cached cases: Vacuum 1377.0 Pa vs 1386.8 Pa (9.8 Pa, 0.14 % of total ΔP); Pressure 233.3 Pa vs 233.8 Pa |
| D06 | D | No solids velocity loss in bends and no re-acceleration length after a bend. AG §2.4.1 (V_p2 = 0.8 V_p1 for a 90° long-radius bend, (1 − θ/90)(1 − 0.8) V_p1 scaling for smaller angles) and §2.4.2 (20 pipe diameters to re-accelerate), p. 20. The slip ratio is constant along the line |
| D07 | D | Solids elevation uses a hard-coded 0.8 (E24) while every other solids term uses the slip ratio input 0.9 (C25). AG gives 0.8 for coarse and 0.9 for fine solids, one value for all terms |
| D08 | D | Gas density basis changes at each section: inlet density from humid air with R_u/M_w (E13), outlet density from dry-air R = 287.05 (E28). Humid R = 8.314/0.028818 = 288.50 (Pressure) and 288.80 J/(kg K) (Vacuum). Cached effect on section 1: outlet density is 0.51 % (Pressure) and 0.61 % (Vacuum) above the isothermally consistent value ρ_in p_out/p_in; in the Pressure case the section-1 outlet density (1.4156) is even **higher** than the inlet density (1.4133) although p falls. AG uses M = 28 throughout |
| D09 | D | Gas and solids elevation apply only to rows whose orientation is exactly "Vertical" and are always positive (loss). Downward vertical flow, inclined runs and the rise inside a "Horizontal to Vertical" bend (equivalent length 6 m, elevation 0) are not modelled. AG Eq. 4/5 take ΔZ in any direction |
| D10 | D | Elevation terms use L_eq as ΔZ (equals the typed length for pipes, which is correct for vertical pipes only) |
| D11 | D | Bend equivalent length is a fixed 6 m for any diameter (C15). AG §2.3: 40 D or 20 ft, whichever is greater; the two coincide at a 6 in pipe (20 ft = 6.1 m). For D > 6 in AG gives more than 6 m. 45° = 6/2 and 30° = 6/3 follow AG's angle/90 rule |
| D12 | D | Section length: AG §2.6 (p. 20) divides the line into 5-10 ft lengths. The sheet takes whatever length is typed (up to 6 m for a bend, 5 m for the cached pipes), one explicit step per section |
| D13 | D | Pressure systems: AG §2.6 (p. 21) marches from the line **end** back to the pickup for pressure systems. The sheet marches forward from the pickup/blower end and goal-seeks the inlet pressure. AG §2.5 reduces the gas mass flow by 5 % for rotary valve leakage in pressure systems; not in the sheet |
| D14 | D | Inlet condition of the Pressure sheet is the gas **velocity** (C30) at the unknown inlet pressure, so the gas mass flow ṁ_f = ρ_in v_in A changes during the goal seek (1.509 kg/s in the cached, unconverged state). The physical constant is the mass flow or the free-air flow |
| D15 | A | Humid air (E10-E13), constant viscosity (E14), solids friction correlation (E07), Rizk saltation (E03-E05) are additions; v_s feeds no term |
| D16 | A | Per-section cumulative equivalent length and the charts (E19, section 2.1) |
| D17 | D | Gas and solids misc. loss column exists but is empty; AG's 0.2 psi dust-collector default is not applied |
| M01 | M | Changelog 2024-12-17: pressure calculation and automatic inlet air density added. 2025-03-21: Goal Seek fixed. 2026-02-20: m/s to fpm factor 196.9 → 196.85. 2026-02-27: summation error in total pressure drop fixed |

## 5. Where WB, DOC and AG disagree on a base relation (not resolved)

| Item | WB | DOC | AG | KL |
|---|---|---|---|---|
| Water p_sat coefficients | Antoine (mmHg, °C) A 8.07131, B 1730.63, C 233.42, × 133.3: **3156.3 Pa at 25 °C** | Antoine with Stull coefficients in bar and K: A 4.6543, B 1435.264, C −64.848 (cites NIST WebBook): **3179.4 Pa** at 25 °C (0.7 % higher) | none | none |
| Viscosity | constant 18.37e-6 Pa·s | Sutherland μ0 = 1.716e-5, T0 = 273 K, S = 111 K: 18.38e-6 at 25 °C; PLT-02 text uses T0 = 273.15 K | µ in the formulas, no correlation | none |
| Friction factor | Swamee-Jain / 4, laminar 64/Re | Swamee-Jain (Darcy) | Eq. 7 (see D01) | Blasius / Koo (smooth) |
| Solids acceleration | inlet-based, lagged (D05) | ΔP_acc = (ṁ_s/A) v_s | outlet-based worksheet | integrated Eq. 6.69-6.71 |
| Gas density | R_u/M_w (inlet) and 287.05 (outlet) | R_u/M_w | 28 p / (19.32 T), p in psi, T in K (p. 21) | p/(R T) |
| Solids elevation velocity | 0.8 | v_s average solids velocity | 0.8 V_g | c |

AG worksheet 3 totals: the table gives 7.550 psi, the text of §3.5 says 7.58 psi (printed in the paper).

## 6. Constants and correlation coefficients

| Constant | Value | Where | Source |
|---|---|---|---|
| g | 9.81 m/s² | T, U columns; C23 | KL g = 9.81 (nomenclature) |
| Dry-air specific gas constant | 287.05 J/(kg K) | AA column | not recorded |
| Universal gas constant | 8.314 J/(mol K) | C53 | DOC Eq. 13 |
| Molar masses | 28.96 g/mol air, 18.02 g/mol water | C52 | DOC |
| Antoine (water) | 8.07131, 1730.63, 233.42 (mmHg, °C), × 133.3 Pa/mmHg (exact 133.322) | C50 | cell comment only (section 5) |
| Dynamic viscosity | 18.37e-6 Pa·s | C35 | cell comment "1.84E-05 @ 25 °C" |
| Temperature | 25 °C (typed 25 in X/Y, input C31) | Y column | header B3 |
| Swamee-Jain | 0.25, 3.7, 5.74, exponent 0.9; Re threshold 4000; laminar 64/Re | C37 | DOC Eq. 19 |
| Rizk | 1440, 1.96, 1100, 2.5 (d in m) | C21, C22 | KL Eq. 5.41 (p. 182) |
| Solids friction correlation | 55.5, D^1.1, v^0.64, d^0.26, ρ_b^0.91 | C26 (Pressure) | B2 note "Klinzing & Rizk and S.S. Mallick" |
| Solids friction constant | 0.009 | C26 (Vacuum) | Keven |
| Slip ratio | 0.9 input; 0.8 hard-coded in U | C25, U | AG §2.4 |
| Bend equivalent length | 6 m (input C15); 1/2 and 1/3 of it | C15, M | AG §2.3 (20 ft) |
| Wall thickness | 0.12 in (11 ga), 0.065 in (16 ga) | C11, Notes D65:D70 | Keven |
| Pipe roughness | 4.6e-5 m | C13 | Notes picture "commercial or welded steel" |
| Goal seek target | 100700 Pa | VBA | Keven (not 101325) |
| Unit conversions | 25.4, 196.85, 248.8, 6895, 2.205, 16.018, 2118.88, 3.3 (ft/m in the Vacuum lengths) | E/F columns; K11, K15 | Keven |
| Bend 45°/30° scaling | 1/2, 1/3 | M | AG §2.3 |

## 7. Friction factor convention at each use

| Use | Convention |
|---|---|
| C37 | **Fanning** f_L (Swamee-Jain Darcy value divided by 4; laminar 64/Re also divided by 4) |
| R column (gas friction) | `4*C37*L*ρ*v²/(2D)`: multiplies back by 4, i.e. Darcy λ_L = 4 f_L inside the Darcy-Weisbach form |
| S column (solids friction) | `μ*λ_s*ρ*v²*L/(2D)`: λ_s (C26) is used like a Darcy-type factor with no factor 4. Its basis relative to KL's λ*_z (KL tabulates λ*_z/4, Table 4.5, p. 97) is unknown |
| C27 (K) | divides by f_L (Fanning), unused |
| AG Eq. 2, Eq. 7 | Fanning f with the 4 explicit (Eq. 2); KL Eq. 2.41 uses Darcy λ_L; KL notes λ_L = 4 f_L (p. 47) |

## 8. Goal seek

Pressure!H6 and the button "Goal Seek" (drawing macro `[0]!Sheet1.GoalSeekPressure`); the VBA, decoded from
`xl/vbaProject.bin` with a small MS-OVBA decompressor, is complete:

```vb
Sub GoalSeekPressure()
    Range("AC34").GoalSeek Goal:=100700, ChangingCell:=Range("C33")
End Sub
```

- **Target cell** `AC34` (outlet pressure, `=AC33`), **goal 100700 Pa absolute (hard-coded, not 101325 Pa)**, **varied cell** `C33` (inlet
  pressure, a pasted value). `C33` feeds back into `C53` and `C51`, so the inlet density (and the humid-air fraction)
  change with each iteration; `C30` (velocity) is held, so ṁ_f changes (D14).
- Tolerance: none in the code; Excel's default Goal Seek settings apply (`calcPr` has no iteration attributes). Not run
  here.
- No other VBA: Sheet2 to Sheet4 and ThisWorkbook are empty. There is no Vacuum macro.
- The cached Pressure state is **not converged**: AC34 = 118701.92 Pa against the 100700 Pa goal. Keven confirmed it
  is a stale result of an unfinished calculation (comment 2026-10-21).

## 9. Thermal assumption and humidity

- **Isothermal at 25 °C** (header B3; comment B31 limits temperature to 1-100 °C). Outlet temperature column Y is typed 25 in all rows, so changing
  the input C31 changes `X11` and the inlet density but **not** the outlet density `AA` (which uses `Y`). Probably unintended (open question 3).
- **Humidity** enters only through the inlet density (E10-E13); the viscosity is constant, not humidity- or temperature-corrected. Along the line the
  outlet density ignores humidity (D08). x_w is computed at the inlet pressure and not updated along the line.
- No heat transfer, compression heating or Joule-Thomson effect (DOC §4 "Temperature" states the same assumption and its limit for air movers).

## 10. Bends, equivalent length, diameter steps, feed point, inline equipment

- **Bends**: one row each, "90° Bend", "45° Bend", "30° Bend" (drop-down in I11:I33), modelled only as equivalent length
  (6, 3, 2 m for any diameter) and charged to Δp_L and Δp_Z; no K-factor, no R/D, no angle input, no separate bend
  term, no solids loss or re-acceleration (D06). Orientation of a bend row ("Horizontal to Vertical" etc.) has no effect:
  only the exact value "Vertical" triggers elevation terms (D09).
- **Orientation** drop-down (J11:J33): Horizontal, Vertical, Horizontal to Vertical, Vertical to Horizontal, Horizontal to Horizontal.
- **Equivalent length**: column M; cumulative in N; used as x-axis of the charts and of the "equivalent distance".
- **Diameter steps**: none. `L11:L33` all equal `$C$11`; there is a single ID for the whole line (stepped lines cannot be entered).
- **Solids feed point**: implicit in section 1: solids start at rest and the section-1 acceleration term is G_s (c/v) v_in (E20). Solids are present in
  every row; there is no way to start solids later, to remove them (dust collector) or to add gas.
- **Inline equipment**: none (column V empty). The pasted Notes pictures list diverter valves and flexible hose as equivalent lengths (not used by any formula).
- **Rows**: 23 fixed. Unused rows have M = 0 and return 0.

## 11. Nomenclature (binding for PLT-02 to PLT-08)

Klinzing et al. symbols only (Keven, 2026-10-21: "use only Klinzing's nomenclature"). Identifiers are ASCII snake_case, Greek
spelled out, subscripts as suffixes. SI units; absolute pressure; K. Klinzing tabulates D and d in mm: the library uses
m. "(proposed)" = Klinzing has no symbol for it. The sheet's labels are in the last column for traceability.
Source for the symbols: Klinzing nomenclature pp. xiii-xviii and the equations cited in section 3. Glyphs are garbled in the PDF text layer; symbols marked (verify) were read from context.

| Klinzing symbol | Meaning | SI unit | Python identifier | Workbook cell / label | Flags |
|---|---|---|---|---|---|
| A | pipe cross-section area, π D²/4 | m² | `A` | implicit | duct_flow field is `area` (boundary mapping, see below) |
| D | pipe inner diameter | m | `D` | C11, L / "I.D." | duct_flow uses `diameter`; the cyclone module uses `D` for the cyclone **body** diameter (H&S). Separate modules, no shared namespace; documented |
| d | particle diameter | m | `d` | C20 / "Particle Diameter" | Rizk constants need d in mm (E03) |
| k | effective wall roughness | m | `k` | C13 / "Roughess (ε)" | the sheet's ε is Klinzing's k; Klinzing's ε is voidage. Cyclone module: `wall_roughness`, `ks_over_R` |
| L | pipe length | m | `L` | K / "Length" | |
| L_eq (proposed) | equivalent length of a section | m | `L_eq` | M / "Eq. Length of Section" | |
| L_eq_cum (proposed) | cumulative equivalent length | m | `L_eq_cum` | N | |
| Z, ΔZ | height, height difference | m | `delta_Z` | implicit (L_eq for "Vertical") | |
| g | gravitational acceleration | m/s² | `g` | 9.81 | |
| v | gas (superficial) velocity | m/s | `v` | AD, AE, C30 | duct_flow field is `velocity`; cyclone uses `v_in`, `v_x` |
| c | particle (solids) velocity | m/s | `c` | C24 (derived) | |
| w = v − c | slip velocity | m/s | `w` | derived | |
| c/v (proposed; §6.7.4, p. 222) | solid/gas velocity ratio | - | `c_over_v` | C25 / "Slip Ratio" | the sheet's "slip ratio" is c/v, not Klinzing's slip velocity w |
| ρ | gas density | kg/m³ | `rho` | Z, AA, C34 | cyclone uses `rho` (same meaning) |
| ρ_p | particle density | kg/m³ | `rho_p` | not in workbook | cyclone `rho_p` (same) |
| ρ_b | bulk density | kg/m³ | `rho_b` | C19 | cyclone field `bulk_density` |
| ρ′ (verify glyph) | apparent bulk (conveying) density, ρ_p(1 − ε) | kg/m³ | `rho_prime` (proposed) | not in workbook | |
| η | gas dynamic viscosity | Pa·s | `eta` | C35 | **clash**: cyclone code uses `mu` for dynamic viscosity and `eta` / `eta_overall` for efficiency |
| ν | gas kinematic viscosity | m²/s | `nu` | not in workbook | |
| Re | Reynolds number ρ v D / η | - | `Re` | C36 | cyclone uses `Re_R`, `Re_p` (no clash) |
| f_L | Fanning gas friction factor | - | `f_L` | C37 | cyclone uses `f_air`, `f` |
| λ_L | Darcy gas friction factor, 4 f_L | - | `lambda_L` | implicit in R | |
| λ_Z | additional pressure-drop factor due to solids | - | `lambda_Z` | `C38*C26` | |
| λ*_z (verify glyph) | solids friction factor | - | `lambda_z_star` | C26 / "Solids Friction Factor" | basis relative to the sheet's λ_s unknown (section 7) |
| μ | mass load ratio ṁ_s/ṁ_f | - | `mu` | C38 / "Solid loading ratio" | **clash**: cyclone code `mu` = viscosity. KL also lists the symbol for "mass flow ratio" |
| ṁ_s, ṁ_f | solids, gas mass flow | kg/s | `m_dot_s`, `m_dot_f` | C18 (kg/h) | |
| G_s, G_f | solids, gas mass flux ṁ/A | kg/(m² s) | `G_s`, `G_f` | derived | |
| p | absolute pressure | Pa | `p` | AB, AC, C33 | |
| p_atm | atmospheric pressure | Pa | `p_atm` | 100700 (VBA) | |
| Δp | pressure difference | Pa | `delta_p` | W | |
| Δp_L | clean-gas friction | Pa | `delta_p_L` | R | |
| Δp_A | solids acceleration | Pa | `delta_p_A` | Q | |
| Δp_Z | solids friction and impact | Pa | `delta_p_Z` | S | |
| Δp_G | gravity (lift) of gas and of solids | Pa | `delta_p_G_gas`, `delta_p_G_solids` (split proposed) | T, U | KL has one Δp_G; the sheet splits it |
| Δp_B | bends | Pa | `delta_p_B` | none (bends are L_eq) | |
| Δp_misc (proposed) | inline equipment | Pa | `delta_p_misc` | V / "Misc." | KL Eq. 6.45: separator and valves |
| T | absolute temperature | K | `T` | X, Y, C31 (°C in sheet) | |
| R | specific gas constant | J/(kg K) | `R` | 287.05 | |
| R (kmol basis, second entry in KL) | universal gas constant | J/(mol K) in the library (KL: J/(kmol K)) | `R_u` (proposed) | 8.314 | unit differs from KL |
| M_w | molecular weight | kg/mol in the library (KL: kg/kmol) | `M_w` | C52 | unit differs from KL |
| φ (verify glyph) | relative humidity | - (0 to 1) | `phi` | C32 (percent) | PLT-02 raises ValueError outside 0-1 |
| p_sat (proposed) | water saturation pressure | Pa | `p_sat` | C50 | |
| x_w (proposed) | water vapour mole fraction | - | `x_w` | C51 | the sheet labels it "mass fraction" |
| ε | voidage | - | `epsilon` | not in workbook | the sheet's ε (roughness) becomes `k` |
| Fr | Froude number v/√(g D) | - | `Fr` | not in workbook | inlet values 30.1 (Vacuum), 25.2 (Pressure) |
| δ, χ (verify glyphs) | Rizk saltation exponents (Eq. 5.41) | - | `delta`, `chi` | C21 "Gamma", C22 "Beta" | the sheet's names Gamma and Beta are not Klinzing's. `delta` is not `delta_p` / `delta_Z` (Δ-quantities always carry a suffix) |
| v_s | gas velocity at the saltation point | m/s | `v_s` | C23 / "Usalt" | KL also has v_s* friction velocity (different) |
| a | speed of sound in the gas | m/s | `a` | not in workbook | |
| Ma (proposed) | Mach number | - | `Ma` | not in workbook | |
| θ | bend angle | degree | `theta` | I column ("30/45/90° Bend") | |
| R_b, D_b | bend radius of curvature, curvature diameter | m | `R_b`, `D_b` | none | |
| t_w (proposed) | pipe wall thickness | m | `t_w` | C11 (0.12 in typed) | |
| D_outer (proposed) | pipe outer diameter | m | `D_outer` | C11 (8 in, 3 in typed) | KL uses `D_o` for an orifice |
| section (proposed) | section index | - | `section` | H, P | |

Boundary mapping to existing flowguard names: `fluid_systems/duct_flow.py` exposes `diameter`, `velocity`, `flow`, `area` and
`RoundDuctResult`; `core/units.py` exposes named converters (`cfm_to_m3s`, `fpm_to_ms`, `in_to_mm`, `inh2o_to_pa`,
`convert_pressure`). None of these names collide with the table above. **Proposed resolution** for the PLT items: Klinzing names inside
the PLT modules (`D`, `v`, `A`); `duct_flow` keeps its public names and is imported by module (`from fluid_systems import
duct_flow`), converting at the boundary. The only true clash is `mu` / `eta` against the cyclone module
(`collection_systems/cyclone_muschelknautz_*`, H&S symbols: `mu` = viscosity, `eta` = efficiency). Proposal: leave the
cyclone code alone (out of scope, different source nomenclature); every PLT docstring states the symbol's meaning; PLT-02's gas-state
dataclass uses `eta` for viscosity so the cyclone orchestrator needs an explicit mapping if it later consumes it (open question 11).

## 12. Validity limits recorded in the workbook (for warnings in PLT-05 and PLT-08)

| Limit | Where |
|---|---|
| Rizk saltation correlation suited to fine powders below 200 µm | comment on B21 |
| K between 0.4 and 4 (AG §2.2) | comment on B27 |
| Temperature 1 to 100 °C (Antoine range) | comment on B31 |
| Dilute phase material/air ratio 5-15; intermediary 10-30; dense > 30 (picture, units not stated) | Notes picture. Cached μ is 1.97 (Vacuum) and 0.147 (Pressure) kg/kg, both below 5 |
| Slip factor 0.7-0.95 | Notes picture (AG §2.4) |

## 13. Material = 0 (gas only, used for high vacuum)

Keven (comment 2026-10-21): the workbook has no stored material = 0 case; it is obtained by setting the material flow rate
C18 to 0 kg/h. Hand trace (not run in Excel):

- C38 = 0, so `S` (solids friction), `Q` (acceleration) and `U` (solids elevation) are 0. C23 (Usalt) = 0. C21, C22 unchanged.
- The gas terms R and T are unaffected (they do not read C18). C27 (K) is unaffected.
- **Pressure sheet only**: C26 = `55.5*D^1.1/(v^0.64 d^0.26 ρ_b^0.91)` is still evaluated, so clearing the particle diameter C20 or
  bulk density C19 gives `#DIV/0!`, which propagates to column S, W and every result. The gas-only case works only while C19 and C20 keep non-zero values. The Vacuum sheet (C26 = 0.009) has no such
  dependency.
- High vacuum: Re may fall below 4000, then `C37 = (64/Re)/4`; no choking or Mach check exists (the sheet has none).

## 14. Fixtures

`tests/fixtures/pressure_loss_theoretical/` (SI; values are the cached ones, `data_only=True`, each fixture re-read against
the workbook cell by cell: 186 values compared, all equal):

| File | Case | Notes |
|---|---|---|
| `vacuum_with_solids.json` | Vacuum sheet, 800 kg/h, 5 sections, λ_s = 0.009 | total ΔP 7209.2 Pa, outlet 93490.8 Pa |
| `pressure_with_solids.json` | Pressure sheet, 800 kg/h, 5 sections, λ_s by correlation | **not converged** (outlet 118701.9 Pa vs the 100700 Pa goal; stale, per Keven). Total ΔP 2865.2 Pa. Flagged in `_meta.flags` |
| gas-only (material = 0, ideally high vacuum) | **missing**: not stored in the workbook | see open question 2 |

Each fixture has `inputs`, `derived`, `sections` (only the 5 used rows) and `totals`. Per-section fields: pressure in/out, gas velocity in/out,
solids velocity in/out (`c_*_derived` = (c/v) × v, derived), density in/out, temperature, every Δp term, L_eq and cumulative.
`tests/test_pressure_loss_theoretical_fixtures.py` checks the sheet's own bookkeeping (terms sum to the section total,
pressure/velocity/density chain, cumulative sums, totals). It exercises no library code.

## 15. Proposed changes to the target files of the sibling items

| Item | Finding and proposal |
|---|---|
| All | The sibling pages cite the source folder as `pressure_loss_theoretical/`; the folder is `Pressure drop theoretical/`. Agarwal is January/February 2005 pp. 18-23, not April 2005 (PLT-05 Sources). Keven asked for everything in SI; the library takes m (not mm, not in) |
| PLT-02 `core/gas_properties_equations.py`, `_orchestrator.py` | Keep names. Humid-air chain E10-E13: use one gas-constant convention. The workbook uses the dry R in E28 (D08) and humid M_w in E13; the regression fixtures need both reproduced, the library should use humid throughout. The p_sat correlation (WB vs DOC, section 5) and the viscosity (constant vs Sutherland, T0 273 vs 273.15 K) are open for Keven. `eta` for viscosity (clash with the cyclone `mu`). Fixtures give inlet ρ for T = 298.15 K, φ = 50 %: 1.1695114 kg/m³ at 100700 Pa and 1.4133016 kg/m³ at 121567.118 Pa |
| PLT-03 `fluid_systems/gas_pipe_flow_equations.py` | Darcy internally is consistent with KL (λ_L). Workbook friction is Swamee-Jain (E16): use it as the turbulent branch; the workbook switches at Re 4000 with 64/Re below (no transition blending); KL puts the laminar limit at 2300. Gas acceleration `dp_accel = G dV` is not a workbook term (the sheet and AG have none; ZO Eq. 1 in AG p. 18 has it): an addition, no regression fixture. Bends: the workbook uses equivalent length only (E18, 6 m, D11); K-factor / R/D are additions (KL Table 2.8, Eq. 6.45c for reference). Elevation: workbook is vertical-only (D09); library takes signed ΔZ |
| PLT-05 `material_handling/pneumatic_conveying_agarwal_equations.py` | The file name is fine but not every solids relation is Agarwal's: Δp_Z form (E22), the λ_s correlation (E07, "Keven tweak", no KL match), Rizk saltation (KL Eq. 5.41). Implement **both** AG Eq. 3 (Δp_g K R) and the workbook form (D02, D03: factor 4 (c/v)); the paper's worked example (AG appendices 1-3, pp. 22-23, 4 in. line, K = 1.2, polyethylene, 10,000 lb/h, total 7.55 psi) needs AG Eq. 3 and is in imperial units (convert at the test boundary). Zero solids: every solids term is already 0 via μ and G_s; the correlation E07 must not be evaluated (or must be guarded) when ṁ_s = 0 (section 13). Bend solids velocity loss and re-acceleration (AG §2.4.1-2) are additions (D06), no fixture. Make 0.8 (E24, D07) and 0.9 (E06) named parameters; the acceleration convention (D05) must be chosen |
| PLT-06 `fluid_systems/pipeline_model.py`, `pipeline_orchestrator.py` | Fixtures are one explicit step per section (E26-E29). To regress against them, the PLT-06 tests need a test-local replica of the sheet recursion built from the PLT-02/03/05 functions (it should reproduce the fixtures to about 1e-9), then the fixed-step march is compared against it and the difference tabulated (the item already expects this). The Pressure case is not converged and has a fixed inlet **velocity**: converting it to a mass-flow input needs ṁ_f = ρ_in v_in A from a converged state, and the goal is 100700 Pa (not 101325 Pa) so the boundary pressure is an input, default as per Keven (open question 1). Equivalent distance = cumulative L_eq (E19): bends are lumped with zero arc length in the workbook. Inline components: workbook has none (column V); dust collector default 0.2 psi comes from AG p. 21 |
| PLT-07 `fluid_systems/pipeline_model.py` builder | Both fixture layouts are feed section, 90° bend, vertical, 90° bend, horizontal (2 bends, no 45/30°, one diameter). They give the detailed layouts for the sensitivity test; the 45/30° handling in the workbook is E18 scaling |
| PLT-08 page | Workbook has 23 fixed rows and one ID; charts plot ΔP and velocity vs cumulative equivalent length (20 of the 23 rows). Candidate validity warnings: section 12. Show ṁ_f when the input is a velocity at the inlet |

No change to the target **file names** is proposed; changes above are to their content, parameters and tests.

## 16. Open questions for Keven

1. **Goal seek target.** The macro targets 100700 Pa absolute (hard-coded). Is that the intended "atmospheric" default (site pressure) for the library, or should it be 101325 Pa? Can you re-run Goal Seek in Excel and save the workbook so a converged Pressure fixture can be added (the stored one is stale, as you said)? Otherwise a computed replica case could be added, clearly labelled.
2. **Gas-only fixture.** The workbook holds none. May I add a case computed from the sheet formulas with C18 = 0 (labelled "computed, not cached"), or will you save one from Excel? Default: left missing.
3. **Outlet temperature column Y** is typed 25 in every row, not linked to C31. Intended, or a bug (changing C31 does not change outlet density)?
4. **Gas density basis** (D08): inlet humid air (R_u/M_w), outlet dry air 287.05 J/(kg K). Intentional? The library will use one basis.
5. **Solids elevation** uses 0.8 hard-coded while the slip input is 0.9 (D07). Intended?
6. **Solids friction λ_s**: confirm its basis (Darcy-type, no factor 4, with gas velocity v²); the source of the Pressure-sheet correlation (S.S. Mallick: which reference?); why 0.009 on the Vacuum sheet. The unused K (C27) and its 19.3 on the Pressure sheet (outside the 0.4-4 range): keep as an option or drop?
7. **Solids acceleration** (D05): the workbook charges acceleration one section late and from the inlet velocity; AG worksheet 3 uses outlet velocity. Reproduce the workbook as is, or follow AG?
8. **Pressure system flow basis** (D14): the input is the velocity at the unknown inlet pressure. The library will take mass flow or free-air flow (PLT-06); OK?
9. **Water p_sat coefficients** and **viscosity** (section 5): which of the workbook's or the docx's? (the Antoine set in the workbook has no recorded source)
10. **Bends**: fixed 6 m for any diameter (D11) and no rise counted inside "Horizontal to Vertical" bends (D09). Keep for regression only, with AG's 40 D / 20 ft rule and bend rise in the library?
11. **Cyclone naming clash** (`mu`, `eta`): leave the cyclone module as is?
12. **Source dates and folder**: confirm Agarwal is January/February 2005 (the PDF and DOC say so; the items say April), and whether the sibling items' source paths should read `Pressure drop theoretical/`.
13. **Notes pictures**: item (b) gives short radius 90° = 12 m and bends under 90° as 12·angle/90, while the sheet scales 6 m by angle/90. Which base applies to 45° and 30° bends (long radius, so 3 m and 2 m as now)?
14. **Embedded Paint objects / EMF** on the Notes sheet were not decoded. Do they hold anything beyond the six pictures described in section 2.4?
