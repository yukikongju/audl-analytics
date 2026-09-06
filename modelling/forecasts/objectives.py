"""Optuna hyperparameter-search objectives for the forecasting models.

Defines one objective function per model (`lgbm`, `xgb`, `random_forest`),
registered in `OBJECTIVE_REGISTRY`. Each objective evaluates a candidate
parameter set via `cross_val_score` over a `StandardScaler`-wrapped
`MultiOutputRegressor` and returns the mean loss to minimize. `run_bayesian`
drives the TPE sampler over a chosen objective for a given number of trials.
"""

import lightgbm as lgbm
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection._split import BaseCrossValidator
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor


from typing import Dict, Callable
from utils import registry

OBJECTIVE_REGISTRY: Dict[str, Callable] = {}

# TODO replace MultiOutputRegressor with RegressorChain
# TODO add monotonic constraints, interaction constraints



@registry(OBJECTIVE_REGISTRY, "lgbm")
def lgbm_objective(trial, X: pd.DataFrame, y: pd.DataFrame, cv: BaseCrossValidator, scoring: str) -> float:
    params = {
        "n_estimators":     trial.suggest_int("n_estimators", 200, 600),
        "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves":       trial.suggest_int("num_leaves", 10, 100),
        "max_depth":        trial.suggest_int("max_depth", 3, 7),
        "lambda_l2":        trial.suggest_float("lambda_l2", 0.1, 30, log=True),
        "lambda_l1":        trial.suggest_float("lambda_l1", 0.0, 1.0),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 0.8),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.7, 0.9),
        "bagging_freq":     trial.suggest_int("bagging_freq", 1, 10),
        "min_child_weight": trial.suggest_int("min_child_weight", 10, 100),
        "min_split_gain":   trial.suggest_float("min_split_gain", 0.0, 5.0),
        "objective":        "regression",
        "verbosity":        -1,
        "random_state":     42,
    }
    base_model = lgbm.LGBMRegressor(**params)
    multi_model = MultiOutputRegressor(base_model)
    scaled_model = TransformedTargetRegressor(
        regressor=multi_model,
        transformer=StandardScaler()
    )

    scores = cross_val_score(
        #  multi_model, 
        scaled_model, 
        X, 
        y, 
        cv=cv, 
        scoring=scoring, 
        n_jobs=-1
    )
    return -scores.mean()

@registry(OBJECTIVE_REGISTRY, "xgb")
def xgb_objective(trial, X: pd.DataFrame, y: pd.DataFrame, cv: BaseCrossValidator, scoring: str):
    params = {
        "n_estimators":     trial.suggest_int("n_estimators", 200, 600),
        "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth":        trial.suggest_int("max_depth", 3, 10),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "subsample":        trial.suggest_float("subsample", 0.5, 0.9),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 0.9),
        "reg_alpha":        trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),   # L1
        "reg_lambda":       trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),  # L2
        "gamma":            trial.suggest_float("gamma", 1e-8, 1.0, log=True),
        "objective":        "reg:squarederror",
        "tree_method":       "hist",
        "enable_categorical": True,
        "eval_metric":       "rmse",
        "n_jobs":           1,  # Keep 1 thread per estimator to prevent CPU oversubscription
        "random_state":     42,
    }
    base_model = xgb.XGBRegressor(**params)
    multi_model = MultiOutputRegressor(base_model)
    scaled_model = TransformedTargetRegressor(
        regressor=multi_model,
        transformer=StandardScaler()
    )
    scores = cross_val_score(
        #  multi_model, 
        scaled_model, 
        X, 
        y, 
        cv=cv, 
        scoring=scoring, 
        n_jobs=-1
    )
    return -scores.mean()


@registry(OBJECTIVE_REGISTRY, "random_forest")
def rf_objective(trial, X: pd.DataFrame, y: pd.DataFrame, cv: BaseCrossValidator, scoring: str):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 100, 500, step=50),
        "max_depth":         trial.suggest_int("max_depth", 3, 20),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf":  trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features":      trial.suggest_float("max_features", 0.4, 1.0),
        "bootstrap":         True,
        "n_jobs":            1,  # Keep 1 thread per tree; cross_val_score handles parallel folds
        "random_state":      42,
    }
    base_model = RandomForestRegressor(**params)
    #  multi_model = MultiOutputRegressor(base_model) # FIXME rfr accepts multi-output regressor
    scaled_model = TransformedTargetRegressor(
        regressor=multi_model,
        transformer=StandardScaler()
    )
    scores = cross_val_score(
        #  base_model, 
        scaled_model, 
        X, 
        y, 
        cv=cv, 
        scoring=scoring, 
        n_jobs=-1
    )
    return -scores.mean()


def run_bayesian(objective, name, X, y, cv, scoring, n_trials=100):
    study = optuna.create_study(
        direction="minimize", # maximize
        study_name=name,
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    study.optimize(lambda trial: objective(trial, X, y, cv, scoring), n_trials=n_trials, show_progress_bar=True)
    return study

