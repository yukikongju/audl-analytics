
# activate virtual environment
python3 -m venv venv
source venv/bin/activate

# download python libraries
pip3 install -r requirements.txt

# create volumes
mkdir data/postgres

# install
brew install mongosh

# 
docker-compose up

# initialize tables
# python3 -m src.db.init.mongodb.init_collections
# python3 -m src.db.init.postgres.init_tables
# python3 -m src.db.postgres.init_tables --sql_path=src/db/postgres/schema/game_metadata.sql --table_name=game_metadata
# python3 -m src.db.postgres.init_tables --sql_path=src/db/postgres/schema/game_rosters.sql --table_name=game_rosters
# python3 -m src.db.postgres.init_tables --sql_path=src/db/postgres/schema/game_tsg.sql --table_name=game_tsg


