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



class PressureL(db.Model):
    __tablename__ = 'PressureL'
    id = db.Column(db.BIGINT, primary_key=True)
    pressure_bar = db.Column(db.FLOAT)
    temperature_c = db.Column(db.FLOAT)
    volume_m3_kg = db.Column(db.FLOAT)
    u_kJ_kg = db.Column(db.FLOAT)
    enthalpy_kJ_kg = db.Column(db.FLOAT)
    entropy_J_gK = db.Column(db.FLOAT)
    phase = db.Column(db.TEXT)

class PressureV(db.Model):
    __tablename__ = 'PressureV'
    id = db.Column(db.BIGINT, primary_key=True)
    pressure_bar = db.Column(db.FLOAT)
    temperature_c = db.Column(db.FLOAT)
    volume_m3_kg = db.Column(db.FLOAT)
    u_kJ_kg = db.Column(db.FLOAT)
    enthalpy_kJ_kg = db.Column(db.FLOAT)
    entropy_J_gK = db.Column(db.FLOAT)
    phase = db.Column(db.TEXT)

class TemperatureL(db.Model):
    __tablename__ = 'TemperatureL'
    id = db.Column(db.BIGINT, primary_key=True)
    temperature_c = db.Column(db.FLOAT)
    pressure_bar = db.Column(db.FLOAT)
    volume_m3_kg = db.Column(db.FLOAT)
    u_kJ_kg = db.Column(db.FLOAT)
    enthalpy_kJ_kg = db.Column(db.FLOAT)
    entropy_J_gK = db.Column(db.FLOAT)
    phase = db.Column(db.TEXT)

class TemperatureV(db.Model):
    __tablename__ = 'TemperatureV'
    id = db.Column(db.BIGINT, primary_key=True)
    temperature_c = db.Column(db.FLOAT)
    pressure_bar = db.Column(db.FLOAT)
    volume_m3_kg = db.Column(db.FLOAT)
    u_kJ_kg = db.Column(db.FLOAT)
    enthalpy_kJ_kg = db.Column(db.FLOAT)
    entropy_J_gK = db.Column(db.FLOAT)
    phase = db.Column(db.TEXT)


def fetch_data_from_table(table_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
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
def specific():
    pass