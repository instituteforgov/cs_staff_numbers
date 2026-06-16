# Civil service staff numbers

Scripts for extracting civil service staff numbers data from ONS PSE releases and loading it into the IfG's research database.

## Related repositories

- 🔓 [Civil service data utilities](https://github.com/instituteforgov/cs_data_utils/): Shared data utilities for civil service data pipelines
- 🔓 [Civil service organisations](https://github.com/instituteforgov/cs_organisations/): Scripts for managing canonical civil service organisation data, used to augment the civil service staff numbers data with things like latest departmental groups

## Project structure

```
├── cs_staff_numbers/
│   ├── legacy/
│   │   ├── sql/
│   │   │   └── compare_data.sql
│   │   ├── compare_data.py
│   │   └── extract_legacy_data.py
│   ├── params/
│   │   └── releases.yaml
│   ├── sql/
│   │   ├── export/
│   │   │   └── select_data.sql
│   │   └── extract/
│   │       ├── count_restated_by_quarter.sql
│   │       ├── count_staff_numbers_by_quarter.sql
│   │       └── select_organisations.sql
│   ├── extract_data.py
│   └── utils.py
├── logs/
│   └── extract_data.log
├── params/
│   └── releases.yaml
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
```

## Extracting a new release

1. **Download the source file.** Download the latest ONS public sector employment release and save it to the `Source` directory (external to this repo).

1. **Add an entry to `params/releases.yaml`.** Add a new entry at the end of the file with the year, quarter, source filename, sheet name and any NA values used in the file. The script always uses the last entry.

1. **Run `cs_staff_numbers/extract_data.py`.** The script validates the file structure and data quality, checks for duplicate rows in the database, resolves organisation IDs, and appends the new and restated rows to `civil_service.staff_numbers`.

1. **Review the output.** Check the log (`logs/extract_data.log`) for any warnings, in particular unresolved organisation names. Unresolved names will need to be added to the canonical organisation data in the [cs_organisations](https://github.com/instituteforgov/cs_organisations/) repo before re-running.

1. **Refresh Excel queries.** Refresh uses of `cs_staff_numbers/sql/export/select_data.sql` in Excel working files to re-export the augmented dataset for use.

## Scripts

| File | Description |
| ---- | ----------- |
| `cs_staff_numbers/extract_data.py` | Extracts data from the latest ONS PSE release file, transforms it and loads it to the research database. |
| `cs_staff_numbers/sql/export/select_data.sql` | Script to be used for (re-)insertion of augmented data into Excel. Duplicates `cs_staff_numbers/legacy/sql/compare_data.sql`, with the following differences to columns: <ul><li><strong>Only one row per organisation and quarter returned</strong>: 'Restated' rows favoured, with 'Original' returned for quarters where it is not</li><li><strong>Column order changed</strong></li><li><strong>Organisation type</strong>: Reported as is</li><li><strong>IfG core department</strong>: Added</li><li><strong>Latest organisation</strong>: Latest actual organisation always reported, rather than latest determinate organisation</li><li><strong>Latest departmental group</strong>: Latest actual (IfG) departmental group always reported, rather than latest determinate organisation</li></ul> |

### Legacy scripts

These scripts were used to make an initial, one-time extraction of existing collated data into the database. They are retained for reference.

| File | Description |
| ---- | ----------- |
| `cs_staff_numbers/legacy/extract_legacy_data.py` | Reads existing civil service staff numbers data and saves to database. |
| `cs_staff_numbers/legacy/sql/compare_data.sql` | Replicates the collated data from the civil service staff numbers working file, to be used as the basis for comparison in `compare_data.py`. |
| `cs_staff_numbers/legacy/compare_data.py` | Validates that the augmented SQL output matches the source Excel file. |

## Environment variables
The scripts require the following environment variables to be set:

### Database connection (Azure SQL Database)
| Variable | Description |
| -------- | ----------- |
| `ODBC_DRIVER` | ODBC driver version for SQL Server (e.g., `ODBC Driver 18 for SQL Server`) |
| `ODBC_SERVER` | SQL Server hostname |
| `ODBC_DATABASE` | Database name |
| `ODBC_AUTHENTICATION` | Authentication method (e.g., `ActiveDirectoryServicePrincipal`) |
| `AZURE_CLIENT_ID` | Azure service principal client ID used for database authentication |
| `AZURE_CLIENT_SECRET` | Azure service principal client secret used for database authentication |

## Contributing

This project uses `pre-commit` hooks to ensure code quality. To set up:

1. Install `pre-commit` on your system if you don't already have it:

    ```bash
    pip install pre-commit
    ```

1. Set up `pre-commit` in your copy of this project. In the project directory, run:
    ```bash
    pre-commit install
    ```

Rules that are applied can be found in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

The hooks run automatically on commit, or manually with `pre-commit run --all-files`.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
