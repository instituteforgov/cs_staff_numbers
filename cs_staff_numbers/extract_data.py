# %%
"""
    Purpose
        Extract new civil service staff numbers release data and append to database.
    Inputs
        - yaml: cs_staff_numbers/params/releases.yaml
            - Run parameters (source file, sheet name, NA values)
        - xlsx: 'ONS PSE <yyyy Qx>.xlsx'
            - ONS public sector employment source file for the latest quarter
        - sql: cs_staff_numbers/sql/extract/count_staff_numbers_by_quarter.sql
            - Counts existing rows for the new quarter (duplicate check)
        - sql: cs_staff_numbers/sql/extract/count_restated_by_quarter.sql
            - Counts existing restated rows for the previous quarter (duplicate check)
        - sql: cs_staff_numbers/sql/extract/select_organisations.sql
            - Canonical civil service organisation details
    Outputs
        - sql: civil_service.staff_numbers
            - New quarter rows appended as original='Original'; previous quarter rows appended as original='Restated'
    Notes
        - New data is appended to the database table, rather than existing rows being modified
        - Run parameters are loaded from cs_staff_numbers/params/releases.yaml (last entry used)
        - Carries out the following checks on data:
            - Structure
                - Sheet title starts with EXPECTED_TITLE
                - First group header row is EXPECTED_FIRST_GROUP
                - File year and quarter match EXPECTED_YEAR and EXPECTED_QUARTER
                - Column headers match EXPECTED_COL_HEADERS
                - First data row starts after the header block (row index >= FIRST_DATA_ROW)
                - Last data row is EXPECTED_LAST_ORG
            - Data quality
                - No unused NA values
                - No organisation rows with both headcount and FTE null
                - All keys in ORG_NAME_REPLACEMENTS appear in at least one organisation name
                - All strings in ORG_NAME_REMOVE_STRINGS appear in at least one organisation name
            - Before appending
                - No existing 'Restated' rows in the database for the previous quarter
                - No existing rows in the database for the new quarter
"""

import logging
import os

from cs_data_utils.utils import parse_quarter
import ds_utils.database_operations as dbo
import pandas as pd
from sqlalchemy import INT, NVARCHAR, SMALLINT, text
from sqlalchemy.dialects.mssql import TINYINT, UNIQUEIDENTIFIER
import yaml

from cs_staff_numbers.utils import add_ids, sql

# %%
# READ IN PARAMETERS
with open("params/releases.yaml", encoding="utf-8") as f:
    params = yaml.safe_load(f)[-1]

# %%
# SET CONSTANTS
SOURCE_DIR = "C:/Users/" + os.getlogin() + "/INSTITUTE FOR GOVERNMENT/Data - General/Civil service/Civil service - staff numbers (FTE and headcount)/Source"
SOURCE_FILE = params["source_file"]
SHEET_NAME = params["sheet_name"]
NA_VALUES = params["na_values"]
EXPECTED_TITLE = "Table 9: Civil Service employment by department and agency"
EXPECTED_YEAR = params["year"]
EXPECTED_QUARTER = params["quarter"]

# Table layout
ORG_NAME_COL = 0
DATE_HEADER_ROW = 2
COL_HEADER_ROW = 3
NEW_HEADCOUNT_COL = 2
NEW_FTE_COL = 3
PREV_HEADCOUNT_COL = 4
PREV_FTE_COL = 5
EXPECTED_COL_HEADERS = ["Headcount", "Full Time Equivalent"]
EXPECTED_FIRST_GROUP = "Attorney General's departments"
EXPECTED_LAST_ORG = "Total employment"
FIRST_DATA_ROW = 5

# Data cleaning
ORG_NAME_NOTE_PATTERN = r"\s*\d+$"
ORG_NAME_REPLACEMENTS = params["org_name_replacements"]
ORG_NAME_REMOVE_STRINGS = [
    "(excluding agencies)",
    "(incl. Office of the Advocate General for Scotland)",
    "(excluding trading funds)",
]

