.PHONY: run_dev
run_dev:
	pipenv run ./supernode/app.py

.PHONY: run_production
run_production:
	cd supernode; \
	pipenv sync && \
	pipenv run gunicorn --bind 0.0.0.0:8000 wsgi:app
