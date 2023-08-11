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

db = SQL("sqlite:///RogersAndMayhewSteamTables.db")


@app.route('/')
def properties():
    pressure_data = db.execute("SELECT * FROM saturated_water_by_sat_pres")
    temperature_data = db.execute("SELECT * FROM saturated_water_by_sat_temp")

    return render_template('properties.html',
                           pressure_data=pressure_data,
                           temperature_data=temperature_data)



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
        initial_entropy = db.execute("SELECT s_f FROM saturated_water_by_sat_pres WHERE Sat_p = ?", pressure)
        # Get pressure from list of dictionary
        for row in initial_entropy:
            pressurecalc = row["s_f"]
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
        hf = db.execute("SELECT enthalpy_kJ_kg FROM TemperatureL WHERE temperature_c = ?", temperature)
        hg = db.execute("SELECT enthalpy_kJ_kg FROM TemperatureV WHERE temperature_c = ?", temperature)
        for row in hf:
            h_f = row["enthalpy_kJ_kg"]
        for row in hg:
            h_g = row["enthalpy_kJ_kg"]
        h_fg = h_g - h_f
        h2 = h_f + x*h_fg
        return render_template("adibaticres.html" , h2=h2)
    else:
        return render_template("adibatic.html")
        
