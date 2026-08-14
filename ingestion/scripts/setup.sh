#!/bin/bash

# Local Setup on remote computer
# Usage: ./setup.sh

### ==== LOGGING FUNCTIONS ====
log_info() { echo -e "\033[1;34m[INFO]\033[0m $(date '+%H:%M:%S') | $1"; }
log_skip() { echo -e "\033[1;33m[SKIP]\033[0m $(date '+%H:%M:%S') | $1"; }
log_success() { echo -e "\033[1;32m[DONE]\033[0m $(date '+%H:%M:%S') | $1"; }
log_header() { echo -e "\n\033[1;35m==== $1 ====\033[0m\n"; }

### ==== Define Variables ====
FIRST_ANALYTICS_SEASON=2020
EXTRACTION_DIR="${HOME}/.Data/ufa/extraction/" # stores raw json files
PROCESSED_DIR="${HOME}/.Data/ufa/processed/"   # process raw json files into ext_
ANALYTICS_DIR="${HOME}/.Data/ufa/analytics/"   # store duckdb
BASE_DIR="${HOME}/temp"                        # directory with audl-analytics repo
CURRENT_YEAR=$(date +%Y)
PROCESSESSING_FORMAT="json"

mkdir -p "${EXTRACTION_DIR}" "${PROCESSED_DIR}" "${ANALYTICS_DIR}" "${BASE_DIR}"

## Clone repo if doesn't exists
# if [ -d "${BASE_DIR}/audl-analytics" ]; then
    # cd "${BASE_DIR}/audl-analytics"
# else
    # cd "${BASE_DIR}"
    # git clone https://github.com/yukikongju/audl-analytics.git
    # cd audl-analytics/
# fi


### ==== BACKFILL THE DATA ====
# IMPORTANT: The `curl` command returns all json data into a single line to save bandwidth and leaves the raw API {"object": "list", "data": [<...>]} envelope. On the other hand, Python strips this enveloppe, so fetching the data from Python already unpack whatever is in data. Thus, we need to use the command `jq` to remove this enveloppe if we fetch using curl in order to match Python.
# all curls need to have the jq because they have this enveloppe, EXCEPT `stats-pages/game` for some reasons

