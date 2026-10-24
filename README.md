# FAHU Academic Studio v4.1

Editable desktop engineering calculator for FAHU air-to-air heat recovery, air states, and preliminary coil and run-around pump calculations.

**Status:** preliminary, educational / engineering review tool. Not certified, endorsed or approved by ASHRAE. The recovery model is an idealized steady-state effectiveness approximation; no leakage, condensation/frost, detailed coil or piping selection.

## What is included
- Python/Tkinter desktop GUI and editable source code
- Rotary wheel, sensible plate and run-around coil schematic illustrations
- Five-state psychrometric chart and CSV/PDF export
- Equation-by-equation calculation sheet with input substitution, source references, and balance tolerances
- Automated unit tests including a numerical comparison with 2020 ASHRAE Handbook, HVAC Systems and Equipment (SI), Chapter 26, Example 1, p.26.4

## Windows development / run
1. Install Python 3.13 (check **Add Python to PATH**).
2. In PowerShell in this folder: `py -3.13 -m pip install -r requirements.txt`
3. Run tests: `py -3.13 -m unittest discover -v`
4. Run editable GUI: `py -3.13 FAHU_Academic_V4_1.py`
5. Build `.exe`: double-click `BUILD_EXE.bat`; the executable appears in `dist/`.

## Engineering references
2020 ASHRAE Handbook—HVAC Systems and Equipment (SI), Chapter 26, pp. 26.2–26.4: effectiveness (Eqs. 2a, 2b), recovery energy (Eqs. 5a–5d), fan power (Eqs. 8–9). Reference equations are paraphrased or implemented in code, not reproduced as copyrighted book pages. Psychrometric property relations use simplified approximations; consult ASHRAE Handbook—Fundamentals for higher-accuracy property methods.

**Note:** The current version does not implement fan pressure drop/power from Eqs. 8–9. Run-around pump head/power are standard fluid mechanics relationships and **are not directly equations from Chapter 26**. Manufacturer selection and independent engineering verification are required.

## Publishing on GitHub
Create a new repository, then use the instructions in `GITHUB_AND_LINKEDIN_GUIDE.md`. Do not upload ASHRAE copyrighted PDFs, private project data, or claim ASHRAE certification. If you want open-source redistribution, add a license after reviewing your IP obligations.
