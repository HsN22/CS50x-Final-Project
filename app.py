import os
import sqlite3
import numpy as np
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from functions import apology, get_vg_temperature, get_vg_pressure

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
        #Remember to validate users input, don't convert to float straight away
        temperature = request.form.get("temperature")
        pressure = request.form.get("pressure")
        #if not temperature or pressure:
        #    return apology("Enter either T or P, not both or empty")
        #else:
        #if not pressure:
            

        #Get T_sat_data and p_sat from database and convert to numpy array
        list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
        # Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
        data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
        # Remove every second item in list of tuples
        data_tuples_filtered = data_tuples[::2]

        # Convert the list of tuples to a numpy array
        data_array = np.array(data_tuples_filtered)
        P_data = data_array[:, 0]
        Tsat_data = data_array[:, 1]

        # Check if user provides one input, not both or empty
        if (temperature and not pressure) or (pressure and not temperature):
            if temperature:
                temperature = float(temperature)
                v_g = get_vg_temperature(temperature, P_data, Tsat_data)
            else:
                pressure = float(pressure)
                v_g = get_vg_pressure(pressure, P_data, Tsat_data)
            return render_template("result.html", v = v_g)
        else:
            return apology("Enter either T or P, not both or empty")      
    else:
        #list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
        #list_of_dictionaries = db.execute("SELECT pv.pressure_bar, pv.temperature_c, pv.volume_m3_kg AS volume_m3_kg_vapor, pl.volume_m3_kg AS volume_m3_kg_liquid FROM PressureV pv JOIN PressureL pl ON pv.pressure_bar = pl.pressure_bar AND pv.temperature_c = pl.temperature_c")
        return render_template("specific.html")#,list_of_dictionaries=list_of_dictionaries)


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
        
