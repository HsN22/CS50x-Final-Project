import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from functions import apology, interpolate

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///databaseName.db")
# @app.route("/login", methods=["GET", "POST"])

@app.route("/", methods=["GET", "POST"])
def specific():
    if request.method == "POST":
        temperature = request.form.get("temperature")
        #Remember to validate users input, don't convert to float straight away
        temperature = float(temperature)
        v_g = interpolate(temperature)
        return render_template("result.html", v = v_g)
    
    else:
        return render_template("specific.html")