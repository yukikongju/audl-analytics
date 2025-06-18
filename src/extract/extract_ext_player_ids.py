import pandas as pd
import requests

from bs4 import BeautifulSoup
from typing import List

def get_all_player_ext_ids() -> List[str]:
    page_idx = 0
    page_empty = False
    ext_player_ids = []
    while not page_empty:
        url = f"https://www.watchufa.com/league/players?page={page_idx}"
        print(url)
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        a_tags = soup.find_all('a', href=True)
        players = [tag['href'].split('/')[-1] for tag in a_tags if tag['href'].startswith('/league/players/')]
        if len(players) == 0:
           page_empty = True 
        ext_player_ids += players
        page_idx += 1
    return ext_player_ids


def main():
    ext_player_ids = get_all_player_ext_ids()
    df_players = pd.DataFrame(ext_player_ids, columns=['ext_player_id'])
    FILE_PATH = 'dbt/seeds/ext_player_ids.csv'
    df_players.to_csv(FILE_PATH, index=False)
    print(f"Successfully saved ext_player_ids in {FILE_PATH}")

if __name__ == "__main__":
    main()

