from dagster import Definitions, ScheduleDefinition, define_asset_job, load_assets_from_package_module

from . import assets
#  from .assets import audl_stats


# “At 18:00 on Monday.” 
weekly_refresh_schedule = ScheduleDefinition(job=define_asset_job(name='all_assets_job'),
                                      cron_schedule='0 18 * * 1')


defs = Definitions(assets=load_assets_from_package_module(assets), 
                   schedules=[weekly_refresh_schedule])
