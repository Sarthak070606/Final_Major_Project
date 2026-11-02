# 💧 AI-Enabled Groundwater Monitoring, Prediction and Well Suitability Assessment System

An AI-powered groundwater monitoring and prediction system developed using Central Ground Water Board (CGWB) data for Madhya Pradesh, India. The project analyzes historical groundwater observations, identifies temporal patterns, predicts the next available groundwater-level observation, and provides an interactive dashboard for exploring groundwater conditions.

## 📌 Project Overview

Groundwater is an important source of water for domestic, agricultural, and industrial purposes. Monitoring groundwater levels across different locations helps understand groundwater trends and supports better water-resource planning.

This project uses historical groundwater observations and machine learning techniques to develop a system for:

- Monitoring groundwater levels across stations in Madhya Pradesh.
- Analyzing historical and yearly groundwater trends.
- Exploring district-wise and station-wise groundwater information.
- Predicting the next available groundwater-level observation.
- Providing location-based groundwater information through an interactive dashboard.
- Offering an AI-powered chatbot for groundwater-related queries.

**Important:** Groundwater-level predictions alone cannot establish drinking-water safety, borewell yield, drilling depth, or actual well suitability. These require additional hydrogeological and laboratory information.

## 🎯 Project Objectives

1. Process and analyze historical groundwater datasets.
2. Perform data cleaning and quality checks.
3. Develop temporal features using lag, rolling statistics, and cyclical time features.
4. Train and evaluate machine learning models.
5. Implement a hybrid prediction approach for known and unseen stations.
6. Develop a dashboard using Streamlit.
7. Integrate model predictions through FastAPI.
8. Provide accessible groundwater information through an AI chatbot.

## 🏗️ System Architecture

The project follows a modular architecture:

```text
              CGWB Groundwater Data
                       |
                       v
               Data Preprocessing
                       |
                       v
                Data Validation
                       |
                       v
                Feature Engineering
                       |
                       v
                Machine Learning
                       |
                       v
             Hybrid Prediction Model
                       |
              +--------+--------+
              |                 |
              v                 v
         FastAPI Backend   Evaluation Reports
              |
              v
       Streamlit Dashboard
              |
       +------+------+------+
       |      |      |      |
     Trends  Maps  Prediction Chatbot
```

## 🤖 Machine Learning Methodology

### Feature Engineering

The model uses 20 input features, including:

- Current groundwater level.
- Historical lag features.
- Rolling mean and standard deviation.
- Month, day of year, and hour.
- Cyclical time representations using sine and cosine.
- Station latitude and longitude.

### Model

The selected model is:

**Random Forest Regressor**

The model predicts the target:

`target_wl_t_plus_1`

This represents the next available observation, not necessarily an observation exactly six hours later.

### Hybrid Prediction Strategy

The system uses two prediction approaches:

| Station type | Prediction method |
|---|---|
| Known training stations | Random Forest Regressor |
| Unseen stations | Persistence baseline |

For unseen stations, the persistence baseline assumes that the next groundwater level equals the latest observed level. It is not a trained machine learning prediction.

## 📊 Model Performance

The following are the existing diagnostic evaluation results:

| Metric | Overall |
|---|---:|
| MAE | 0.2679 |
| RMSE | 1.6367 |
| R² Score | 0.9766 |

Additional results:

| Evaluation group | MAE | RMSE | R² |
|---|---:|---:|---:|
| Known stations | 0.2338 | 0.7967 | 0.9883 |
| Unseen stations | 0.3668 | 2.9331 | 0.9678 |

These results are diagnostic metrics from the existing evaluation, not a claim of performance on an untouched final holdout dataset.

## 📍 Dataset Information

The project uses groundwater observations sourced from CGWB-related data.

Current feature dataset statistics:

| Parameter | Value |
|---|---:|
| Total feature records | 4,097,128 |
| Monitoring stations | 1,379 |
| Districts | 52 |
| First available observation | 8 May 2021 |
| Latest available observation | 2 September 2026 |

The year 2026 contains partial-year data.

Large raw and processed datasets are excluded from this Git repository. Refer to the project documentation for dataset preparation details.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming language | Python |
| Machine Learning | Scikit-learn |
| Model | Random Forest Regressor |
| Data processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Dashboard | Streamlit |
| Backend API | FastAPI |
| API server | Uvicorn |
| Geospatial visualization | Folium |
| AI chatbot | Ollama |
| Data storage | CSV, Parquet, JSON |
| Version control | Git and GitHub |

## 📂 Project Structure

```text
major_project_phase_one/
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── dashboard/
│   ├── app.py
│   ├── views/
│   └── utils/
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── models/
│   ├── best_model.joblib
│   ├── model_metadata.json
│   └── hybrid/
│       └── hybrid_model.joblib
│
├── notebooks/
│
├── reports/
│   ├── phase2/
│   ├── phase3/
│   └── hybrid/
│
├── src/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── figures/
│
├── requirements-dashboard.txt
├── requirements-phase1.txt
├── requirements-phase2.txt
└── README.md
```

Note: Large datasets and model binaries are excluded from GitHub through `.gitignore`. The structure above describes the local project.

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

cd YOUR_REPOSITORY
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements-dashboard.txt
```

Install FastAPI dependencies if they are not included:

```bash
pip install fastapi "uvicorn[standard]" pyarrow
```

### 4. Prepare project data and models

The raw and processed datasets and trained model binaries are not included in this repository.

Obtain the authorized project datasets and model artifacts separately, then place them in their expected directories.

### 5. Start the FastAPI backend

From the project root:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Start the Streamlit dashboard

Open another terminal:

```bash
streamlit run dashboard/app.py
```

Dashboard:

```text
http://localhost:8501
```

## 🔍 Key Features

- Historical groundwater monitoring.
- Station-wise groundwater exploration.
- District-wise analysis.
- Yearly and representative-month analysis.
- Interactive groundwater maps.
- Machine learning-based next-observation prediction.
- Hybrid prediction for known and unseen stations.
- AI-powered groundwater chatbot.
- Model evaluation and data-quality reports.

## ⚠️ Limitations

- Predictions represent the next available observation, not a guaranteed six-hour forecast.
- Unseen stations use a persistence baseline rather than a trained Random Forest prediction.
- Water-level predictions alone cannot determine groundwater quality or drinking-water safety.
- Reliable well suitability assessment requires additional geological, aquifer, recharge, and laboratory data.
- Spatial interpolation can be unreliable where nearby station observations vary significantly.
- The dataset contains irregular observation intervals and incomplete coverage for some periods.

## 🚀 Future Improvements

- Integrate verified geological and lithological datasets.
- Incorporate groundwater chemistry and water-quality parameters.
- Improve spatial prediction using suitable geospatial machine learning methods.
- Develop more robust time-series forecasting models.
- Add rainfall and recharge information.
- Improve well-suitability assessment with verified hydrogeological data.
- Deploy the application to a cloud platform.

## 👨‍💻 Author

**Sarthak Jain**

B.Tech – Computer Science and Engineering (AI-IBM)  
Shri Vaishnav Vidyapeeth Vishwavidyalaya, Indore, Madhya Pradesh, India.

### Project Domain

Artificial Intelligence | Machine Learning | Groundwater Monitoring | Environmental Data Analytics

---

*Developed as an academic major project.*
