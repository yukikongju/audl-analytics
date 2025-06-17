CREATE TABLE IF NOT EXISTS load_game_rosters (
    id INT PRIMARY KEY,
    team_season_id INT,
    player_id INT,
    jersey_number INT,
    active BOOLEAN,
    --  player_id INT,
    player_first_name TEXT,
    player_last_name TEXT,
    player_ext_player_id TEXT,
    player_ls_player_id TEXT
);
