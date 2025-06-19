import argparse

def main():
    # --- TODO: get game schedule within dates

    # --- TODO: get games already in MongoDB document

    # --- TODO: get the games we need to fetch

    # --- TODO: insert document into MongoDB
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracting all game events within dates")
    parser.add_argument("--start_date", type=str, help="Start date in format 'YYYY-MM-DD'")
    parser.add_argument("--end_date", type=str, help="End date in format 'YYYY-MM-DD'")

    main()
