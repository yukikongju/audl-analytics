
# activate virtual environment
python3 -m venv venv
source venv/bin/activate

# download python libraries
pip3 install -r requirements.txt

# create volumes
mkdir data/postgres

# install
brew install mongosh 

# note: very important to NOT install dbt as it is deprecated

# 
docker-compose up

# --- initialize tables
# python3 -m src.db.init.mongodb.init_collections
# python3 -m src.db.postgres.init_tables --sql_path=dbt/models/load/load_game_metadata.sql --table_name=load_game_metadata
# python3 -m src.db.postgres.init_tables --sql_path=dbt/models/load/load_game_rosters.sql --table_name=load_game_rosters
# python3 -m src.db.postgres.init_tables --sql_path=dbt/models/load/load_game_tsg.sql --table_name=load_game_tsg
# python3 -m src.db.postgres.init_tables --sql_path=src/db/postgres/schema/player_game_stats.sql --table_name=player_game_stats

# --- backfill
# python3 -m src.load.load_game_events_table --ext_game_id "2024-08-24-CAR-MIN"

