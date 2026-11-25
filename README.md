# Similar Results-Posting Proportions Despite Low Trial Retrieval by Funder Name: A Pancreas-Focused Portfolio and Cross-Funder Analysis

Analysis code and curated data accompanying **Similar Results-Posting Proportions Despite Low Trial Retrieval by Funder Name: A Pancreas-Focused Portfolio and Cross-Funder Analysis**.

The package recalculates the reported coverage and reporting quantities from the curated inputs and regenerates the two manuscript figures.

## Run

Python 3.10 or later. The numerical calculations and checks use the standard library:

```bash
python reproduce.py --no-figures
python -m unittest discover -s tests -v
```

Figure generation uses Python 3.10–3.12 and the packages in `requirements.txt`:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: ./.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python reproduce.py --no-figures
python plot_figures.py --font-path /path/to/arialbd.ttf
```

The manuscript figures use Arial Bold throughout, with uppercase 18-point panel letters. Use an installed, licensed Arial Bold TrueType font with `--font-path` (for example, `C:/Windows/Fonts/arialbd.ttf` on Windows). The font file is not redistributed. If Arial Bold is installed and discoverable by Matplotlib, `--font-path` may be omitted; the script reports an error rather than silently changing fonts.

Run from the repository root. Outputs are written to `results/`. The scripts make no network requests. PDF and SVG are vector formats; PNG and TIFF are written at 600 dpi.

## Contents

| Material | Operation |
|---|---|
| Table 1 | Check source inventories against the curated records |
| Table 2, Figure 1 | Recalculate percentages and differences; redraw the figure |
| SU2C, Table 3 | Recompute the registry/journal union, name subset and conference sensitivity |
| MRC, Table 3 and Figure 2 | Recompute reporting and the NCT-bearing restriction |
| MRC paper evidence | Inspect the confirmed-row evidence records and identifier partition |
| NIHR, Table 4 | Recompute known-identifier coverage and the family union |
| NIHR pilot and extension | Reproduce the reported comparisons from the aggregate counts and reference memberships |
| Supplementary tables | Retain the published presentation for comparison |

## Files

- `data/curated/`: trial, source-row, family and registration-link evidence.
- `data/aggregate/`: comparison counts.
- `expected/`: manuscript tables used for comparison.
- `reproduce.py`, `plot_figures.py`, `tests/`: analysis, figure generation and checks.
- `docs/`: methods, field definitions, data manifest and reuse terms.
- `SHA256SUMS`: SHA-256 checksums for the packaged files.

Source capture dates are October 2026 as specified in the methods.

## Version and repository

Prepared release version: `v1.0.0`  
Target repository: https://github.com/FENG1567/funder-name-trial-retrieval

## Licence and citation

`LICENSE` applies to project code only. Third-party records retain their source terms; see `docs/data_reuse.md`.
