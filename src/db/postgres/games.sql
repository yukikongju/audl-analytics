CREATE TABLE IF NOT EXISTS games (
    gameID TEXT NOT NULL PRIMARY KEY,
    awayTeamID TEXT NOT NULL,
    awayTeamCity TEXT NOT NULL,
    awayTeamName TEXT NOT NULL,
    awayTeamNameRaw TEXT NOT NULL,
    homeTeamID TEXT NOT NULL,
    homeTeamCity TEXT NOT NULL,
    homeTeamName TEXT NOT NULL,
    homeTeamNameRaw TEXT NOT NULL,
    status TEXT NOT NULL,
    week TEXT NOT NULL,
    ticketURL TEXT,
    hasRosterReport BOOLEAN NOT NULL,
    locationName TEXT,
    locationURL TEXT,
    startTimestamp TIMESTAMP,
    startTimezone TEXT,
    startTimeTBD BOOLEAN NOT NULL
);
