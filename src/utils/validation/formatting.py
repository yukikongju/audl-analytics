from datetime import datetime

def is_valid_date(date_str: str, date_format: str = "%Y-%m-%d") -> bool:
    """
    Verify if date string respect date format
    """
    try:
        date = datetime.strptime(date_str, date_format)
        return True
    except:
        return False

