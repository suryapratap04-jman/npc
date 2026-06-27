import re
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
from cleaning.config import RAW_DIR, RAW_FILES, TARGET_DATE_FORMAT, RAW_DATE_FORMAT, SKILL_MAP

logger = logging.getLogger(__name__)

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def load_dataset(key: str) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Loads raw dataset based on configuration key. Returns DataFrame or dict of DataFrames (for Excel with multiple sheets)."""
    if key not in RAW_FILES:
        raise ValueError(f"Key {key} not found in RAW_FILES")
    
    path = RAW_DIR / RAW_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Raw file {path} not found")
        
    logger.info(f"Loading raw dataset: {key} from {path.name}")
    if path.suffix == ".csv":
        return pd.read_csv(path)
    elif path.suffix == ".xlsx":
        xl = pd.ExcelFile(path)
        if len(xl.sheet_names) == 1:
            return pd.read_excel(path, sheet_name=xl.sheet_names[0])
        else:
            # Return dict of sheets
            return {sheet: pd.read_excel(path, sheet_name=sheet) for sheet in xl.sheet_names}
    else:
        raise ValueError(f"Unsupported file format for: {path.name}")

def standardize_col_name(col: Any) -> str:
    """Standardizes column headers to lower snake_case, cleaning non-breaking characters."""
    if not isinstance(col, str):
        return str(col)
    # Replace non-breaking spaces and hyphens with normal spaces/hyphens
    c = col.replace("\xa0", " ").replace("\u2011", "-")
    c = c.strip().lower()
    c = re.sub(r"[^a-z0-9_]+", "_", c)
    c = re.sub(r"_+", "_", c)
    return c.strip("_")

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of the dataframe with standardized column names."""
    df_copy = df.copy()
    df_copy.columns = [standardize_col_name(c) for c in df_copy.columns]
    return df_copy

def clean_text_field(val: Any) -> Any:
    """Trim whitespace, collapse double spaces, handle NaN."""
    if pd.isna(val) or not isinstance(val, str):
        return val
    # Remove non-breaking spaces
    v = val.replace("\xa0", " ").replace("\u200b", "")
    # Collapse multiple spaces
    v = re.sub(r"\s+", " ", v)
    return v.strip()

def parse_date(val: Any) -> Any:
    """Parses date string into standard YYYY-MM-DD format."""
    if pd.isna(val):
        return pd.NaT
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(val)
    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return pd.NaT
        # Try DD-MM-YYYY first (CSV format)
        try:
            return pd.to_datetime(val_str, format="%d-%m-%Y", errors="raise")
        except ValueError:
            pass
        # Try YYYY-MM-DD (Excel output / ISO)
        try:
            return pd.to_datetime(val_str, format="%Y-%m-%d", errors="raise")
        except ValueError:
            pass
        # Fallback to general parsing
        try:
            return pd.to_datetime(val_str, errors="coerce")
        except:
            return pd.NaT
    return pd.to_datetime(val, errors="coerce")

def parse_experience(val: Any) -> Optional[float]:
    """Converts experience strings like '1-2 Year' or '5' to a numeric midpoint float."""
    if pd.isna(val):
        return None
    val_str = str(val).strip().lower()
    if not val_str:
        return None
    
    # Range pattern, e.g. "1-2 Years" or "1-2 Year"
    range_match = re.search(r"(\d+)\s*-\s*(\d+)", val_str)
    if range_match:
        try:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return (low + high) / 2.0
        except ValueError:
            pass
            
    # Single integer pattern, e.g., "5 Years" or "5"
    single_match = re.search(r"(\d+)", val_str)
    if single_match:
        try:
            return float(single_match.group(1))
        except ValueError:
            pass
            
    return None

def parse_utilization(val: Any) -> Optional[float]:
    """Converts utilization/allocation strings like '75%' to float (75.0)."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return None
    # Remove percentage signs
    val_str = val_str.replace("%", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return None

def standardize_skill_name(skill: Any) -> Any:
    """Normalizes Skill/SubSkill names using SKILL_MAP config, protecting 'ReAct' framework distinct."""
    if pd.isna(skill) or not isinstance(skill, str):
        return skill
    skill_clean = clean_text_field(skill)
    skill_lower = skill_clean.lower()
    
    # Specific protection for ReAct / Tool-calling frameworks
    if "react / tool-calling" in skill_lower or "react / tool calling" in skill_lower:
        return "ReAct / Tool-calling frameworks"
        
    for k, v in SKILL_MAP.items():
        if skill_lower == k:
            return v
    return skill_clean
