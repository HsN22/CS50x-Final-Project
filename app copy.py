import os
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from functions import apology, get_vg_temperature

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)



def fetch_data_from_table(table_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data

def get_entropy(pressure):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT entropy_J_gK FROM PressureV WHERE pressure_bar = ?", (pressure,))
    data = cursor.fetchall()
    conn.close()
    return data



@app.route('/')
def properties():
    pressure_l_data = fetch_data_from_table('PressureL')
    pressure_v_data = fetch_data_from_table('PressureV')
    temperature_l_data = fetch_data_from_table('TemperatureL')
    temperature_v_data = fetch_data_from_table('TemperatureV')

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
        initial_entropy = get_entropy(pressure)
        return render_template("adibaticres.html" , entropy=initial_entropy)
    else:
        
        return render_template("adibatic.html")
        
