.PHONY: run_dev
run_dev:
	pipenv run ./supernode/app.py

.PHONY: run_production
run_production:
	pipenv run uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app