NUM_SEASONS=$(( CURRENT_YEAR - FIRST_ANALYTICS_SEASON + 1 ))
N=8
for (( year = FIRST_ANALYTICS_SEASON; year <= CURRENT_YEAR; year++ ));
do
    log_header "Season ${year}"

    echo -e "----------------------------------------"
    log_info "SEASON DATA EXTRACTION: team, game, schedule"
    echo -e "----------------------------------------"
    schedule_file_path="${EXTRACTION_DIR}/games/season=${year}/games.json"
    if [ -f "${schedule_file_path}" ]; then
        log_skip "${year} season schedule already exists, skipping."
    else
        log_info "Extracting ${year} season schedule..."
        mkdir -p "${EXTRACTION_DIR}/games/season=${year}/"
        curl -s "https://www.backend.ufastats.com/api/v1/games?date=${year}" | jq '.data' > "${schedule_file_path}"
    fi

    player_file_path="${EXTRACTION_DIR}/players/season=${year}/players.json"
    if [ -f "${player_file_path}" ]; then
        log_skip "${year} player data already exists, skipping."
    else
        log_info "Extracting ${year} player data..."
        mkdir -p "${EXTRACTION_DIR}/players/season=${year}/"
        curl -s "https://www.backend.ufastats.com/api/v1/players?years=${year}" | jq '.data'> "${player_file_path}"
    fi

    team_file_path="${EXTRACTION_DIR}/teams/season=${year}/teams.json"
    if [ -f "${team_file_path}" ]; then
        log_skip "${year} team data already exists, skipping."
    else
        log_info "Extracting ${year} team data..."
        mkdir -p "${EXTRACTION_DIR}/teams/season=${year}/"
        curl -s "https://www.backend.ufastats.com/api/v1/teams?years=${year}" | jq '.data'> "${team_file_path}"
    fi

    echo -e "----------------------------------------"
    log_info "FETCHING GAME IDS"
    echo -e "----------------------------------------"
    game_ids=$(uv run python -c '
import pandas as pd
import sys
import requests
from datetime import datetime, timezone

SEASON = sys.argv[1]
LAST_BACKFILLED_DATE = sys.argv[2]

if not LAST_BACKFILLED_DATE:
    LAST_BACKFILLED_DATE = f"{SEASON}-01-01"

game_url = f"https://www.backend.ufastats.com/api/v1/games?date={SEASON}"
res = requests.get(game_url)

if res.status_code != 200:
    sys.exit(1)

data = res.json().get("data", [])
df = pd.DataFrame(data)
if df.empty:
    sys.exit(1)

df["startTimestamp"] = pd.to_datetime(df["startTimestamp"], utc=True)
today = pd.to_datetime(datetime.now(timezone.utc).date(), utc=True)
has_been_played_mask = df["status"] == "Final"
date_mask = (df["startTimestamp"] > pd.to_datetime(LAST_BACKFILLED_DATE, utc=True)) & (df["startTimestamp"] < today)
game_ids = list(df[has_been_played_mask & date_mask]["gameID"])
game_ids.sort()

print(" ".join(game_ids))
    ' "${year}" "")
    
    num_games=$(echo "${game_ids}" | wc -w | xargs)
    
    if [ "${num_games}" -eq 0 ]; then
        log_skip "No completed games found to backfill for ${year}."
        continue
    fi

    log_success "Found ${num_games} games to process for ${year}."

    echo -e "----------------------------------------"
    log_info "GAME STATS EXTRACTION"
    echo -e "----------------------------------------"
    i=0
    for game_id in ${game_ids}; do
        # note: we lock the current i and game_id to prevent the shell from grabbing the wrong values (because we are processing in parallel)
        curr_i=$i
        curr_game_id=$game_id

        (
            month="${curr_game_id:5:2}"
            
            player_game_stats_dir="${EXTRACTION_DIR}/player_game_stats/season=${year}/month=${month}"
            game_events_dir="${EXTRACTION_DIR}/game_events/season=${year}/month=${month}"
            game_stats_page_dir="${EXTRACTION_DIR}/game_stats/season=${year}/month=${month}"

            player_game_stats_file="${player_game_stats_dir}/${curr_game_id}.json"
            game_events_file="${game_events_dir}/${curr_game_id}.json"
            game_stats_page_file="${game_stats_page_dir}/${curr_game_id}.json"

            if [ -f "${player_game_stats_file}" ] && [ -f "${game_events_file}" ] && [ -f "${game_stats_page_file}" ]; then
                log_skip "[${curr_i}/${num_games}] ${curr_game_id} (Already exists)"
            else
                log_info "[${curr_i}/${num_games}] Downloading ${curr_game_id}..."
                
                mkdir -p "${player_game_stats_dir}" "${game_events_dir}" "${game_stats_page_dir}"
                
                [ ! -f "${player_game_stats_file}" ] && curl -s "https://www.backend.ufastats.com/api/v1/playerGameStats?gameID=${curr_game_id}" | jq '.data' > "${player_game_stats_file}"
                [ ! -f "${game_events_file}" ] && curl -s "https://www.backend.ufastats.com/api/v1/gameEvents?gameID=${curr_game_id}" | jq '.data' > "${game_events_file}"
                [ ! -f "${game_stats_page_file}" ] && curl -s "https://www.backend.ufastats.com/stats-pages/game/${curr_game_id}" > "${game_stats_page_file}"
                
                log_success "[${curr_i}/${num_games}] ${curr_game_id} (Downloaded successfully)"
            fi
        ) & 
        
        # wait for the batch to finish before continuing
        if (( i % N == 0 )); then
            wait
        fi
        i=$((i + 1))
    done
    wait

    echo -e "----------------------------------------"
    log_info "PROCESSING GAMES STATS"
    echo -e "----------------------------------------"
    i=0
    for game_id in ${game_ids}; do
        curr_i=$i
        curr_game_id=$game_id

        (
            month="${curr_game_id:5:2}"
            ext_blocks_file_path="${PROCESSED_DIR}/ext_blocks/season=${year}/month=${month}/${game_id}.${PROCESSESSING_FORMAT}"
            ext_games_file_path="${PROCESSED_DIR}/ext_games/season=${year}/month=${month}/${game_id}.${PROCESSESSING_FORMAT}"
            ext_point_lineups_file_path="${PROCESSED_DIR}/ext_point_lineups/season=${year}/month=${month}/${game_id}.${PROCESSESSING_FORMAT}"
            ext_pulls_file_path="${PROCESSED_DIR}/ext_pulls/season=${year}/month=${month}/${game_id}.${PROCESSESSING_FORMAT}"
            ext_throws_file_path="${PROCESSED_DIR}/ext_throws/season=${year}/month=${month}/${game_id}.${PROCESSESSING_FORMAT}"


            if [ -f "${ext_blocks_file_path}" ] && [ -f "${ext_games_file_path}" ] && [ -f "${ext_point_lineups_file_path}" ] && [ -f "${ext_pulls_file_path}" ] && [ -f "${ext_throws_file_path}" ]; then
                log_skip "[${curr_i}/${num_games}] ${curr_game_id} (Already processed)"
            else
                log_info "[${curr_i}/${num_games}] Processing ${curr_game_id}..."
                uv run audl-pipeline ${curr_game_id} --source-dir ${EXTRACTION_DIR} --processed-dir ${PROCESSED_DIR} --format "${PROCESSESSING_FORMAT}"
                log_success "[${curr_i}/${num_games}] ${curr_game_id} (Downloaded successfully)"
            fi
        ) & 
        
        if (( i % N == 0 )); then
            wait
        fi
        i=$((i + 1))
    done
    wait
done
