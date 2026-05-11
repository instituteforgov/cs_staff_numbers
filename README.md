# Template repo - Python

Add a short (1–5-line) description of the repo here.

E.g.

> A template that can be used for creating repos for Python projects  
>  
> This README sets out a structure that should be used in READMEs. Optional sections in this README template are marked **[optional]** - sometimes with notes on when these may apply. Note that this is a minimal template - other sections should be added where they are of use. Examples are marked using blockquotes (`>`) - remove these when replicating the examples

## Related repositories

Add a link to related repos where the code relies on code or data stemming from another repo, indicating whether the repo is public 🔓 or private 🔒.

E.g.

> - 🔒 [IfG Ministers Database - private repo](https://github.com/instituteforgov/ifg-ministers-database-private/): Holds the majority of code and resources for the IfG Ministers Database project  
>  
>    In several places, identifiers used in this repo have been aligned with those used in the IfG Ministers Database - described in further detail below  
>  
> - 🔓 [IfG Ministers Database - public repo](https://github.com/instituteforgov/ifg-ministers-database-public/): Holds the public element of the IfG Ministers Database project
> - 🔓 [GOV.UK organisations](https://github.com/instituteforgov/govuk_organisations) Experimental work to see whether it's possible to track organisational histories using organisations data from the GOV.UK API

## Project structure [optional]

Add a diagram showing the project structure.

E.g.
> ```
> ├── csps_extraction/
> │   ├── sql/
> │   │   ├── compare_organisations_data.sql
> │   │   ├── select_organisations_data.sql
> │   ├── compare_data.py
> │   ├── extract_existing_data.py
> │   └── utils.py
> ├── .gitignore
> ├── .pre-commit-config.yaml
> ├── LICENSE
> ├── README.md
> └── requirements.txt
> ```

## Installation [optional - where applicable]

Where the repo contains a `requirements.txt` file, include the commands to install dependencies using it.

E.g.

> ```bash
> pip install -r requirements.txt
> ```


## Scripts

Add details of the substantive scripts in the repo with a brief description, in run order where the order is important.

E.g.

> | File | Description |
> | ---- | ----------- |
> | `csps_extraction/extract_existing_data.py` | Reads existing CSPS data and saves to database. |
> | `csps_extraction/sql/compare_organisations_data.sql` | Replicates the collated organisations data from the CSPS working file, to be used as the basis for comparison in `compare_data.py`. |
> | `csps_extraction/compare_data.py` | Validates that the augmented SQL output matches the source Excel file. |
> | `csps_extraction/sql/select_organisations_data.sql` | Script to be used for (re-)insertion of augmented data into Excel. Duplicates `compare_organisations_data.sql`, with the following differences to columns: <ul><li><strong>Organisation type</strong>: Simplified (things of type 'Aggregation'/'Disaggregation'/'Reporting total' reported as such, rather than being reported as 'Combination')</li><li><strong>Organisation aggregation?</strong>: Removed</li><li><strong>IfG core department</strong>: Added</li><li><strong>Latest organisation</strong>: Latest actual organisation always reported, rather than latest determinate organisation</li><li><strong>Latest departmental group</strong>: Latest actual (IfG) departmental group always reported, rather than latest determinate organisation</li></ul> |

## Environment variables [optional - where applicable]

Add details of environment variables here, where the code makes use of any of.

E.g.

> The scripts require the following environment variables to be set:
> 
> | Variable | Description |
> | -------- | ----------- |
> | `ODBC_DRIVER` | ODBC driver version for SQL Server (e.g., `ODBC Driver 18 for SQL Server`) |
> | `ODBC_SERVER` | SQL Server hostname |
> | `ODBC_DATABASE` | Database name |
> | `ODBC_AUTHENTICATION` | Authentication method (e.g., `ActiveDirectoryServicePrincipal`) |
> | `AZURE_CLIENT_ID` | Azure service principal client ID used for database authentication |
> | `AZURE_CLIENT_SECRET` | Azure service principal client secret used for database authentication |


## Contributing [optional - repos likely to have multiple contributors]

Add a section describing any important information for contributors.

E.g.

> This project uses `pre-commit` hooks to ensure code quality. To set up:
> 
> 1. Install `pre-commit` on your system if you don't already have it:
> 
    > ```bash
    > pip install pre-commit
    > ```
> 
> 1. Set up `pre-commit` in your copy of this project. In the project directory, run:
    > ```bash
    > pre-commit install
    > ```
> 
> Rules that are applied can be found in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
> 
> The hooks run automatically on commit, or manually with `pre-commit run --all-files`.

## License [optional - public repos only]

Add details of the license if the project is public.

E.g.

> This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
