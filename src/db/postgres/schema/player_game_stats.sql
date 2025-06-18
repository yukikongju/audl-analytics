CREATE TABLE IF NOT EXISTS player_game_stats (
    player_ext_id TEXT PRIMARY KEY,
    gameID TEXT,
    scoreHome INT,
    scoreAway INT,
    assists INT,
    goals INT,
    hockeyAssists INT,
    completions INT,
    throwaways INT,
    stalls INT,
    throwsAttempted INT,
    catches INT,
    drops INT,
    blocks INT,
    callahans INT,
    pulls INT,
    obPulls INT,
    recordedPulls INT,
    recordedPullsHangtime INT,
    oPointsPlayed INT, 
    oPointsScored INT,
    dPointsPlayed INT,
    dPointsScored INT,
    secondsPlayed INT,
    yardsReceived INT,
    yardsThrown INT,
    hucksCompleted INT,
    hucksAttempted INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create an index on startTimestamp and gameID
--  CREATE INDEX IF NOT EXISTS gameID ON schedule (gameID);
--      ON schedule (startTimestamp, gameID);
