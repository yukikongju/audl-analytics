from dagster import Definitions, ScheduleDefinition, define_asset_job, load_assets_from_package_module

from . import assets
#  from assets import etl


# “At 18:00 on Monday.” 
etl_schedule = ScheduleDefinition(job=define_asset_job(name='etl_job'),
                                      cron_schedule='0 18 * * 1')

defs = Definitions(assets=load_assets_from_package_module(assets.etl), 
                   schedules=[etl_schedule])
