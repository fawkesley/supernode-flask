#!/usr/bin/env python

import uuid

from flask import Flask, render_template, request
from flask_json import FlaskJSON, as_json, JsonError
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

PRODUCTS = {
    'web-haiku': 125000,
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
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

    payment_request = 'FAKE_{}'.format(str(uuid.uuid4()))
    invoice = Invoice(payment_request=payment_request, paid=False)
    db.session.add(invoice)
    db.session.commit()

    return {
        'payment_request': payment_request,
        'satoshis': satoshis
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
