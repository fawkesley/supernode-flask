.PHONY: run_dev
run_dev:
	pipenv sync --dev && \
	FAKE_INVOICES=1 \
	FLASK_ENV=development \
	FLASK_APP=./supernode/app.py \
	pipenv run python -m flask run

.PHONY: run_production
run_production:
	./run

.PHONY: watch_invoices
watch_invoices:
	./run_invoice_watcher

.PHONY: download_config
download_config:
	scp supernode.li:/etc/nginx/sites-available/*supernode* etc/nginx/sites-available/
	scp supernode.li:/etc/supervisor/conf.d/*supernode* etc/supervisor/conf.d/

.PHONY: migrate
migrate:
	cd supernode; \
	FAKE_INVOICES=1 \
	pipenv run flask db upgrade

.PHONY: tunnel
tunnel:
	ssh -L 10009:localhost:10009 supernode.li
