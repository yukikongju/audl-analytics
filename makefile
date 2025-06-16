postgres:
	pgcli -h localhost -p 5432 -u root -d audl

mongo:
	docker exec -it mongodb mongosh -u root -p example
	mongosh "mongodb://root:example@localhost:27017/"
	# use audl
	# show collections
	# db.games.find({ "game.ext_game_id": "2022-07-31-DET-MIN" }).pretty()
	# db.games.countDocuments()

	# mongosh "mongodb://<username>:<password>@localhost:27017/<your_db>?authSource=admin"


# python3 -m src.db.mongodb.create_games
# python3 -m src.extract.extract_game_events --ext_game_id "2024-08-24-CAR-MIN"


tests:
	python3 -m pytest --print tests/

