"""Player game-stats forecasting pipeline.

End-to-end training script: loads a feature dataset from DuckDB, performs a
chronological train/test split, selects the lag or rolling feature family,
runs an Optuna TPE hyperparameter search, trains a MultiOutput regressor, saves
the fitted model as a joblib artifact, and writes a predictions table back to
DuckDB.

All run configuration is supplied via required CLI arguments (no defaults).

Current invocation:

    uv run main.py \\
        --model_type xgb \\
        --db_path "$AUDL_ANALYTICS_DIR/dev.duckdb" \\
        --models_dir "$AUDL_MODELS_DIR" \\
        --query_name player_game_stats \\
        --feature_type lag \\
        --scoring_type neg_root_mean_squared_error \\
        --train_size 0.8 \\
        --n_splits 5 \\
        --n_trials 5
"""

from os.path import isfile

import argparse
import duckdb
import joblib
import lightgbm as lgbm
import os
import pandas as pd
import xgboost as xgb


#  from pydantic import ValidationError
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

from objectives import OBJECTIVE_REGISTRY, run_bayesian
from queries import QUERY_REGISTRY
from schemas import Scoring, ModelFeatures


### 0. Config Parser
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--model_type", type=str, required=True, help="model to train: `xgb`, `lgbm`, or `random_forest`")
parser.add_argument("--db_path", type=str, required=True, help="path to the DuckDB analytics database (`*.duckdb`)")
parser.add_argument("--models_dir", type=str, required=True, help="directory where trained model artifacts are written")
parser.add_argument("--query_name", type=str, required=True, help="dataset query key from QUERY_REGISTRY")
parser.add_argument("--feature_type", type=str, required=True, help="feature family to train on: `lag` or `rolling`")
parser.add_argument("--scoring_type", type=str, required=True, help="sklearn scoring metric, e.g. `neg_root_mean_squared_error`")
parser.add_argument("--train_size", type=float, required=True, help="fraction of chronological data used for training")
parser.add_argument("--n_splits", type=int, required=True, help="number of KFold CV splits")
parser.add_argument("--n_trials", type=int, required=True, help="number of Optuna TPE search trials")
#  parser.add_argument("--enforce_monotonicity", action="store_true", help="TODO")
args = parser.parse_args()

model_type = args.model_type
db_path = args.db_path
models_dir = args.models_dir
query_name = args.query_name
feature_type = args.feature_type
scoring_type = args.scoring_type
train_size = args.train_size
n_splits = args.n_splits
n_trials = args.n_trials

table_name = f"{query_name}_{model_type}_{feature_type}_predictions"
model_base_path = f"{query_name}_{model_type}_{feature_type}.joblib"

