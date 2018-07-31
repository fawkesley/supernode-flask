#!/usr/bin/env python

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Invoice(db.Model):
    payment_request = db.Column(db.String(500), primary_key=True)
    paid = db.Column(db.Boolean)


@app.route("/")
def index():
    return render_template('index.html')

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
