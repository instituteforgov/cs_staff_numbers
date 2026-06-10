# %%
"""
    Purpose
        Extract existing civil service staff numbers data and save to database.
    Inputs
        - xlsx: "Civil service staff numbers.xlsx"
            - Collated civil service staff numbers data
        - sql: civil_service.organisation
            - Canonical civil service organisation details
    Outputs
        - sql: civil_service.staff_numbers
    Notes
        - Replaces existing data in `civil_service.staff_numbers`
"""

import os
import uuid

from cs_organisations.resolve import resolve_org_id
import ds_utils.database_operations as dbo
import pandas as pd
from sqlalchemy import INT, NVARCHAR, SMALLINT
from sqlalchemy.dialects.mssql import TINYINT, UNIQUEIDENTIFIER

from cs_staff_numbers.utils import normalise_column_names

# %%
# SET CONSTANTS
BASE_PATH = "C:/Users/" + os.getlogin() + "/INSTITUTE FOR GOVERNMENT/Data - General/Civil service/Civil service - staff numbers (FTE and headcount)/Civil service staff numbers.xlsx"
SHEET_NAME = "Data.Collated staff numbers"
NA_VALUES = ["-", "..", "N/A"]
CALCULATED_COLUMNS = [
    "Release number",
    "Departmental group",
    "Organisation type",
    "Managed",
    "Census",
    "Ministerial department?",
    "Ministerial department/executive agency/selected non-ministerial department",
    "Latest organisation",
    "Latest departmental group"
]
COLUMN_RENAMES = {"organisation": "organisation_name"}
INSERT_ORG_ID_BEFORE_COL = "Organisation"

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
# READ IN DATA
# NB: Sets non-numeric values to NaN
df_cs_staff_numbers = pd.read_excel(BASE_PATH, sheet_name=SHEET_NAME, na_values=NA_VALUES)

# %%
# EDIT DATA
# Drop rows where 'Organisation' is blank
df_cs_staff_numbers = df_cs_staff_numbers.dropna(subset=["Organisation"])

# Add UUID columns
df_cs_staff_numbers.insert(0, "id", [str(uuid.uuid4()) for _ in range(len(df_cs_staff_numbers))])

# Drop calculated columns
df_cs_staff_numbers = df_cs_staff_numbers.drop(columns=CALCULATED_COLUMNS)


# Normalise column names to snake_case
df_cs_staff_numbers.columns = [normalise_column_names(col) for col in df_cs_staff_numbers.columns]
_insert_before = normalise_column_names(INSERT_ORG_ID_BEFORE_COL)

# Rename columns
df_cs_staff_numbers = df_cs_staff_numbers.rename(columns=COLUMN_RENAMES)
_insert_before = COLUMN_RENAMES.get(_insert_before, _insert_before)

# Drop ' - <yyyy> iteration' strings from organisation names that have been reused (e.g. "Department for Culture, Media and Sport - 2017 iteration" becomes "Department for Culture, Media and Sport")
df_cs_staff_numbers["organisation_name"] = df_cs_staff_numbers["organisation_name"].str.replace(r"\s*-\s*\d{4}\s*iteration\s*", "", regex=True)

# %%
# Resolve organisation ids
# Temporally match each row's organisation name and year to civil_service.organisation.
# Rows that don't match (e.g. aggregations like "Civil Service benchmark") remain NULL.
df_organisation = pd.read_sql(
    """select
        o.id,
        o.name,
        o.start_year,
        o.start_quarter,
        o.end_year,
        o.end_quarter
    from civil_service.organisation o""",
    engine
)

df_cs_staff_numbers.insert(
    df_cs_staff_numbers.columns.get_loc(_insert_before),
    "organisation_id",
    resolve_org_id(df_cs_staff_numbers, df_organisation, quarter_col="quarter")
)

# %%
# SAVE DATA TO DATABASE
df_cs_staff_numbers.to_sql(
    schema="civil_service",
    name="staff_numbers",
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=1000,
    dtype={
        "id": UNIQUEIDENTIFIER,
        "year": SMALLINT,
        "quarter": TINYINT,
        "organisation_id": UNIQUEIDENTIFIER,
        "organisation_name": NVARCHAR(200),
        "headcount": INT,
        "fte": INT,
        "original": NVARCHAR(20),
    }
)

# %%
