# Data

`wdi_migration_extract.csv` is a long-format export from the World Bank DataBank: one row per country, year and indicator.

| Column | Meaning |
|---|---|
| Country Code | ISO 3-letter code |
| Country Name | Country or aggregate name |
| Year | 1975 to 2024 |
| Series Name | Indicator name |
| Value | Indicator value (exported with a leading apostrophe, which `src/prep.py` strips) |

## Indicators

| Indicator | World Bank code |
|---|---|
| Net migration | SM.POP.NETM |
| GDP per capita (current US$) | NY.GDP.PCAP.CD |
| Unemployment, total (% of labour force, modelled ILO estimate) | SL.UEM.TOTL.ZS |
| Political Stability and Absence of Violence/Terrorism: Estimate | PV.EST |
| Poverty headcount ratio at national poverty lines (% of population) | SI.POV.NAHC |
| Average transaction cost of sending remittances from a specific country (%) | SI.RMT.COST.OB.ZS |

## Known limits

- The export hit DataBank's 30,000-row cap. It covers entities alphabetically from Afghanistan to Russia, and Russia only for 1975 to 1985. Run `python scripts/download_wdi.py` to get every country as `data/wdi_full.csv`.
- The file includes regional and income-group aggregates. `src/prep.py` removes them.

## Licence

World Bank data is published under the [Creative Commons Attribution 4.0 licence](https://creativecommons.org/licenses/by/4.0/). Source: World Bank, World Development Indicators and Worldwide Governance Indicators.
