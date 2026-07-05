#!/bin/bash

# 1. Use Python to parse the JSON and output the filtered gameIDs as a space-separated string
GAME_IDS=$(uv run python -c '
import pandas as pd
import os

# Get environment variable safely
base_dir = os.environ.get("AUDL_SOURCE_DIR", "")
game_path = os.path.join(base_dir, "games/season=2026/games.json")

# Load and filter
df = pd.read_json(game_path)
df["startTimestamp"] = pd.to_datetime(df["startTimestamp"], utc=True)

today = pd.Timestamp.utcnow().normalize()
start_date = today - pd.Timedelta(weeks=2)
end_date = today - pd.Timedelta(days=1)

date_mask = (df["startTimestamp"] >= start_date) & (df["startTimestamp"] <= end_date)
dff = df[date_mask]

# Print the gameIDs separated by a space so Bash can loop over them easily
print(" ".join(dff["gameID"].astype(str).tolist()))
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
    # uv run audl-pipeline $game_id --source-dir $AUDL_SOURCE_DIR --processed-dir $AUDL_PROCESSED_DIR 
    uv run audl-pipeline $game_id --source-dir $AUDL_SOURCE_DIR --processed-dir $AUDL_PROCESSED_DIR --format json
done

