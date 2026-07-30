#!/bin/bash

# Usage: ./script.sh

BUCKET_NAME="ds-ufa-backups"
SEASON=$(date +%Y)

## find last data backfilled from bucket
LAST_DATE=$(gcloud storage ls "gs://${BUCKET_NAME}/season=${SEASON}/" 2>/dev/null | sort | tail -n 1 | awk -F'=' '{print $NF}' | tr -d '/')
# LAST_DATE="2026-07-20"

## find all games to fetch
GAME_IDS=$(uv run python -c '
import pandas as pd
import os
import sys
import requests
from datetime import datetime, timezone

# 1. Read parameters from sys.argv
# sys.argv[0] is always "-c" for inline scripts
# sys.argv[1] is the first parameter ($SEASON)
# sys.argv[2] is the second parameter ($LAST_DATE)
SEASON = sys.argv[1]
LAST_BACKFILLED_DATE = sys.argv[2]

# 2. Handle the edge case where the bucket is empty (LAST_DATE was empty in bash)
if not LAST_BACKFILLED_DATE:
    LAST_BACKFILLED_DATE = f"{SEASON}-01-01"

game_url = f"https://www.backend.ufastats.com/api/v1/games?date={SEASON}"
res = requests.get(game_url)

# check if request was succesfull
if res.status_code != 200:
    os.exit(1)

# check if there are games
data = res.json()["data"]
df = pd.DataFrame(data)
if df.empty:
    os.exit(1)

# data prep
df["startTimestamp"] = pd.to_datetime(df["startTimestamp"], utc=True)

# find games that have been played and not in bucket
today = pd.to_datetime(datetime.now(timezone.utc).date(), utc=True)
has_been_played_mask = df["status"] == "Final"
date_mask = (df["startTimestamp"] > pd.to_datetime(LAST_BACKFILLED_DATE, utc=True)) & (df["startTimestamp"] < today)
game_ids = list(df[has_been_played_mask & date_mask]["gameID"])
game_ids.sort()

# Print the gameIDs separated by a space so Bash can loop over them easily
print(" ".join(game_ids))
' "$SEASON" "$LAST_DATE")

NUM_GAMES=$(echo "$GAME_IDS" | wc -w | xargs)
echo "${GAME_IDS}"
echo "Processing for season ${SEASON} backfilled from ${LAST_DATE}"
echo "Total games to fetch: ${NUM_GAMES}"

if [ "$NUM_GAMES" -eq 0 ]; then
    echo "No new games found. Exiting."
    exit 0
fi


N=8
for GAME_ID in $GAME_IDS; do
    ((i=i%N)); ((i++==0))
    DATE="${GAME_ID:0:10}"        # 2026-05-10
    SEASON="${DATE:0:4}"          # 2026
    BASE_PATH="gs://${BUCKET_NAME}/season=${SEASON}/date=${DATE}/game_id=${GAME_ID}"
    
    echo "Processing GameID: ${GAME_ID} to ${BASE_PATH} [${i}/${NUM_GAMES}]"

    # 1) playerGameStats -> player_game_stats.json
    curl -s "https://www.backend.ufastats.com/api/v1/playerGameStats?gameID=${GAME_ID}" | gcloud storage cp - "${BASE_PATH}/player_game_stats.json" > /dev/null 2>&1

    # 2) gameEvents -> game_events.json
    curl -s "https://www.backend.ufastats.com/api/v1/gameEvents?gameID=${GAME_ID}" | gcloud storage cp - "${BASE_PATH}/game_events.json" > /dev/null 2>&1

    # 3) stats page (HTML) -> game_stats_page.json
    curl -s "https://www.backend.ufastats.com/stats-pages/game/${GAME_ID}" | gcloud storage cp - "${BASE_PATH}/game_stats_page.json" > /dev/null 2>&1
done

echo "Completed!"

