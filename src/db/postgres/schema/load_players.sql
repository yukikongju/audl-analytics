CREATE TABLE IF NOT EXISTS load_players (
    ext_player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    jersey_number TEXT,
    height TEXT,
    weight FLOAT,
    dob TEXT,
    college TEXT,
    hometown TEXT,
    bio TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
)
