#!/usr/bin/env python

import datetime
import os
import uuid

from flask import Flask, render_template, request, redirect, url_for
from flask_json import FlaskJSON, as_json, JsonError
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from lndgrpc import LNDClient

from os.path import join as pjoin, dirname

AUTH_DIR = pjoin(dirname(__file__), '..', 'lnd_auth')

PRODUCTS = {
    'web-haiku': 125000,
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.sqlite3'
app.config['JSON_ADD_STATUS'] = False
app.config['FAKE_INVOICES'] = os.environ.get('FAKE_INVOICES', '0') == '1'

json = FlaskJSON(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class FakeLNDClient():
    def __init__(self, *args, **kwargs):
        pass

    def add_invoice(self, amount):
        class FakeAddInvoiceResponse():
            def __init__(self, satoshis):
                self.satoshis = satoshis
                self.payment_request = 'FAKE_{}'.format(str(uuid.uuid4()))

        return FakeAddInvoiceResponse(amount)


def make_lnd_client():
    if app.config['FAKE_INVOICES']:
        return FakeLNDClient()
    else:
        return LNDClient("127.0.0.1:10009",
                         macaroon_filepath=pjoin(AUTH_DIR, 'admin.macaroon'),
                         cert_filepath=pjoin(AUTH_DIR, 'tls.cert'))


def make_payment_request(satoshis):
    """
    Make an invoice in `lnd` and a matching invoice in our database, returning
    the `payment_request`
    """
    add_invoice_response = lnd.add_invoice(satoshis)
    payment_request = add_invoice_response.payment_request

    invoice = Invoice(payment_request=payment_request, paid=False)
    db.session.add(invoice)
    db.session.commit()

    return payment_request


lnd = make_lnd_client()


class Invoice(db.Model):
    payment_request = db.Column(db.String(500), primary_key=True)
    paid = db.Column(db.Boolean)


class Haiku(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    haiku = db.Column(db.String(500))
    sold_to_payment_request = db.Column(
        db.String(500), index=True, nullable=True
    )


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/buy-a-haiku")
def haiku():
    return render_template('haiku.html')

@app.route("/apiv1/shop/make-invoice", methods=['POST'])
@as_json
def make_invoice():
    try:
        product_slug = request.get_json()['product']
        satoshis = PRODUCTS[product_slug]
    except KeyError:
        raise JsonError(status_=400, message='Specify valid `product` in JSON')

    return {
        'payment_request': make_payment_request(satoshis),
        'satoshis': satoshis
    }


@app.route("/apiv1/shop/invoice/<payment_request>", methods=['GET'])
@as_json
def check_invoice_paid(payment_request):
    invoice = Invoice.query.get(payment_request)

    if invoice is None:
        raise JsonError(
            status_=404,
            message="No such invoice with that `payment_request`: '{}'".format(
                payment_request
                )
        )

    return {
        'payment_request': invoice.payment_request,
        'paid': invoice.paid,
    }


@app.route("/shop/<product_slug>/", methods=['GET'])
def redirect_to_payment_request(product_slug):
    satoshis = PRODUCTS[product_slug]
    payment_request = make_payment_request(satoshis)

    return redirect(
        url_for(
            'product_payment_request',
            product_slug=product_slug,
            payment_request=payment_request
        )
    )


@app.route("/invoice/<product_slug>/<payment_request>/", methods=['GET'])
def product_payment_request(product_slug, payment_request):
    return render_template(
        'invoice.html',
        product_slug=product_slug,
        payment_request=payment_request
    )


@app.route("/shop/deliver/<product_slug>/<payment_request>/", methods=['GET'])
def deliver_product(product_slug, payment_request):
    return 'Have a Haiku!'


@app.route('/save-time-syncing-by-downloading-blockchain/')
def snapshot():
    return render_template('snapshot.html')

@app.route('/thanks/')
def thanks():
    return render_template('thanks.html')

@app.route('/turn-a-pi-into-a-bitcoin-and-lightning-network-full-node/')
def pi():
    return render_template('pi.html')


class InvoiceSyncer():
    def __init__(self, lnd, echo=None):
        self.lnd = lnd
        self.echo = echo or self._echo

        self._remote_cache = {}  # payment_request -> remote_invoice
        self._delete_local = set()

    def sync(self):
        self.cache_valid_remote_invoices()
        self.sync_remote_invoices_to_local()

        self.delete_invalid_local_invoices()
        # self.delete_invalid_remote_invoices()

    def _echo(self, message):
        print(message)

    def cache_valid_remote_invoices(self):
        for remote_invoice in lnd.list_invoices().invoices:
            if not self.has_expired(remote_invoice):
                self._remote_cache[
                    remote_invoice.payment_request
                ] = remote_invoice

            # ignore expired remote invoices
        self.echo('Cached {} remote invoices'.format(len(self._remote_cache)))

    def sync_remote_invoices_to_local(self):
        dirty = False

        for local_invoice in Invoice.query.all():
            try:
                remote_invoice = self._remote_cache[
                    local_invoice.payment_request
                ]
            except KeyError:
                self.echo('Local invoice has no valid remote `{}`'.format(
                    local_invoice.payment_request)
                )

                self._delete_local.add(local_invoice)
            else:
                if local_invoice.paid != remote_invoice.settled:
                    self.echo('Syncing invoice `{}`'.format(
                        local_invoice.payment_request)
                    )
                    local_invoice.paid = remote_invoice.settled
                    dirty = True

        if dirty:
            self.echo('Saving changes to database')
            db.session.commit()

    @staticmethod
    def has_expired(remote_invoice, now=None):
        now = now or datetime.datetime.now()
        expires = datetime.datetime.fromtimestamp(
            remote_invoice.creation_date + remote_invoice.expiry
        )
        return now > expires

    def delete_invalid_local_invoices(self):
        if not self._delete_local:
            return

        self.echo('Deleting {} local invoices'.format(
            len(self._delete_local))
        )
        for invoice in self._delete_local:
            db.session.delete(invoice)
        db.session.commit()


@app.cli.command()
def watch_invoices():
    """Checks `lnd` whether invoices have been paid"""
    import click
    import time

    click.echo('Connecting to `lnd` and watching invoices')

    while True:
        syncer = InvoiceSyncer(lnd, echo=click.echo)
        syncer.sync()
        time.sleep(10)


@app.cli.command()
def add_haiku():
    """Adds a haiku into the database ready to sell"""

    while True:
        print('\nenter haiku:\n')

        haiku_lines = []

        for i in range(3):
            haiku_lines.append(input(''))

        lines_joined = ('{}\n{}\n{}'.format(*[l.strip() for l in haiku_lines]))

        haiku = Haiku(haiku=lines_joined, sold_to_payment_request=None)
        db.session.add(haiku)
        db.session.commit()

        print('Saved haiku to db:\n\n{}\n'.format('\\ '.join(haiku_lines)))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
