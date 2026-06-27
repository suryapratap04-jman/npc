import json
from pathlib import Path

notebook_path = Path(r"c:\Users\SuryaPratapSingh\Documents\project\notebooks\01_data_profiling.ipynb")
notebook_path.parent.mkdir(parents=True, exist_ok=True)

# Build cells
cells = []

# Cell 1: Title & Introduction
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# AI-Powered Resource Recommendation System\n",
        "## Part 1: Data Discovery, Cleaning, & Validation Pipeline\n",
        "\n",
        "This notebook serves as the master documentation for the data pipeline. It explains the steps taken to profile the raw hackathon datasets, validate relationships, clean data anomalies, and prepare clean outputs for downstream machine learning and recommendation models.\n",
        "\n",
        "### Project Directory Structure\n",
        "```\n",
        "project/\n",
        "├── rawData/                  (Read-only raw data files)\n",
        "├── cleanedData/              (Deduplicated, parsed, standardized outputs)\n",
        "├── cleaning/                 (Modular python scripts)\n",
        "│   ├── config.py             (Paths and mappings)\n",
        "│   ├── utils.py              (Date parsing, experience converter, type cast helpers)\n",
        "│   ├── clean_data.py         (Main orchestrator script)\n",
        "│   ├── validation.py         (Post-cleaning validation checks)\n",
        "│   └── feature_engineering.py(Feature recommendations)\n",
        "└── notebooks/\n",
        "    └── 01_data_profiling.ipynb (This documentation)\n",
        "```"
    ]
})

# Cell 2: Imports
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import os\n",
        "import pandas as pd\n",
        "import numpy as np\n",
        "import matplotlib.pyplot as plt\n",
        "from IPython.display import Image, display\n",
        "from pathlib import Path\n",
        "\n",
        "clean_dir = Path(\"../cleaning\")\n",
        "cleaned_data_dir = Path(\"../cleanedData\")\n",
        "reports_dir = Path(\"../cleaning/reports\")"
    ]
})

# Cell 3: Loading Profiling Summaries
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 1. Dataset Profiling Summary\n",
        "We profile raw file structures (row count, columns, duplicates, memory footprints, primary and foreign key candidates) to check database shapes before cleaning."
    ]
})

# Cell 4: View Dataset Summary Table
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_summary = pd.read_csv(clean_dir / \"dataset_summary.csv\")\n",
        "df_summary"
    ]
})

# Cell 5: Data Dictionary introduction
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 2. Data Dictionary\n",
        "A detailed column-level breakdown showing unique values, null count, null percentage, data ranges, and sample values."
    ]
})

# Cell 6: View Data Dictionary
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_dict = pd.read_csv(clean_dir / \"data_dictionary.csv\")\n",
        "display(df_dict.head(10))\n",
        "print(f\"Total columns defined in schema: {len(df_dict)}\")"
    ]
})

# Cell 7: Missing value explanation
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 3. Missing Value Analysis\n",
        "We identify missing values by column to decide on appropriate cleaning and replacement strategies."
    ]
})

# Cell 8: View Missing Value Heatmap
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "display(Image(filename=reports_dir / \"missing_values.png\"))\n",
        "display(Image(filename=reports_dir / \"null_percentage.png\"))"
    ]
})

# Cell 9: Duplicate analysis
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 4. Duplicate Analysis\n",
        "We look for duplicate rows and keys to prevent data leakage in training datasets."
    ]
})

# Cell 10: View duplicate report
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_dups = pd.read_csv(clean_dir / \"duplicate_report.csv\")\n",
        "display(df_dups)\n",
        "display(Image(filename=reports_dir / \"duplicate_summary.png\"))"
    ]
})

# Cell 11: Relationship Analysis
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 5. Relationship Analysis & Referential Integrity\n",
        "We evaluate primary/foreign key mappings (e.g. employee_id references from allocations to employee master) and identify broken references."
    ]
})

# Cell 12: View Relationship Report
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_rel = pd.read_csv(clean_dir / \"relationship_report.csv\")\n",
        "df_rel"
    ]
})

# Cell 13: Cleaning operations documentation
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 6. Cleaning Strategies Implemented\n",
        "\n",
        "The following operations were implemented programmatically in `cleaning/clean_data.py`:\n",
        "\n",
        "1. **Column Standardizations**: Convert columns to lowercase snake_case (e.g., `Employee ID` $\\rightarrow$ `employee_id`).\n",
        "2. **Text Normalization**: Clean spacing, remove trailing characters, and map variations (e.g., `Python`/`PYTHON` $\\rightarrow$ `Python`, `ReactJS`/`React.js` $\\rightarrow$ `React`). ReAct AI prompting framework was protected from frontend React mapping.\n",
        "3. **Date Standardizations**: Parsed DD-MM-YYYY strings and formatted consistently to standard `YYYY-MM-DD` datetimes.\n",
        "4. **Casting Experience ranges**: Strings like `'1-2 Year'` were parsed into numeric midpoint averages (`1.5`) for modeling compatibility.\n",
        "5. **Casting Allocation percentages**: Strings like `'75%'` were parsed into numeric integers (`75`).\n",
        "6. **Consolidation of Competencies**: The three Excel sheets representing Solution Enablers, Consultants, and Senior Engineers were merged into a single standardized table (`competencies_clean.csv`) aligning overlapping scoring dimensions.\n",
        "7. **Consolidation of Pipeline**: Extracted and cleaned the `Forecast` sheet into `pipeline_clean.csv`.\n",
        "8. **Handling Impossible Values**: Six allocations where the end date occurred before the start date were flagged using `impossible_value_flag = 1` rather than silently dropped.\n",
        "9. **Null Value Handling**: Missing locations, job designations, and managers were mapped to `'Unknown'`. Active employees' resignation dates were left as null/NaT."
    ]
})

# Cell 14: Data Quality Report
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 7. Data Quality Scores (out of 100)\n",
        "Quality Scores are computed as the average of Completeness, Consistency (no impossible values), Uniqueness (no duplicate primary keys), and Integrity (no orphaned references)."
    ]
})

# Cell 15: View Quality Scores
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_quality = pd.read_csv(clean_dir / \"quality_report.csv\")\n",
        "df_quality"
    ]
})

# Cell 16: Validation
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 8. Programmatic Validation Assertions\n",
        "We run assertion checks using `cleaning/validation.py`. The output verification status log is displayed below:"
    ]
})

# Cell 17: Read Validation log
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "with open(clean_dir / \"validation_report.txt\", \"r\", encoding=\"utf-8\") as f:\n",
        "    print(f.read())"
    ]
})

# Cell 18: Visualizations preview
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 9. Clean Data Exploratory Visuals"
    ]
})

# Cell 19: View Clean Visuals
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "display(Image(filename=reports_dir / \"dataset_sizes.png\"))\n",
        "display(Image(filename=reports_dir / \"top_skills.png\"))\n",
        "display(Image(filename=reports_dir / \"top_competencies.png\"))\n",
        "display(Image(filename=reports_dir / \"allocation_distribution.png\"))"
    ]
})

# Cell 20: Feature Engineering Suggestions introduction
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### 10. Downstream Feature Recommendations\n",
        "We recommend engineered features for resources and projects, exported as `feature_recommendations.csv`:"
    ]
})

# Cell 21: View Feature Recommendations
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "df_feats = pd.read_csv(clean_dir / \"feature_recommendations.csv\")\n",
        "df_feats"
    ]
})

# Compile notebook json
notebook_data = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook_data, f, indent=1)

print(f"Generated notebook at: {notebook_path}")
