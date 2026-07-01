CREATE TABLE IF NOT EXISTS players (
    ext_player_id TEXT PRIMARY KEY,
    name TEXT,
    team_position TEXT,
    jersey_number TEXT,
    height TEXT,
    weight FLOAT,
    dob TEXT,
    college TEXT,
    hometown TEXT,
    bio TEXT
    --  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
)