# %%
# CONFIGURE LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("logs/extract_data.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# %%
# CONNECT TO DATABASE
engine = dbo.connect_sql_db(
    driver="pyodbc",
    driver_version=os.environ["ODBC_DRIVER"],
    dialect="mssql",
    server=os.environ["ODBC_SERVER"],
    database=os.environ["ODBC_DATABASE"],
    authentication=os.environ["ODBC_AUTHENTICATION"],
    username=os.environ["AZURE_CLIENT_ID"],
    password=os.environ["AZURE_CLIENT_SECRET"],
)

# %%
# PARSE NEW RELEASE
source_path = f"{SOURCE_DIR}/{SOURCE_FILE}"

# Read as strings first to support header and NA value checks
df_raw_str = pd.read_excel(source_path, sheet_name=SHEET_NAME, header=None, dtype=str)
df_raw = pd.read_excel(source_path, sheet_name=SHEET_NAME, header=None, na_values=NA_VALUES)

# Check sheet title
sheet_title = str(df_raw_str.iloc[0, 0]).strip()
assert sheet_title.startswith(EXPECTED_TITLE), f"Unexpected sheet title in cell A1: '{sheet_title}'"

# Check first group header row
first_group = str(df_raw_str.loc[df_raw_str.index >= FIRST_DATA_ROW, ORG_NAME_COL].dropna().iloc[0]).strip()
assert first_group == EXPECTED_FIRST_GROUP, f"First group header is '{first_group}', expected '{EXPECTED_FIRST_GROUP}'"

# Parse quarter dates from header row
new_year, new_quarter = parse_quarter(str(df_raw_str.iloc[DATE_HEADER_ROW, NEW_HEADCOUNT_COL]).strip())
prev_year, prev_quarter = parse_quarter(str(df_raw_str.iloc[DATE_HEADER_ROW, PREV_HEADCOUNT_COL]).strip())

# Cross-check parsed dates against params
assert (new_year, new_quarter) == (EXPECTED_YEAR, EXPECTED_QUARTER), (f"File date ({new_year} Q{new_quarter}) does not match params ({EXPECTED_YEAR} Q{EXPECTED_QUARTER})")

logger.info("Starting extraction: %s Q%s from '%s'", new_year, new_quarter, SOURCE_FILE)

# Check column headers for new and previous quarter columns
for col_pair, label in [(NEW_HEADCOUNT_COL, "new"), (PREV_HEADCOUNT_COL, "previous")]:
    for offset, expected in enumerate(EXPECTED_COL_HEADERS):
        actual = str(df_raw_str.iloc[COL_HEADER_ROW, col_pair + offset]).strip()
        if actual != expected:
            logger.warning("%s quarter col %s: expected '%s', got '%s'", label, col_pair + offset, expected, actual)
            raise AssertionError("Column headers do not match expected structure — see warnings above")

# Data rows: org name present and headcount value present in new quarter column.
# This excludes group-header rows (headcount col null) and blank separator rows (org name col null).
df_data = df_raw[df_raw[ORG_NAME_COL].notna() & df_raw[NEW_HEADCOUNT_COL].notna()].copy()
df_data["organisation_name"] = df_data[ORG_NAME_COL].astype(str).str.strip()

# Remove note numbers from org names
df_data["organisation_name"] = df_data["organisation_name"].str.replace(ORG_NAME_NOTE_PATTERN, "", regex=True).str.strip()

# Check first and last data rows
assert df_data.index[0] >= FIRST_DATA_ROW, f"First data row found at unexpected position (raw row {df_data.index[0] + 1})"
last_org = df_data.iloc[-1]["organisation_name"]
assert last_org == EXPECTED_LAST_ORG, f"Last data row is not '{EXPECTED_LAST_ORG}': '{last_org}'"

# Check all replacement keys and remove strings are present in the data
_org_names = df_data["organisation_name"].tolist()
_missing_replacements = [k for k in ORG_NAME_REPLACEMENTS if not any(k in name for name in _org_names)]
assert not _missing_replacements, f"ORG_NAME_REPLACEMENTS keys not found in any organisation name: {_missing_replacements}"
_missing_remove_strings = [s for s in ORG_NAME_REMOVE_STRINGS if not any(s in name for name in _org_names)]
assert not _missing_remove_strings, f"ORG_NAME_REMOVE_STRINGS entries not found in any organisation name: {_missing_remove_strings}"

