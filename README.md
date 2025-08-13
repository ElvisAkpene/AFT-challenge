# PFT Automated Interpretation System

A comprehensive tool for the automated preliminary interpretation of Pulmonary Function Tests (PFTs). This system uses the Global Lung Function Initiative (GLI-2012) reference equations to analyze spirometry data, determine ventilatory patterns (Normal, Obstructive, Restrictive, Mixed), assess severity, and generate detailed clinical reports.

## ⚠️ Medical Disclaimer

This is a preliminary report and a proof-of-concept tool. It is not a substitute for professional medical advice, diagnosis, or treatment. Final interpretation of any PFT data must be performed by a qualified physician who can correlate the findings with the patient's full clinical context. The authors of this software assume no liability for any decisions made based on its output.

## ✨ Key Features

**GLI-2012 Compliant**: Implements the modern, all-age, multi-ethnic GLI-2012 reference equations for calculating predicted values and Z-scores.

**Comprehensive Interpretation**:
- Determines ventilatory pattern: Normal, Obstructive, Restrictive, or Mixed.
- Classifies severity: Mild, Moderate, Moderately Severe, Severe, Very Severe.
- Assesses bronchodilator response and reversibility based on ATS/ERS criteria.

**Detailed Reporting**:
- Generates comprehensive JSON reports with patient data, results, interpretation, clinical impressions, and multi-faceted recommendations.
- Provides concise, human-readable summary reports in plain text.

**Multiple Interfaces**:
- **Web UI**: An interactive web-based form for single-patient interpretation and PDF report generation (powered by FastAPI and HTMX).
- **Command-Line Interface (CLI)**: A powerful CLI for processing single files, batch processing entire datasets (JSON/JSONL), and running data quality assessments.

**Validation Framework**: Includes a validation script to compare system interpretations against expert-labeled data, ensuring accuracy and facilitating model tuning.

**Data Quality Analysis**: Built-in validation checks for biological plausibility (e.g., FEV1 > FVC) and data completeness.

## 🧠 Core Interpretation Logic: The GLI-2012 Standard

This system's logic is grounded in the recommendations of the ERS/ATS Task Force and uses the GLI-2012 equations, as detailed in Quanjer PH, et al. Eur Respir J. 2012;40(6):1324-43. The key departure from older methods is the move from fixed percentages (e.g., FEV1/FVC < 70%) to a statistically robust Z-score system.

### 1. Predicted Value Calculation

Predicted values for FEV1 and FVC are calculated using a complex regression model that accounts for age, height, and sex. The core of the model is a log-log relationship with an age-dependent spline function to capture non-linear growth and decline.

The general form of the equation is:

```
ln(Predicted_Value) = Intercept + β₁ * ln(Height) + β₂ * ln(Age) + Spline(Age)
```

or

```
Predicted_Value = exp( Intercept + β₁ * ln(Height) + β₂ * ln(Age) + Spline(Age) )
```

- **ln**: Natural logarithm.
- **Coefficients (Intercept, β₁, β₂)**: These are specific to the parameter (FEV1, FVC), sex, and ethnicity. The current implementation uses the Caucasian dataset from the GLI-2012 paper.
- **Spline(Age)**: This is a crucial, non-linear function that adjusts the prediction across the entire lifespan (from age 3 to 95). It corrects for the rapid changes during childhood, adolescence, and aging that a simple linear model cannot capture. The implementation (`_calculate_spline`) uses a simplified piecewise function to approximate the GLI spline.

### 2. Z-Score Calculation (The Heart of GLI)

The Z-score (or standard deviation score) measures how many standard deviations an observation is from the predicted mean. It is the modern standard for interpretation.

The standard deviation (SD) itself varies with age. The GLI model uses another set of equations to model this changing variability, expressed as the Coefficient of Variation (CV). The Z-score is calculated as:

```python
# From PFT_interpreter.py
z_score = (measured_value - predicted_value) / (predicted_value * coefficient_of_variation)
```

A Z-score of -1.645 corresponds to the 5th percentile, which is the Lower Limit of Normal (LLN). Any value below this is considered statistically abnormal.

### 3. Pattern Determination

The interpretation flow follows a decision tree based on Z-scores, as recommended by ATS/ERS guidelines.

1. **Check for Obstruction**: Is the FEV1/FVC Z-score < -1.645?
   - **YES**: An obstructive component is present.
     - Then, check for restriction: Is the FVC Z-score < -1.645?
       - **YES**: The pattern is **MIXED**.
       - **NO**: The pattern is **OBSTRUCTIVE**.
   - **NO**: No obstructive component.
     - Then, check for restriction: Is the FVC Z-score < -1.645?
       - **YES**: The pattern is **RESTRICTIVE**.
       - **NO**: The pattern is **NORMAL**.

### 4. Severity Classification

Severity is primarily based on the FEV1 % Predicted. The thresholds vary slightly by pattern to align with common clinical guidelines.

| Pattern | FEV1 % Predicted | Severity |
|---------|------------------|----------|
| **Obstructive** | >= 80% | Mild |
|  | 50% - 79% | Moderate |
|  | 30% - 49% | Moderately Severe |
|  | < 30% | Severe |
| **Restrictive** | >= 70% | Mild |
|  | 60% - 69% | Moderate |
|  | 50% - 59% | Moderately Severe |
|  | < 50% | Severe |
| **Mixed** | >= 60% | Moderate |
|  | 40% - 59% | Moderately Severe |
|  | < 40% | Severe |

