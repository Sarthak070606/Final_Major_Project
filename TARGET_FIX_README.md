# Target Realignment Fix (Phase 2)

## Problem
After cleaning, 54 128 rows had a `target_wl_t_plus_1` that no longer matched the true next chronological observation of the same station.

## Solution
1. Load the cleaned dataset (or Phase-1 features).
2. Resolve any remaining station-timestamp duplicates (keep first).
3. Sort by station + datetime.
4. **Recalculate** for every station:
   - `target_wl_t_plus_1` = next row’s `wl_raw` (last row → NaN and is dropped)
   - lag features
   - trailing rolling statistics
5. Save as `data/processed/phase2/features_clean_v2.parquet` (never overwrites previous files).
6. Run a strict validation script that must report **zero** target mismatches.

## PowerShell commands

```powershell
# From the root of major_project_phase_one
$env:PYTHONPATH = (Get-Location).Path

# 1. Recalculate targets and features
python -m src.training.recalculate_targets

# 2. Validate (must exit with code 0 and report zero mismatches)
python -m src.evaluation.validate_targets
```

Only after the validation script prints  
`VALIDATION PASSED – zero target mismatches`  
should you proceed to chronological splitting and model training, using  
`features_clean_v2.parquet` as the input.
