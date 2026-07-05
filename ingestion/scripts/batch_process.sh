#!/bin/bash

# Season and format must match what extract_weekly wrote to the data lake.
YEAR="${1:-2026}"
FMT="${2:-json}"

# 1. Select gameIDs the same way src/extract_weekly.py does: filter on the date
#    prefix parsed from the gameID (local scheduled date), NOT startTimestamp (a UTC
#    instant, which shifts evening games to the next day and drops the last day).
GAME_IDS=$(YEAR="$YEAR" FMT="$FMT" uv run python -c '
import os
from datetime import date, timedelta

from pipeline_utils import data_suffix, game_date, read_table, source_dir

year = int(os.environ["YEAR"])
fmt = os.environ["FMT"]

today = date.today()
start_date = (today - timedelta(days=14)).isoformat()
end_date = (today - timedelta(days=1)).isoformat()

games_file = source_dir() / "games" / f"season={year}" / f"games{data_suffix(fmt)}"
games = read_table(games_file)

selected = [g["gameID"] for g in games if start_date <= game_date(g["gameID"]) <= end_date]
print(" ".join(selected))
')

# 2. Check if we actually got any IDs back
if [ -z "$GAME_IDS" ]; then
    echo "No games found matching the date criteria."
    exit 0
fi

# 3. Loop through the outputted IDs and execute the uv command
N=8
for game_id in $GAME_IDS; do
    ((i=i%N)); ((i++==0))
    echo "Processing gameID: $game_id"
    uv run audl-pipeline $game_id --source-dir $AUDL_SOURCE_DIR --processed-dir $AUDL_PROCESSED_DIR --format "$FMT"
done

