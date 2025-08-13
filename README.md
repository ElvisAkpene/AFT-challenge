
# **PFT Automated Interpretation System**

---

## ⚠️ Medical Disclaimer

This software is a **proof-of-concept** and generates **preliminary, computer-assisted interpretations** of Pulmonary Function Tests (PFTs).
It **does not replace** professional medical judgment.
All final interpretations must be performed by a **qualified physician**, considering the patient’s full clinical picture.
The authors assume **no liability** for clinical decisions based on this tool.

---

## ✨ Key Features

* **GLI-2012 Compliant**
  Uses the Global Lung Function Initiative (GLI-2012) all-age, multi-ethnic reference equations to calculate predicted values and Z-scores.

* **Comprehensive Interpretation**

  * Determines ventilatory patterns: **Normal**, **Obstructive**, **Restrictive**, **Mixed**.
  * Classifies severity: Mild → Very Severe.
  * Evaluates bronchodilator response and reversibility.

* **Detailed Reporting**

  * Generates **JSON reports** with patient data, results, interpretation, and recommendations.
  * Produces **human-readable summaries** in plain text.

* **Multiple Interfaces**

  * **Web UI**: Interactive FastAPI + HTMX form for single-patient interpretation and PDF report generation.
  * **CLI**: Batch processing, dataset interpretation, and quality assessments.

* **Validation & Quality Checks**

  * Framework for comparing interpretations to expert-labelled datasets.
  * Built-in data plausibility checks (e.g., FEV1 > FVC, missing values).

---

## 🧠 Core Interpretation Logic — GLI-2012 Standard

This tool follows **ERS/ATS Task Force** recommendations and implements GLI-2012 equations from:
*Quanjer PH et al., Eur Respir J. 2012;40(6):1324–1343*

### 1. Predicted Values

Predicted FEV1 and FVC are calculated using:

```
ln(Predicted) = Intercept + β₁·ln(Height) + β₂·ln(Age) + Spline(Age)
Predicted     = exp(ln(Predicted))
```

* **Height & Age**: Logged for regression.
* **Spline(Age)**: Non-linear age adjustments from GLI-2012.
* **Coefficients**: Current version uses Caucasian dataset.

---

### 2. Z-Score Calculation

```
Z = (Measured − Predicted) / (Predicted × CV)
```

* **CV** (Coefficient of Variation) models SD changes with age.
* **LLN** (Lower Limit of Normal) = Z-score ≤ -1.645 (\~5th percentile).

---

### 3. Pattern Determination

* **Obstruction**: FEV1/FVC Z-score < -1.645
* **Restriction**: FVC Z-score < -1.645
* Decision tree classifies: Obstructive, Restrictive, Mixed, Normal.

---

### 4. Severity Classification (FEV1 % Predicted)

| Pattern     | Severity Cutoffs                                            |
| ----------- | ----------------------------------------------------------- |
| Obstructive | ≥80% Mild, 50–79% Moderate, 30–49% Mod. Severe, <30% Severe |
| Restrictive | ≥70% Mild, 60–69% Moderate, 50–59% Mod. Severe, <50% Severe |
| Mixed       | ≥60% Moderate, 40–59% Mod. Severe, <40% Severe              |

---

### 5. Bronchodilator Response

Significant if:

* ΔFEV1 or ΔFVC > **12%** *and* > **200 mL** (post vs pre).

---

## 🛠 Installation

**Requirements**: Python 3.8+

```bash
git clone <repository_url>
cd PFT-test
python -m venv venv
# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install fastapi "uvicorn[standard]" jinja2
```

---

## 🚀 Usage

### 1. Web Interface

```bash
uvicorn api.api_server:app --reload --host 0.0.0.0 --port 8080
```

* Visit: `http://localhost:8080`
* Fill form → Generate Report → Export as PDF.

---

### 2. Command-Line Interface

**Syntax**:

```bash
python -m modules.PFT_main <command> --input <file> [options]
```

**Commands**:

* `single` → Interpret one JSON record
* `batch` → Interpret JSON/JSONL dataset
* `quality` → Run plausibility checks only

Example:

```bash
python -m modules.PFT_main single -i sample.json -o output/
python -m modules.PFT_main batch -i PFT-data/PFT_data.json -o batch_output/ --format json
```

---

## 📄 Input Data Format (JSON)

```json
{
    "file_name": "sample_pft.pdf",
    "demographics": { "age": 65, "sex": "M", "height_cm": 175.0, "weight_kg": 88.0 },
    "pft_results": {
        "pre_bronchodilator": {
            "fvc": { "liters": 3.95, "percent_predicted": 98 },
            "fev1": { "liters": 2.53, "percent_predicted": 78 },
            "fev1_fvc_ratio": { "value": 64 }
        },
        "post_bronchodilator": {
            "fvc": { "liters": 4.15, "percent_predicted": 103 },
            "fev1": { "liters": 2.91, "percent_predicted": 90 },
            "fev1_fvc_ratio": { "value": 70 }
        }
    }
}
```

---

## 🔬 Validation

Run:

```bash
python -m validation.validate_system
```

Outputs: Pattern & Severity accuracy vs expert interpretation.

---

## 📂 Project Structure

```
PFT-test/
├── api/                # FastAPI server
├── modules/            # Core logic & CLI
├── templates/          # HTML templates
├── validation/         # Validation scripts
├── PFT-data/           # Sample datasets
└── ...
```

---

## 📈 Future Improvements

* Multi-ethnic GLI implementation.
* Add Lung Volumes (TLC, RV) & DLCO.
* Configurable thresholds & GLI coefficients.
* Unit & integration test suite.
* Docker container for deployment.

---

## 📜 License

MIT License — see `LICENSE` file.

---
