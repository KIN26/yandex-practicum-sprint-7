shell:
	@docker compose run --rm app /bin/bash

create-index:
	@docker compose run --rm app poetry run python main.py create-index

search:
	@docker compose run --rm app poetry run python main.py search
