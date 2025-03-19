# AUDL Analytics

Code for to ingest AUDL data. The goal of this project is to create a 
pipeline that can be reproduced locally by others so that they can 
explore AUDL analytics on their own

## Entity-Relationship Diagram

The ER diagram can be found in the folder `diagrams/` and can be open 
using [drawio](https://www.drawio.com/)

## Technologies Used

Databases:
- Relational Database (PostgreSQL, DuckDB) => Player, Team and Game Stats
- Document-Oriented Database (MongoDB) => to store game events JSON
- Graph Databases (Neo4j) => to keep track of player passes 

DevOps Tools:
- Docker

Data Orchestration:
- Airflow

DE Tools:
- dbt
- pyspark


