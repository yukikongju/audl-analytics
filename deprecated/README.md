# AUDL Analytics

## Goal of this Project

[Pipeline](https://docs.google.com/drawings/d/1IdWRcp2mRWDZX7EwqnIUUZ3jFeHZ4ynZm599IL8uahc/edit)

## Tables Schema

**Game Events (JSON) [ COMPLETED ]**

- Table Name: `GameEvents`
- Endpoints: `audlstats.com/stats-pages/game/{2023-08-25-ATX-NY <game_id>}`
- Delete Query: None. Only insert in database if not found
- Schema: Insert as Raw

**Team Information Table (MySQL) [ COMPLETED ]**

- Table Name: `Teams`
- Endpoints: `audlstats.com/stats-pages/game/{2023-08-25-ATX-NY <game_id>}`
- Delete Query: None. Only insert in database if not found
- Schema:

    ```
    - id: int
    - team_id: int
    - season_id: int
    - division_id: int
    - city: str
    - abbrev: str
    - ulti_analytics_ext_id: str
    - final_standing: str
    - team_name: str
    - ext_team_id: str
    - ls_team_id: str
    - active: bool
    - primary_hex: str
    - secondary_hex: str
    ```

![images/teams_seasons_infos.png]

**Player Information Table (MySQL) [ COMPLETED ]**

- Table Name: `Players`
- Endpoints: `audlstats.com/stats-pages/game/{2023-08-25-ATX-NY <game_id>}`
- Delete Query: None. Only insert in database if not found
- Schema:

    ```
    - id: int [key]
    - team_season_id: int
    - player_id: int
    - jersey_number: int
    - active: bool
    - player_id: int [key]
    - first_name: str
    - last_name: str
    - ext_player_id: str
    - ls_player_id: str
    ```

![images/player_infos_schema.png]


**Player Game Stats Table (MySQL) [ COMPLETED ]**

- Table Name: `PlayerGameStats`
- Endpoints: `https://www.backend.audlstats.com/web-api/roster-game-stats-for-player?playerID={jbabbitt <ext_player_id>}&year={2023 <year>}`
- Delete Query: delete where game_id
- Schema:

    ```
    - player_id: int [key]
    - gameID: str [key]
    - reg_season: bool
    - isHome: bool
    - scoreHome: int
    - scoreAway: int
    - assists: int
    - goals: int
    - hockeyAssists: int
    - completions: int
    - throwaways: int
    - stalls: int
    - throwsAttempted: int
    - catches: int
    - drops: int
    - block: int
    - callahans: int
    - pulls: int
    - obPulls: int
    - recordedPulls: int
    - recordedPullsHangTime: float
    - oPointsPlayed: int
    - oPointsScored: int
    - dPointsPlayed: int
    - dPointsScored: int
    - secondsPlayed: int
    - yardsReceived: int
    - yardsThrown: int
    - hucksCompleted: int
    - hucksAttempted: int

    To add? No because EXTRACTION
    - breaksAttempted: int
    - breaksCompleted: int
    - dumpsAttempted: int
    - dumpsCompleted: int
    - flicksAttempted: int
    - flicksCompleted: int
    - swingsAttempted: int
    - swingsCompleted: int
    - dishesAttempted: int
    - dishesCompleted: int
    ```

![images/player_game_stats_endpoint.png]

**Team Game Stats Table (MySQL) [ COMPLETED ]**

- Table Name: `TeamGameStats`
- Endpoints: `https://www.backend.audlstats.com/stats-pages/game/2023-08-25-ATX-NY`
- Delete Query: delete where game_id
- Schema:

    ```
    - team_id: int [key]
    - gameID: str [key]
    - reg_season: bool
    - scoreTimeOurs: [int]
    - scoreTimeTheir: [int]
    - rosterIDs: [int]
    - completionsNumer: int
    - completionsDenom: int
    - hucksNumer: int
    - hucksDenom: int
    - blocks: int
    - turnovers: int
    - oLineScores: int
    - oLinePoints: int
    - oLinePossessions: int
    - dLineScores: int
    - dLinePoints: int
    - dLinePossessions: int
    - redZoneScores: int
    - redZonePossessions: int
    - isHome: bool
    ```

![images/teams_game_stats_infos.png]

**Player Completion Rate Graph (GraphQL) [ TO REVIEW ]**


- Table Name: `PlayersCompletionRateGraph`
- Endpoints: Transform from `GameEvents` table
- Delete Query: delete edge where game_id
- Schema:

    ```
    Node: Player
    - ext_player_id
    - last_name

    Edge: Throws Attempts
    - gameID: str [key]
    - reg_season: bool
    - point_number: int [key]
    - sequence_number: int [key] (?)
    - sequence_length: int
    - throw_type: str
    - x: float
    - y: float
    - is_success: bool
    ```

**Team Completion Rate Graph (GraphQL) [ TO REVIEW ]**

- Table Name: `TeamsCompletionRateGraph`
- Endpoints: Transform from `GameEvents` table
- Delete Query: delete edge where game_id
- Schema: Duplicate of `TeamGameStats`?


## Technologies used

- [ ] Data Orchestration: `Dagster` and `Github Actions`
- [ ] Database: 
	* Document-Based for JSON file: [ `MongoDB` ] or `Firebase`
	* NoSQL Database: `Cassandra` with AstraDB
	* SQL Database: `PostgreSQL` or [ `BigQuery` ]
	* Graph Database: `GraphQL` or [ `Neo4j` ] or [ `graphene` ]
- [ ] CI/CD: `Github Actions` or `Terraform`
- [ ] Containerization: `Docker`
- [ ] Distributed Computing: `pyspark`
- [ ] Unit Testing: `pytest`

**Optional**

- [ ] Drift Detection: 
- [ ] Hyperparameters Tuning:
- [ ] Caching: `Redis`
- [ ] Retraining ML Models: `SageMaker` or `Apache Spark` or `Google AutoML`
- [ ] MLOps: `MLFlow` or `Airflow`
- [ ] Clusters: `Databricks` or `Snowflake`
- [ ] Self-Hosted or Cloud


## Ressources

**Dagster**

- [Dagster - Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules)
- [Dagster - Dynamic Outs](https://discuss.dagster.io/t/2644935/sounds-great-claire-i-think-you-gave-me-the-recipe-i-need-th)
- [Dagster - Dynamic Graphs](https://docs.dagster.io/concepts/ops-jobs-graphs/dynamic-graphs#a-dynamic-job)

**Terraform**

- [Terraform with Github Actions](https://developer.hashicorp.com/terraform/tutorials/automation/github-actions)
- [Continuous INtegration for Terraform Modules with Github Actions](https://www.hashicorp.com/blog/continuous-integration-for-terraform-modules-with-github-actions)

**Neo4j**

- [Neo4j Console](https://console.neo4j.io/?product=aura-db#databases)


