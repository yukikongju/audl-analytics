import pandas as pd

from dagster import asset, graph, op
from audl.stats.endpoints.gamestats import GameStats
from audl.stats.endpoints.playerprofile import PlayerProfile


game_id = '2023-08-25-ATX-NY'
    
@asset(deps=[game_id], compute_kind='AUDL API')
def fetch_game():
    game = GameStats(game_id=game_id)
    return game

@asset(deps=[fetch_game], group_name='game_json', compute_kind='AUDL API')
def game_events_extraction() -> pd.DataFrame:
    return game.json

@asset(deps=[fetch_game], group_name='players_extraction', compute_kind='AUDL API')
def players_extraction():
    return game.get_players_metadata()

@asset(deps=[fetch_game], group_name='teams_extraction', compute_kind='AUDL API')
def teams_extraction():
    return game.get_teams_metadata()

@asset(deps=[fetch_game], group_name='players_stats_extraction', compute_kind='AUDL API')
def players_stats_extraction():
    return game.get_roster_stats()

@asset(deps=[fetch_game], group_name='teams_stats_extraction', compute_kind='AUDL API')
def teams_stats_extraction():
    return game.get_team_stats()

#  ---

@asset(deps=[players_extraction], group_name='players_extraction', compute_kind='BigQuery')
def store_players_metadata(): # TODO
    pass

@asset(deps=[teams_extraction], group_name='teams_extraction', compute_kind='BigQuery')
def store_teams_metadata(): # TODO
    pass

@asset(deps=[players_stats_extraction], group_name='players_stats_extraction', compute_kind='BigQuery')
def store_players_game_stats(): # TODO
    pass
        
@asset(deps=[teams_stats_extraction], group_name='teams_stats_extraction', compute_kind='Neo4j')
def store_teams_game_stats(): # TODO
    pass

@asset(deps=[game_events_extraction], group_name='game_json', compute_kind='MongoDB')
def store_game_events_json(): # TODO
    pass

#  --- 

@asset(deps=[game_events_extraction], group_name='players_completion_graph', compute_kind='pandas')
def player_completion_rate_transformation():
    pass

@asset(deps=[game_events_extraction], group_name='game_json', compute_kind='pandas')
def throwing_sequence_transformation():
    pass

#  --- 

@asset(deps=[player_completion_rate_transformation], group_name='players_completion_graph', compute_kind='Neo4j')
def store_player_completion_rate_transformation():
    pass

