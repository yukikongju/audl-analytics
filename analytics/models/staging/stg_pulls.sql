{{ config(
    materialized='incremental',
    unique_key=['game_id', 'point_id']
) }}

with source_data as (
    SELECT * FROM {{ source('external', 'ext_pulls') }}
)

SELECT *
FROM source_data

{% if is_incremental() %}
WHERE 
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
    AND NOT EXISTS (
        SELECT 1 
        FROM {{ this }} target_table
        WHERE target_table.game_id = source_data.game_id
    )
{% endif %}
