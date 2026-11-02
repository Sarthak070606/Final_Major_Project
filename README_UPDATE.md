# MP Groundwater Intelligence Dashboard – Updated Package

## Included
- Existing dashboard pages and utilities, preserved.
- Refreshed professional blue/white UI theme.
- Consistent light Plotly chart templates.
- Local SVG hero banner under `dashboard/assets/`.
- Updated floating chatbot styling.
- Corrected available-period estimation engine and polished chatbot service.
- Dashboard dependency list.

## Important
This package contains the dashboard source only. It does not contain or replace:
- `data/`
- `models/`
- `reports/`

Keep those folders in your existing `major_project_phase_one` project root.

## Windows PowerShell – run all commands from project root

```powershell
# 1. Back up the current dashboard folder first (optional but recommended)
if (Test-Path .\dashboard) {
    Copy-Item .\dashboard .\dashboard_backup_before_update -Recurse -Force
}

# 2. Extract/copy the updated dashboard folder from this package
#    Copy the package's dashboard folder into the project root and replace the old dashboard folder.

# 3. Install dashboard dependencies
python -m pip install -r requirements-dashboard.txt

# 4. Start the dashboard
python -m streamlit run dashboard/app.py
```

Open: http://localhost:8501

## Optional chatbot requirement
The chatbot uses your existing local Ollama service and configured model.
Make sure Ollama is running and the model used by `chatbot_service.py` is installed.

## Image display
The overview hero banner is embedded from a local SVG asset. It does not depend on an external image URL.
Other charts/maps are rendered by Plotly and Folium from the existing project data.

## Data and scientific limitations
- The source telemetry begins in 2021; do not invent 2020 values.
- 2026 summaries are year-to-date / available-period when applicable.
- Missing representative months remain missing, not zero.
- Groundwater-level telemetry alone cannot certify drinking-water quality, borewell yield, drilling depth, or well suitability.
- Predictions represent the next available station observation, not a guaranteed six-hour forecast.
