from pathlib import Path
import uuid

from cs_organisations.resolve import resolve_org_id
import pandas as pd


def sql(filename: str) -> str:
    """Load a SQL file from the sql/extract/ directory relative to this module.

    Args:
        filename: SQL filename, e.g. 'select_organisations.sql'.

    Returns:
        SQL string.
    """
    return (Path(__file__).parent / "sql" / "extract" / filename).read_text(encoding="utf-8")


def add_ids(
    df: pd.DataFrame,
    df_organisation: pd.DataFrame,
    quarter: int,
) -> pd.DataFrame:
    """Add row id and organisation_id columns to a release DataFrame.

    Args:
        df: DataFrame with at least 'organisation_name' and 'year' columns.
        df_organisation: Reference DataFrame with organisation id/name/dates.
        quarter: Quarter of all rows in df, passed as a scalar to resolve_org_id.

    Returns:
        DataFrame with 'id' prepended and 'organisation_id' inserted before 'organisation_name'.
    """
    df = df.copy()
    df.insert(0, "id", [str(uuid.uuid4()) for _ in range(len(df))])
    df.insert(
        df.columns.get_loc("organisation_name"),
        "organisation_id",
        resolve_org_id(df, df_organisation, quarter_col=quarter),
    )
    return df
