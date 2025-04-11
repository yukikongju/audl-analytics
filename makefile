postgres:
	pgcli -h localhost -p 5432 -u root -d audl

mongo:
	docker exec -it mongodb mongosh -u root -p example
	mongosh "mongodb://root:example@localhost:27017/"
	# use audl
	# show collections

	# mongosh "mongodb://<username>:<password>@localhost:27017/<your_db>?authSource=admin"


# python3 -m src.db.mongodb.create_games

