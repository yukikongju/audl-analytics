# AUDL Analytics

Code for to ingest AUDL data. The goal of this project is to create a 
pipeline that can be reproduced locally by others so that they can 
explore AUDL analytics on their own

## Setup

**Step 1: Defining the environment variables**

We will create `.env` and `.envrc` files to define where downloaded files and duckdb tables will reside

```
# .env
AUDL_EXTRACTION_DIR="${HOME}/.Data/ufa/extraction/"     # where raw data gets stored
AUDL_PROCESSED_DIR="${HOME}/.Data/ufa/processed/"       # where raw data gets transformed into 5 tables
AUDL_ANALYTICS_DIR="${HOME}/.Data/ufa/analytics/"       # where duckdb files will live
```

```
# .envrc
dotenv .env
```

To load your variables everytime you go into this repo:
1. In your `~/.zshrc`, add this line `eval "$(direnv hook zsh)"`
2. In `audl-analytics`, run `direnv allow`. This will automatically load the environment variables you have defined in `.envrc`.

## Entity-Relationship Diagram

The ER diagram can be found in the folder `diagrams/` and can be open 
using [drawio](https://www.drawio.com/)

## Technologies Used

* Ingestion: `Python`
* Transformation: `dbt`, `duckdb`
* Orchestration: `crontab -e`
* API: `FastAPI`
* Website: `javascript`, `html`, `css`, `ngrok`, `cloudflare`

