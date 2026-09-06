import duckdb
import joblib
import lightgbm as lgbm
import os
import pandas as pd
import xgboost as xgb


from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

from objectives import OBJECTIVE_REGISTRY, run_bayesian
from queries import QUERY_REGISTRY


### 0. Config Parser
model_type = "xgb"
#  db_path = "/Users/emulie.chhor/.Data/ufa/analytics/dev.duckdb"
db_path = os.path.join(os.getenv("AUDL_ANALYTICS_DIR"), "dev.duckdb")
models_dir = os.getenv("AUDL_MODELS_DIR")
query_name = "player_game_stats"
metric_type = "rolling" # lag
scoring_type = "neg_root_mean_squared_error"
train_size = 0.8
n_splits = 5
n_trials = 2 # 50


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
    "pulls",
    "ob_pulls",
    "recorded_pulls",
    "recorded_pulls_hangtime",
    "o_points_played",
    "o_points_scored",
    "d_points_played",
    "d_points_scored",
    "seconds_played",
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

# TODO verify configs


### 1. Load Data
con = duckdb.connect(db_path, read_only=True)
try:
    df = con.execute(QUERY_REGISTRY[query_name]).df()
except Exception as e:
    raise RuntimeError(f"query '{query_name}' failed: {e}") from e
finally:
    con.close()


### 2. Split into train/val/test dataset
df[CAT_COLS] = df[CAT_COLS].astype('category')
df = df.sort_values(by=["ext_player_id", "game_date"])
group_row_number = df.groupby(["ext_player_id"]).cumcount()
group_size = df.groupby(["ext_player_id"])["ext_player_id"].transform('size')
is_train = group_row_number < (group_size * train_size)
df_train = df[is_train]
df_test = df[~is_train]

print(f"[INFO] Train Dataset Size: {len(df_train)} ; Test Dataset Size: {len(df_test)}")

### 3. Feature Engineering
metric_cols = [metric for metric in df.columns if metric_type in metric]
feature_cols = [c for c in KEY_COLS if c not in DROP_KEY_COLS] + metric_cols
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
model_path = os.path.join(models_dir, f"player_stats_{model_type}.joblib")
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
table_name = f"{query_name}_predictions"
con = duckdb.connect(db_path, read_only=False)
try:
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_predictions")
    print(f"[INFO] Successfully wrote 'model_eval_predictions' to DuckDB.")
except Exception as e:
    raise RuntimeError(f"[ERROR] Failed to write evaluation to DuckDB: {e}") from e
finally:
    con.close()

