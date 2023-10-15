from dagster import asset, graph, op
from audl.stats.endpoints.gamestats import GameStats
from audl.stats.endpoints.playerprofile import PlayerProfile


game_id = '2023-08-25-ATX-NY'
    
@asset(deps=[game_id])
def fetch_game_data():
    # Fetch Game results
    game = GameStats(game_id=game_id)

    # Get Game Events as JSON
    game_json = game.json

    # Get players/teams infos
    df_players = game.get_players_metadata()
    df_teams = game.get_teams_metadata()

    # Get Players that played and query their game stats
    df_playerstats = game.get_roster_stats()

    return game_json, df_players, df_teams


@asset(deps=[fetch_game_data])
def store_players_game_stats(): # TODO
    pass
        
@asset(deps=[fetch_game_data])
def store_teams_game_stats(): # TODO
    pass

@asset(deps=[fetch_game_data])
def store_game_events_json(): # TODO
    pass


