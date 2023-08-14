import os
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functions import apology, get_vg_temperature, get_vg_pressure, get_vg_Affandi, calc_error, get_h2, interpolate_temp, interpolate_press

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///database.db")

# Global
list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
# Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
# Remove every second item in list of tuples
data_tuples_filtered = data_tuples[::2]

# Convert the list of tuples to a numpy array
data_array = np.array(data_tuples_filtered)
P_data = data_array[:, 0]
Tsat_data = data_array[:, 1]

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


@app.route("/temperature", methods=["GET", "POST"])
def temperature():
    if request.method == "POST":
        pressure = request.form.get("pressure")
        P = float(pressure)
        
        #list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
        # Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
        #data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
        # Remove every second item in list of tuples
        #data_tuples_filtered = data_tuples[::2]

        # Convert the list of tuples to a numpy array
        #data_array = np.array(data_tuples_filtered)
        #P_data = data_array[:, 0]
        #Tsat_data = data_array[:, 1]

        temp = interpolate_temp(P, P_data, Tsat_data)
        return render_template("tempresult.html", temp=temp)
    
    else:
        return render_template("temperature.html")


@app.route("/pressure", methods=["GET", "POST"])
def pressure():
    if request.method == "POST":
        temperature = request.form.get("temperature")
        T = float(temperature)

        #list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
        # Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
        #data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
        # Remove every second item in list of tuples
        #data_tuples_filtered = data_tuples[::2]

        # Convert the list of tuples to a numpy array
        #data_array = np.array(data_tuples_filtered)
        #P_data = data_array[:, 0]
        #Tsat_data = data_array[:, 1]

        pressure = interpolate_press(T, Tsat_data, P_data)
        return render_template("pressresult.html", pressure=pressure)

    else:
        return render_template("pressure.html")



@app.route("/specific", methods=["GET", "POST"])
def specific():
    if request.method == "POST":
        #Remember to validate users input, don't convert to float straight away
        temperature = request.form.get("temperature")
        pressure = request.form.get("pressure")
        vg_dict = db.execute("SELECT volume_m3_kg FROM PressureV")
        hmm = []
        for j in vg_dict:
            hmm.append(j["volume_m3_kg"])
        vg_array = np.array(hmm)
        
        #Get T_sat_data and p_sat from database and convert to numpy array
        #list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
        # Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
        #data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
        # Remove every second item in list of tuples
        #data_tuples_filtered = data_tuples[::2]

        # Convert the list of tuples to a numpy array
        #data_array = np.array(data_tuples_filtered)
        #P_data = data_array[:, 0]
        #Tsat_data = data_array[:, 1]
        vg_data = vg_array

        # Check if user provides one input, not both or empty
        if (temperature and not pressure) or (pressure and not temperature):
            if temperature:
                temperature = float(temperature)
                v_g = get_vg_temperature(temperature, P_data, Tsat_data)
                affandi_v_g = get_vg_Affandi(temperature)

                tempdict = db.execute("SELECT temperature_c FROM PressureL")
                tuplesz = []
                for i in tempdict:
                    tuplesz.append(i["temperature_c"])
                #nparray = np.array(tuplesz)
                #print(nparray)

                temps = np.array(tuplesz)
                err1 = np.zeros_like(temps)
                err2 = np.zeros_like(temps)
                for i in np.arange(0,len(temps),1):
                    err1[i], err2[i] = calc_error(temps[i], Tsat_data, vg_data, P_data)
                
                plt.plot(temps,abs(err1),'ob-',temps,abs(err2),'^r-')
                plt.xlabel('Temperature [Celsius]')
                plt.ylabel('Error [%]')
                plt.gca().legend(('Ideal Gas Method','Affandi et al. Method'))
                # Save the graph as an image
                plt.savefig('static/error_graph.png')  # Save in the 'static' folder
                plt.close()  # Clear the figure
                
            else:
                pressure = float(pressure)
                v_g = get_vg_pressure(pressure, P_data, Tsat_data)
            return render_template("result.html", v = v_g, affandi_v_g = affandi_v_g)
        else:
            return apology("Enter either T or P, not both or empty")      
    else:
        return render_template("specific.html")


@app.route("/adibatic", methods=["GET", "POST"])
def adibatic():
    if request.method == "POST":
        pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")
        
        if not pressure or not temperature:
            return apology("Enter values for both temperature and pressure")
        
        try:
            pressure = float(pressure)
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature and pressure")
            
        if pressure <= 0 or temperature <= 0:
            return apology("Both temperature and pressure must be positive numbers")
        
        initial_entropy = db.execute("SELECT entropy_J_gK FROM PressureV WHERE pressure_bar = ?", pressure)

        # Get pressure from list of dictionaries
        for row in initial_entropy:
            pressurecalc = row["entropy_J_gK"]

        sf = db.execute("SELECT entropy_J_gK FROM TemperatureL WHERE temperature_c = ?", temperature)
        sg = db.execute("SELECT entropy_J_gK FROM TemperatureV WHERE temperature_c = ?", temperature)
        for row in sf:
            s_f = row["entropy_J_gK"]
        for row in sg:
            s_g = row["entropy_J_gK"]
        s_fg = s_g - s_f

        hf = db.execute("SELECT enthalpy_kJ_kg FROM TemperatureL WHERE temperature_c = ?", temperature)
        hg = db.execute("SELECT enthalpy_kJ_kg FROM TemperatureV WHERE temperature_c = ?", temperature)
        for row in hf:
            h_f = row["enthalpy_kJ_kg"]
        for row in hg:
            h_g = row["enthalpy_kJ_kg"]
        h_fg = h_g - h_f
        
        h2 = get_h2(pressurecalc, s_g, s_f, s_fg, h_f, h_g, h_fg)

        return render_template("adibaticres.html" , h2=h2)
        
    
    else:
        return render_template("adibatic.html")
        
