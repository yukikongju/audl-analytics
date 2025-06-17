with source as (
    select * from {{ source('audl', 'game_metadata') }}
)

select * from source