### 5. Bronchodilator Response

A significant response (i.e., reversibility) is defined as an increase of > 12% AND > 200 mL in either FEV1 or FVC from pre- to post-bronchodilator values.

## 🛠️ Installation

**Prerequisites**: Python 3.8+

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/PFT-test.git
   cd PFT-test
   ```

2. **Create and activate a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   (A requirements.txt should be created. Based on the code, these are the core dependencies.)
   ```bash
   pip install fastapi "uvicorn[standard]" jinja2
   ```

## 🚀 Usage

### 1. Web Interface

The most user-friendly way to interact with the system for single interpretations.

1. **Start the server**:
   ```bash
   uvicorn api.api_server:app --reload --host 0.0.0.0 --port 8080
   ```

2. **Open your browser** and navigate to `http://localhost:8080`.

3. **Fill out the form** with patient and spirometry data.

4. **Click "Generate Report"**. The results will appear on the page.

5. You can **export the generated report as a PDF**.

### 2. Command-Line Interface (CLI)

The CLI (`modules/PFT_main.py`) is ideal for batch processing or integration into automated workflows.

**General Syntax**:
```bash
python -m modules.PFT_main <command> --input <file_path> [options]
```

**Commands**:

- **single**: Process a single PFT record from a JSON file.
  ```bash
  # Generate a comprehensive JSON report
  python -m modules.PFT_main single -i path/to/sample.json -o output/

  # Generate a summary text report
  python -m modules.PFT_main single -i path/to/sample.json -o output/ --format text
  ```

- **batch**: Process a list of PFT records from a JSON or JSONL file.
  ```bash
  # Process a batch file, generating JSON reports for each record
  python -m modules.PFT_main batch -i PFT-data/PFT_data.json -o batch_output/ --format json
  ```
  This will create an output directory containing individual reports and a `batch_summary.json` with aggregate statistics.

- **quality**: Run a data quality assessment on a batch file without full interpretation.
  ```bash
  python -m modules.PFT_main quality -i PFT-data/PFT_data.json -o quality_reports/
  ```
  This generates a `quality_assessment.json` detailing valid/invalid records and specific validation errors.

## Input Data Format

The system expects input data in a specific JSON structure. Here is an example:

```json
{
    "file_name": "sample_pft.pdf",
    "demographics": {
        "age": 65,
        "sex": "M",
        "height_cm": 175.0,
        "weight_kg": 88.0
    },
    "pft_results": {
        "pre_bronchodilator": {
            "fvc": {"liters": 3.95, "percent_predicted": 98},
            "fev1": {"liters": 2.53, "percent_predicted": 78},
            "fev1_fvc_ratio": {"value": 64}
        },
        "post_bronchodilator": {
            "fvc": {"liters": 4.15, "percent_predicted": 103},
            "fev1": {"liters": 2.91, "percent_predicted": 90},
            "fev1_fvc_ratio": {"value": 70}
        }
    }
}
```

## 🔬 Validation

The project includes a validation script to measure the system's accuracy against a ground-truth dataset.

- **Dataset**: The validation script expects a JSON file (`PFT-data/PFT_data.json`) where each record contains an `impression` field with the expert's text-based interpretation.

- **Execution**:
  ```bash
  python -m validation.validate_system
  ```

- **Output**: The script will print a report comparing the system's Pattern and Severity classification against the parsed expert impression, providing accuracy percentages and a list of mismatches.

```
==================================================
      PFT SYSTEM VALIDATION REPORT
==================================================
Total Records Processed: 13

--- ACCURACY METRICS ---
Pattern Identification Accuracy:  92.31% (12/13)
Severity Classification Accuracy: 84.62% (11/13)
Overall Agreement (Pattern & Severity): 84.62% (11/13)

--- MISMATCH ANALYSIS ---
Found 2 records with disagreements.
Top 5 Mismatches for Review:
...
```

## 📂 Project Structure

```
PFT-test/
├── api/
│   └── api_server.py           # FastAPI server for the web interface
├── modules/
│   ├── PFT_interpreter.py      # Core logic for GLI calculations and interpretation
│   ├── PFT_main.py             # Main entry point for CLI, batch processing
│   └── PFT_report.py           # Report generation logic
├── templates/
│   ├── index.html              # Main HTML page for the web UI
│   └── results_partial.html    # Jinja2 template for displaying results via HTMX
├── validation/
│   └── validate_system.py      # Script to validate system accuracy against a dataset
├── PFT-data/
│   └── PFT_data.json           # Sample dataset for validation and batch testing
└── ... (other project files)
```

## 📈 Future Improvements

- **Expand GLI Ethnicities**: Implement coefficients for other ethnic groups (e.g., African-American, North/South East Asian) as defined in the GLI-2012 data.

- **Add More PFT Parameters**: Extend the interpretation to include Lung Volumes (TLC, RV) and Diffusing Capacity (DLCO) for a more complete picture of restrictive diseases.

- **Unit & Integration Testing**: Develop a robust test suite using a framework like pytest to ensure the reliability of individual functions and the system as a whole.

- **Configuration File**: Externalize settings like GLI coefficients and severity thresholds into a configuration file (e.g., `config.yaml`) for easier tuning.

- **Containerization**: Provide a Dockerfile to make deployment easier and more consistent across different environments.

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.
