# Estimating how much spaces would be required for each database

**Game Events JSON**

- MongoDB: 512MB to 5 GB storage
- GameEvents.json: 60K
- Number of games per season: 190 (in 2023)

Conclusion: we chillin

**Player Completion Rate Graph**

- neo4j: 200 000 nodes ; 400 000 relationships
- Players: < 1500
- PlayersGameEvents: 35 throws per points x 40 points per game x 190 games = 266,000 edges per season

Conclusion: We can fetch data for 2-3 years before paying for extension

**Players/Teams Game Stats Table**

- 
