#!/usr/bin/env python

from flask import Flask, render_template
app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')

@app.route('/save-time-syncing-by-downloading-blockchain/')
def snapshot():
    return render_template('snapshot.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
