import os
import sqlite3
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from functions import apology, get_vg_temperature

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///database.db")


@app.route('/')
def properties():
    pressure_l_data = db.execute("SELECT * FROM PressureL")
    pressure_v_data = db.execute("SELECT * FROM PressureV")
    temperature_l_data = db.execute("SELECT * FROM TemperatureL")
    temperature_v_data = db.execute("SELECT * FROM TemperatureV")

    return render_template('properties.html',
                           pressure_l_data=pressure_l_data,
                           pressure_v_data=pressure_v_data,
                           temperature_l_data=temperature_l_data,
                           temperature_v_data=temperature_v_data)



@app.route("/specific", methods=["GET", "POST"])
def specific():
    if request.method == "POST":
        temperature = request.form.get("temperature")
        #Remember to validate users input, don't convert to float straight away
        temperature = float(temperature)
        v_g = get_vg_temperature(temperature)
        return render_template("result.html", v = v_g)
    
    else:
        return render_template("specific.html")


@app.route("/adibatic", methods=["GET", "POST"])
def adibatic():
    if request.method == "POST":
        pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")
        #return f"Pressure: {pressure}"
        pressure = float(pressure)
        temperature = float(temperature)
        initial_entropy = db.execute("SELECT entropy_J_gK FROM PressureV WHERE pressure_bar = ?", pressure)
        # Get pressure from list of dictionary
        for row in initial_entropy:
            pressurecalc = row["entropy_J_gK"]
        # print(pressurecalc)
        sf = db.execute("SELECT entropy_J_gK FROM TemperatureL WHERE temperature_c = ?", temperature)
        sg = db.execute("SELECT entropy_J_gK FROM TemperatureV WHERE temperature_c = ?", temperature)
        for row in sf:
            s_f = row["entropy_J_gK"]
        for row in sg:
            s_g = row["entropy_J_gK"]
        s_fg = s_g - s_f
        print(s_fg)
        x = (pressurecalc - s_f) / s_fg
        print(x)
        return render_template("adibaticres.html" , pressurecalc=pressurecalc)
    else:
        return render_template("adibatic.html")
        
