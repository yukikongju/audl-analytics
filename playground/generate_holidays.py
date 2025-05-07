import pandas as pd
import os
import inspect
import holidays
import sys
from datetime import datetime, timezone
from typing import List

def main(start_date: pd.to_datetime, end_date: pd.to_datetime):
    # --- 1. generate all dates
    countries = list(set(dct_country_to_continent.keys()))
    date_range = pd.date_range(start=start_date, end=end_date)

    # --- 2. get holiday for supoprted countries
    years = list(set(date_range.year))
    supported_countries = set(holidays.list_supported_countries().keys())
    df_supported = pd.DataFrame(
        [(d, c) for d in date_range for c in supported_countries],
        columns=["date", "country_code"],
    )
    holiday_dict = {
        country: holidays.CountryHoliday(country, years=years)
        for country in supported_countries
    }

    def get_holiday_info(row):
        h = holiday_dict[row["country_code"]]
        date = row["date"].date()
        if date in h:
            return pd.Series([True, h[date]])
        else:
            return pd.Series([False, None])

    df_supported[["is_holiday", "holiday_name"]] = df_supported.apply(
        get_holiday_info, axis=1
    )

    # --- 3. generate default dataframe for unsupported countries
    unsupported_countries = list(set(countries) - set(supported_countries))
    unsupported_countries.sort()
    df_unsupported = pd.DataFrame(
        [(d, c) for d in date_range for c in unsupported_countries],
        columns=["date", "country_code"],
    )
    df_unsupported["is_holiday"] = False
    df_unsupported["holiday_name"] = None

    # --- 4. Generatate Dates DataFrame
    df_dates = pd.DataFrame(date_range, columns=["date"])
    df_dates["week_of_year"] = df_dates["date"].apply(lambda x: x.isocalendar()[1])
    df_dates["day_of_week"] = df_dates["date"].apply(lambda x: x.isocalendar()[2])

    # --- 5. Concatenate and add week of year and day of week
    df_holidays = pd.concat([df_supported, df_unsupported])
    df_holidays.sort_values(by=["date", "country_code"])
    df_holidays = df_holidays.merge(df_dates, on=["date"], how="left")

    # --- 6. push into bigquery


if __name__ == "__main__":
    start_date = pd.to_datetime("2025-01-01")
    end_date = pd.to_datetime("2025-02-01")
    main(start_date=start_date, end_date=end_date)