SEED = 42
KEY_COLS = [
    "season",
    "game_date",
    "ext_game_id",
    "team_id",
    "opponent_team_id",
    "ext_team_id",
    "opponent_ext_team_id",
    "ext_player_id",
]
CONDITION_COLS = [
    "o_points_played",
    "d_points_played",
]
DROP_KEY_COLS = [
    "game_date",
    "ext_game_id",
    "team_id",
    "opponent_team_id",
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

### 0. Configs Verification
Scoring(type=scoring_type)
ModelFeatures(type=feature_type)
if query_name not in QUERY_REGISTRY:
    raise KeyError(f"`{query_name}` is not defined. Options: {QUERY_REGISTRY.keys()}")
#  path = Path(db_path)
if not os.path.isfile(db_path) or not db_path.endswith(".duckdb"):
    raise FileNotFoundError(f"File `{db_path}` is not a valid duckdb file")


### 1. Load Data
con = duckdb.connect(db_path, read_only=True)
try:
    df = con.execute(QUERY_REGISTRY[query_name]).df()
except Exception as e:
    raise RuntimeError(f"query '{query_name}' failed: {e}") from e
finally:
    con.close()


### 2. Split into train/val/test dataset

## 
df[CAT_COLS] = df[CAT_COLS].astype('category')
#  df = df.sort_values(by=["ext_player_id", "game_date"])
#  group_row_number = df.groupby(["ext_player_id"]).cumcount()
#  group_size = df.groupby(["ext_player_id"])["ext_player_id"].transform('size')
#  is_train = group_row_number < (group_size * train_size)
#  df_train = df[is_train]
#  df_test = df[~is_train]

# Split chronologically
df = df.sort_values(by=["game_date"])
split_idx = int(len(df) * train_size)

df_train = df.iloc[:split_idx]
df_test = df.iloc[split_idx:]

print(f"[INFO] Train Dataset Size: {len(df_train):,} ; Test Dataset Size: {len(df_test):,}")

### 3. Feature Engineering
candidate_cols = [metric for metric in df.columns if any(prefix in metric for prefix in TARGET_COLS)]
metric_cols = [metric for metric in candidate_cols if feature_type in metric]
feature_cols = [c for c in KEY_COLS if c not in DROP_KEY_COLS] + CONDITION_COLS + metric_cols

#  print(f"[INFO] Feature Columns: {feature_cols}")


X_train = df_train[feature_cols].copy()
X_test = df_test[feature_cols].copy()
for X in (X_train, X_test):
    # game_date is a split key we keep as a feature; XGBoost needs it numeric
    #  X["game_date"] = pd.to_datetime(X["game_date"]).astype("int64") // 86_400_000_000_000  # ns -> days
    X[metric_cols] = X[metric_cols].fillna(0.0)
y_train = df_train[TARGET_COLS].fillna(0.0)
y_test = df_test[TARGET_COLS].fillna(0.0)

### 4. Models Training
cv = KFold(n_splits=n_splits, shuffle=True, random_state=SEED)
objective = OBJECTIVE_REGISTRY[model_type]
print(f"[INFO] Running Bayesian TPE hyperparameters search")
model_study = run_bayesian(objective, model_type, X_train, y_train, cv, scoring_type, n_trials=n_trials)

print(f"[INFO] Training the model")
if model_type == "lgbm":
    base_model = lgbm.LGBMRegressor(**model_study.best_params, objective='regression', verbosity=-1, random_state=42)
    model = MultiOutputRegressor(base_model)
elif model_type == "xgb":
    base_model = xgb.XGBRegressor(**model_study.best_params, objective='reg:squarederror', tree_method='hist', enable_categorical=True, random_state=42)
    model = MultiOutputRegressor(base_model)
elif model_type == "random_forest": # or whatever your string alias is
    # Random Forest natively supports multi-output, so it becomes 'model' directly
    model = RandomForestRegressor(**model_study.best_params, random_state=42)
model.fit(X_train, y_train)

# save model
os.makedirs(models_dir, exist_ok=True)
model_path = os.path.join(models_dir, model_base_path)
joblib.dump(model, model_path)
print(f"[INFO] Model saved to {model_path}")

### 5. Models Evaluation
preds_train = model.predict(X_train)
preds_test = model.predict(X_test)

df_preds_train = df_train[KEY_COLS].copy()
df_preds_test = df_test[KEY_COLS].copy()

for i, col in enumerate(TARGET_COLS):
    df_preds_train[f"pred_{col}"] = preds_train[:, i]
    df_preds_train[f"actual_{col}"] = y_train[col].values
    
    df_preds_test[f"pred_{col}"] = preds_test[:, i]
    df_preds_test[f"actual_{col}"] = y_test[col].values

df_preds_train['split'] = 'train'
df_preds_test['split'] = 'test'

df_predictions = pd.concat([df_preds_train, df_preds_test], ignore_index=True)
df_predictions['model_type'] = model_type

# save to duckdb
con = duckdb.connect(db_path, read_only=False)
try:
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_predictions")
    print(f"[INFO] Successfully wrote 'model_eval_predictions' to DuckDB.")
except Exception as e:
    raise RuntimeError(f"[ERROR] Failed to write evaluation to DuckDB: {e}") from e
finally:
    con.close()

