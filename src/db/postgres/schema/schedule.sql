CREATE TABLE IF NOT EXISTS schedule (
    gameID TEXT PRIMARY KEY,
    awayTeamID TEXT,
    awayTeamCity TEXT,
    awayTeamName TEXT,
    awayTeamNameRaw TEXT,
    awayScore INT,
    homeTeamID TEXT,
    homeTeamCity TEXT,
    homeTeamName TEXT,
    homeTeamNameRaw TEXT,
    homeScore INT,
    status TEXT,
    week TEXT,
    streamingURL TEXT,
    ticketURL TEXT,
    hasRosterReport BOOLEAN,
    locationName TEXT,
    locationURL TEXT,
    startTimestamp TEXT,
    startTimezone TEXT,
    startTimeTBD BOOLEAN
    --  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create an index on startTimestamp and gameID
--  CREATE INDEX IF NOT EXISTS gameID ON schedule (gameID);
    --  ON schedule (startTimestamp, gameID);
