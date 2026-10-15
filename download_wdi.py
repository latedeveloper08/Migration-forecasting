"""Download the full World Bank data used in this project.

The CSV in data/ came from a manual export that stopped at 30,000 rows, so it only
covers countries from Afghanistan to Romania. This script pulls the same six
indicators for every country from the World Bank API and writes
data/wdi_full.csv in the same long format.

Usage (from the repo root):
    python scripts/download_wdi.py

Then set DATA = ROOT / "data" / "wdi_full.csv" in the notebook.
"""

import csv
import json
import time
import urllib.request
from pathlib import Path

API = "https://api.worldbank.org/v2"
YEARS = "1975:2024"
OUT = Path(__file__).resolve().parent.parent / "data" / "wdi_full.csv"

# Indicator code -> series name used in the project (matches the original export)
INDICATORS = {
    "SM.POP.NETM": "Net migration",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "SL.UEM.TOTL.ZS": "Unemployment, total (% of total labor force) (modeled ILO estimate)",
    "PV.EST": "Political Stability and Absence of Violence/Terrorism: Estimate",
    "SI.POV.NAHC": "Poverty headcount ratio at national poverty lines (% of population)",
    "SI.RMT.COST.OB.ZS": "Average transaction cost of sending remittances from a specific country (%)",
}


def fetch_all(url: str) -> list[dict]:
    """Fetch every page of a World Bank API v2 JSON endpoint."""
    rows, page, pages = [], 1, 1
    while page <= pages:
        with urllib.request.urlopen(f"{url}&page={page}", timeout=60) as resp:
            meta, data = json.load(resp)
        pages = int(meta["pages"])
        rows.extend(data or [])
        page += 1
        time.sleep(0.2)
    return rows


def real_countries() -> dict[str, str]:
    """Return {iso3 code: name} for countries only, leaving out regional and income aggregates."""
    rows = fetch_all(f"{API}/country?format=json&per_page=500")
    return {r["id"]: r["name"] for r in rows if r["region"]["value"] != "Aggregates"}


def main() -> None:
    countries = real_countries()
    print(f"{len(countries)} countries")
    records = []
    for code, series in INDICATORS.items():
        rows = fetch_all(f"{API}/country/all/indicator/{code}?format=json&date={YEARS}&per_page=20000")
        kept = [
            (r["countryiso3code"], countries[r["countryiso3code"]], int(r["date"]), series, r["value"])
            for r in rows
            if r["value"] is not None and r["countryiso3code"] in countries
        ]
        print(f"{code}: {len(kept):,} values")
        records.extend(kept)

    records.sort(key=lambda r: (r[1], r[3], r[2]))
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Country Code", "Country Name", "Year", "Series Name", "Value"])
        writer.writerows(records)
    print(f"Wrote {len(records):,} rows to {OUT}")


if __name__ == "__main__":
    main()
