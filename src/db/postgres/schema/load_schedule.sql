CREATE TABLE IF NOT EXISTS load_schedule (
    gameID TEXT PRIMARY KEY,
    awayTeamID TEXT NOT NULL,
    awayTeamCity TEXT NOT NULL,
    awayTeamName TEXT NOT NULL,
    awayTeamNameRaw TEXT NOT NULL,
    awayScore INT NOT NULL,
    homeTeamID TEXT NOT NULL,
    homeTeamCity TEXT NOT NULL,
    homeTeamName TEXT NOT NULL,
    homeTeamNameRaw TEXT NOT NULL,
    homeScore INT NOT NULL,
    status TEXT NOT NULL,
    week TEXT NOT NULL,
    streamingURL TEXT NOT NULL,
    ticketURL TEXT,
    hasRosterReport BOOLEAN NOT NULL,
    locationName TEXT,
    locationURL TEXT,
    startTimestamp TIMESTAMP,
    startTimezone TEXT,
    startTimeTBD BOOLEAN NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create an index on startTimestamp and gameID
--  CREATE INDEX IF NOT EXISTS gameID ON schedule (gameID);
    --  ON schedule (startTimestamp, gameID);
