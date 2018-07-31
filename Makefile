.PHONY: run_dev
run_dev:
	pipenv sync --dev && \
	FLASK_ENV=development FLASK_APP=./supernode/app.py pipenv run python -m flask run

.PHONY: run_production
run_production:
	cd supernode; \
	pipenv sync && \
	pipenv run gunicorn --bind 0.0.0.0:8000 wsgi:app

.PHONY: download_config
download_config:
	scp supernode.li:/etc/nginx/sites-available/*supernode* etc/nginx/sites-available/
	scp supernode.li:/etc/supervisor/conf.d/*supernode* etc/supervisor/conf.d/

.PHONY: migrate
migrate:
	cd supernode; \
	pipenv run flask db upgrade

.PHONY: tunnel
tunnel:
	ssh -L 10009:localhost:10009 supernode.li
