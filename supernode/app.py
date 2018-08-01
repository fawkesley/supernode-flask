#!/usr/bin/env python

from flask import Flask, render_template, request
from flask_json import FlaskJSON, as_json, JsonError
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from lndgrpc import LNDClient

from os.path import join as pjoin, dirname

AUTH_DIR = pjoin(dirname(__file__), '..', 'lnd_auth')

lnd = LNDClient("127.0.0.1:10009",
                macaroon_filepath=pjoin(AUTH_DIR, 'admin.macaroon'),
                cert_filepath=pjoin(AUTH_DIR, 'tls.cert'))

lnd.get_info()


PRODUCTS = {
    'web-haiku': 125000,
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.sqlite3'
app.config['JSON_ADD_STATUS'] = False

json = FlaskJSON(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Invoice(db.Model):
    payment_request = db.Column(db.String(500), primary_key=True)
    paid = db.Column(db.Boolean)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/apiv1/shop/make-invoice", methods=['POST'])
@as_json
def make_invoice():
    try:
        product_slug = request.get_json()['product']
        satoshis = PRODUCTS[product_slug]
    except KeyError:
        raise JsonError(status=400, message='Specify valid `product` in JSON')

    add_invoice_response = lnd.add_invoice(satoshis)
    payment_request = add_invoice_response.payment_request

    invoice = Invoice(payment_request=payment_request, paid=False)
    db.session.add(invoice)
    db.session.commit()

    return {
        'payment_request': payment_request,
        'satoshis': satoshis
    }


@app.route("/apiv1/shop/invoice/<payment_request>", methods=['GET'])
@as_json
def check_invoice_paid(payment_request):
    invoice = Invoice.query.get(payment_request)

    if invoice is None:
        raise JsonError(
            status=400,
            message='Specify valid `payment_request` in JSON'
        )

    return {
        'payment_request': invoice.payment_request,
        'paid': invoice.paid,
    }


@app.route('/save-time-syncing-by-downloading-blockchain/')
def snapshot():
    return render_template('snapshot.html')

@app.route('/thanks/')
def thanks():
    return render_template('thanks.html')

@app.route('/turn-a-pi-into-a-bitcoin-and-lightning-network-full-node/')
def pi():
    return render_template('pi.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
