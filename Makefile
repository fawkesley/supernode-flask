.PHONY: run_dev
run_dev:
	export FLASK_DEBUG=1
	pipenv sync --dev && \
	pipenv run ./supernode/app.py

.PHONY: run_production
run_production:
	cd supernode; \
	pipenv sync && \
	pipenv run gunicorn --bind 0.0.0.0:8000 wsgi:app

.PHONY: download_config
download_config:
	scp supernode.li:/etc/nginx/sites-available/*supernode* etc/nginx/sites-available/
	scp supernode.li:/etc/supervisor/conf.d/*supernode* etc/supervisor/conf.d/
