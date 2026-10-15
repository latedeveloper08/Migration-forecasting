"""Data loading, cleaning and feature building for the migration forecasting project.

Every step here only looks backwards in time, so no future values leak into a row.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Short names for the World Bank series used in the project
SERIES = {
    "Net migration": "net_migration",
    "GDP per capita (current US$)": "gdp_per_capita",
    "Unemployment, total (% of total labor force) (modeled ILO estimate)": "unemployment",
    "Political Stability and Absence of Violence/Terrorism: Estimate": "political_stability",
    "Poverty headcount ratio at national poverty lines (% of population)": "poverty_rate",
    "Average transaction cost of sending remittances from a specific country (%)": "remittance_cost",
}

# World Bank regional and income-group aggregates. They are sums or averages of
# real countries, so keeping them would count the same people twice.
AGGREGATE_CODES = {
    "AFE", "AFW", "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS", "EMU",
    "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "LAC", "LCN",
    "LDC", "LIC", "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAC", "OED", "OSS",
    "PRE", "PSS", "PST", "TEA", "TEC", "TLA", "TMN",
}

LAGS = (1, 2, 3)


def load_long(path: str | Path) -> pd.DataFrame:
    """Read the World Bank extract (long format) and return clean numeric values."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    # Values were exported with a leading apostrophe, e.g. "'-44418"
    df["Value"] = pd.to_numeric(df["Value"].astype(str).str.replace("'", "", regex=False), errors="coerce")
    df = df[df["Series Name"].isin(SERIES)].copy()
    df["series"] = df["Series Name"].map(SERIES)
    return df


def to_panel(long_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape to one row per country and year, with one column per series."""
    panel = (
        long_df.pivot_table(index=["Country Code", "Country Name", "Year"], columns="series", values="Value")
        .reset_index()
        .rename(columns={"Country Code": "code", "Country Name": "country", "Year": "year"})
    )
    panel.columns.name = None
    for col in SERIES.values():
        if col not in panel.columns:
            panel[col] = np.nan
    return panel.sort_values(["code", "year"]).reset_index(drop=True)


def drop_aggregates(panel: pd.DataFrame) -> pd.DataFrame:
    return panel[~panel["code"].isin(AGGREGATE_CODES)].copy()


def drop_incomplete_countries(panel: pd.DataFrame, min_years: int = 40) -> pd.DataFrame:
    """Remove countries with too few years of net migration (e.g. one cut off by the export limit)."""
    counts = panel.groupby("code")["net_migration"].count()
    keep = counts[counts >= min_years].index
    return panel[panel["code"].isin(keep)].copy()


def add_features(panel: pd.DataFrame, predictors: list[str]) -> pd.DataFrame:
    """Add lagged target values and last year's predictors.

    - Lags use the real past values of net migration (no filling).
    - Predictors are forward-filled within each country only, so a gap is filled
      with the latest earlier value and never with a later one.
    - Predictors are then shifted by one year (`<name>_prev`). To forecast year t
      you only know the indicators up to year t-1, so that is all the model gets.
    - GDP per capita is given on a log10 scale, because it spans several orders of magnitude.
    """
    out = panel.sort_values(["code", "year"]).copy()
    grouped = out.groupby("code")
    for k in LAGS:
        out[f"net_migration_lag{k}"] = grouped["net_migration"].shift(k)
    for col in predictors:
        filled = grouped[col].ffill()
        out[f"{col}_prev"] = filled.groupby(out["code"]).shift(1)
    if "gdp_per_capita" in predictors:
        out["log_gdp_per_capita_prev"] = np.log10(out["gdp_per_capita_prev"])
    return out


def build_dataset(path: str | Path, predictors: list[str]) -> pd.DataFrame:
    """Full pipeline: load, reshape, drop aggregates and partial countries, add features."""
    panel = to_panel(load_long(path))
    panel = drop_aggregates(panel)
    panel = drop_incomplete_countries(panel)
    data = add_features(panel, predictors)
    # A row needs a target and all three lags to be usable
    lag_cols = [f"net_migration_lag{k}" for k in LAGS]
    return data.dropna(subset=["net_migration", *lag_cols]).reset_index(drop=True)
