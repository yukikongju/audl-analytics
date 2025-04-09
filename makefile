postgres:
	pgcli -h localhost -p 5432 -u root -d audl

mongo:
	docker exec -it mongodb mongosh -u root -p example
