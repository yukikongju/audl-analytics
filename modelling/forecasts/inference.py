import duckdb
import joblib
import os
import pandas as pd

from utils import duckdb_query
from queries import QUERY_REGISTRY

## 0. Configurations
query_name = "player_game_stats"
model_type = "xgb"
feature_type = "lag"
#  model_base_path = f"{query_name}_{model_type}_{feature_type}.joblib"
model_base_path = "player_stats_xgb.joblib"
model_dir = os.getenv("AUDL_MODELS_DIR")
duckdb_dir = os.getenv("AUDL_ANALYTICS_DIR")
duckdb_path = os.path.join(duckdb_dir, "dev.duckdb")
model_path = os.path.join(model_dir, model_base_path)
table_name = f"counterfactuals_{query_name}_{model_type}_{feature_type}"


CONDITION_COLS = [
    "o_points_played",
    "d_points_played",
]
CAT_COLS = ["ext_player_id", "ext_team_id", "opponent_ext_team_id"]
TARGET_COLS = [
    "assists",
    "goals",
    "hockey_assists",
    "completions",
    "throwaways",
    "stalls",
    "throws_attempted",
    "catches",
    "drops",
    "blocks",
    "callahans",
    # note: for pulls, condition only on pullers
    #  "pulls",
    #  "ob_pulls",
    #  "recorded_pulls",
    #  "recorded_pulls_hangtime",
    "o_points_played",
    "d_points_played",
    #  "o_points_scored",
    #  "d_points_scored",
    #  "seconds_played",
    "yards_received",
    "yards_thrown",
    "hucks_completed",
    "hucks_attempted",
    "pass_completed",
    "pass_attempted",
    "dump_completed",
    "dump_attempted",
    "swing_completed",
    "swing_attempted" 
]


## 1. Load the data
con = duckdb.connect(duckdb_path, read_only=True)
df = duckdb_query(con, QUERY_REGISTRY[query_name])
con.close()

## 2. Load the model
model = joblib.load(model_path)
#  model.verbose = True
model_features = model.feature_names_in_
print(f"[INFO] Model Features: {model_features}")

## 3. Make Inference on counterfactual
df_counterfactuals = df[model_features].drop(columns=CONDITION_COLS)
df_counterfactuals[CAT_COLS] = df_counterfactuals[CAT_COLS].astype('category')
max_o_points_played, max_d_points_played = df['o_points_played'].max().item(), df['d_points_played'].max().item()

points_grid = pd.MultiIndex.from_product(
    [range(max_o_points_played + 1), range(max_d_points_played + 1)],
    names=['o_points_played', 'd_points_played']
).to_frame(index=False)
df_counterfactuals = df_counterfactuals.merge(points_grid, how='cross')
df_counterfactuals = df_counterfactuals[model_features]

# FIXME inference with pyspark for faster execution?
preds = model.predict(df_counterfactuals)
df_preds = pd.DataFrame(preds, columns=TARGET_COLS)

df_complete = pd.concat([df[model_features].drop(columns=CONDITION_COLS), df_preds], axis=1)

## 4. Store results in duckdb
con = duckdb.connect(duckdb_path, read_only=False)
try:
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_complete")
    print(f"[INFO] Successfully wrote 'counterfactual_predictions' to DuckDB.")
except Exception as e:
    raise RuntimeError(f"[ERROR] Failed to write dataframe to DuckDB: {e}") from e
finally:
    con.close()