# Clean org names
for remove_str in ORG_NAME_REMOVE_STRINGS:
    df_data["organisation_name"] = df_data["organisation_name"].str.replace(remove_str, "", regex=False).str.strip()

for old_name, new_name in ORG_NAME_REPLACEMENTS.items():
    df_data["organisation_name"] = df_data["organisation_name"].str.replace(old_name, new_name, regex=False).str.strip()

# New quarter
df_new = df_data[["organisation_name", NEW_HEADCOUNT_COL, NEW_FTE_COL]].copy()
df_new.columns = ["organisation_name", "headcount", "fte"]
df_new["year"] = new_year
df_new["quarter"] = new_quarter
df_new["original"] = "Original"
df_new = df_new.reset_index(drop=True)

# Previous quarter
df_restated = df_data[["organisation_name", PREV_HEADCOUNT_COL, PREV_FTE_COL]].copy()
df_restated.columns = ["organisation_name", "headcount", "fte"]
df_restated["year"] = prev_year
df_restated["quarter"] = prev_quarter
df_restated["original"] = "Restated"
df_restated = df_restated.reset_index(drop=True)

# %%
# VALIDATE NEW DATA
# Check for unused NA values
used_na_values = {v for v in NA_VALUES if (df_raw_str == v).any().any()}
unused_na_values = [v for v in NA_VALUES if v not in used_na_values]
assert not unused_na_values, f"Unused NA values (remove from NA_VALUES): {unused_na_values}"

# Check for org rows where both headcount and FTE are null
df_null = df_new[df_new["headcount"].isna() & df_new["fte"].isna()]
assert len(df_null) == 0, f"{len(df_null)} rows with no headcount or FTE:\n{df_null['organisation_name'].to_string()}"

logger.info("Structure and data quality checks passed")

# %%
# DUPLICATE CHECK
n_existing_new = pd.read_sql(
    text(sql("count_staff_numbers_by_quarter.sql")),
    engine,
    params={"year": new_year, "quarter": new_quarter},
).iloc[0, 0]
assert n_existing_new == 0, (
    f"{new_year} Q{new_quarter} already has {n_existing_new} rows in civil_service.staff_numbers. "
    "Remove them before re-running, or check you are loading the correct release."
)

n_existing_restated = pd.read_sql(
    text(sql("count_restated_by_quarter.sql")),
    engine,
    params={"year": prev_year, "quarter": prev_quarter},
).iloc[0, 0]
assert n_existing_restated == 0, (
    f"{prev_year} Q{prev_quarter} already has {n_existing_restated} restated rows in civil_service.staff_numbers. "
    "Remove them before re-running, or check you are loading the correct release."
)

logger.info("Duplicate check passed — no existing rows for %s Q%s and no restated rows for %s Q%s", new_year, new_quarter, prev_year, prev_quarter)

# %%
# RESOLVE ORG IDs
df_organisation = pd.read_sql(sql("select_organisations.sql"), engine)


df_new = add_ids(df_new, df_organisation, new_quarter)
df_restated = add_ids(df_restated, df_organisation, prev_quarter)

# Report unresolved organisation names
unresolved = df_new.loc[df_new["organisation_id"].isna(), "organisation_name"].tolist()
if unresolved:
    logger.warning("Unresolved organisation names (%s):\n  %s", len(unresolved), "\n  ".join(unresolved))
else:
    logger.info("All organisation names resolved")

# %%
# APPEND TO DATABASE
_DTYPE = {
    "id": UNIQUEIDENTIFIER,
    "year": SMALLINT,
    "quarter": TINYINT,
    "organisation_id": UNIQUEIDENTIFIER,
    "organisation_name": NVARCHAR(200),
    "headcount": INT,
    "fte": INT,
    "original": NVARCHAR(20),
}

with engine.begin() as conn:
    pd.concat([df_new, df_restated], ignore_index=True).to_sql(
        schema="civil_service",
        name="staff_numbers",
        con=conn,
        if_exists="append",
        index=False,
        chunksize=1000,
        dtype=_DTYPE,
    )

logger.info("Appended %s new rows (%s Q%s) and %s restated rows (%s Q%s)", len(df_new), new_year, new_quarter, len(df_restated), prev_year, prev_quarter)

# %%
