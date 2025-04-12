# TODOs

**CI/CD**

- [ ] Precommit Hook

**Databases**

1. [X] Initialize Docker => posgresql, airflow, mongoDB, neo4j
2. [X] Create MongoDB Utils
    - [X] Database connection
    - [X] Create collection
    - [X] insert document
3. [o] Create postgres Utils
    - [X] connection
    - [X] Create Table
    - [ ] insert

**ELT**

- [.] Extraction Jobs
    - [o] Extract season schedule from season
    - [X] Extract Game events from game external id "2024-08-24-CAR-MIN"
- [ ] Transformations
    - [ ] From Game Events, get team metadata => `game.get_teams_metadata()`
    - [ ] From Game Events, get player metadata => `game.get_players_metadata()`
    - [ ] 
    - [ ] From [Game Events??], get throw selection
    - [ ] From Game Events, get roster stats => `game.get_roster_stats()`
    - [ ] From Roster Stats, get boxscores => `game.get_team_stats()`
    - [ ] From Game Events, get scoring time => `game._get_scoring_time()`
- [ ] Backfilling

**Data Modeling**

1. [ ] Create ER 
    a. [ ] Player
    b. [ ] Games IDs
    c. [ ] Teams
    d. [ ] Game Events JSON
2. [ ] Finish ELT Diagram => 

**Visualization**


**ML**

1. [ ] Setup MLFlow


Questions:
- how to implement 2PC


Notes:
- Index MongoDB using hash index instead of B-Tree

