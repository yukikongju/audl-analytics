from dagster import Definitions, ScheduleDefinition, define_asset_job, load_assets_from_modules, AssetSelection

#  from . import assets
from .assets import etl

#  --- ETL Job: “At 18:00 on Monday.” 
etl_assets = load_assets_from_modules([etl])
etl_job = define_asset_job("etl_job", selection=AssetSelection.all())
etl_schedule = ScheduleDefinition(job=etl_job, cron_schedule='0 18 * * 1')

defs = Definitions(assets=etl_assets, schedules=[etl_schedule])

