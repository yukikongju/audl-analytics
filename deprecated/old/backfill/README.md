# Backfill

Here are the following job we need to backfill
- [X] Populating Postgres "schedule" once every beginning of the season
    * `python3 -m src.extract.extract_season_schedule --year 2025`
- [X] Updating list of players external id for dbt/seeds
    * `python3 -m src.extract.extract_ext_player_ids`
- [ ] Populating Postgres "players" table (player profile) every season
    * TBD
- [TODO] Populating MongoDB "game-events" collection within time range
    * 


