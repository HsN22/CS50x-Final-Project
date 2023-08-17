import os
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functions import apology, get_vg_temperature, get_vg_Affandi, calc_error, get_h2, interpolate_press, Buck, Affandi_pressure, calc_error_pressure

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("sqlite:///databaseplus.db") # Using heated steam db

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

tempdict = db.execute("SELECT temperature_c FROM PressureL")
tuplesz = []
for i in tempdict:
    tuplesz.append(i["temperature_c"])


@app.route('/')
def properties():
    # Data from NIST website
    pressure_l_data = db.execute("SELECT * FROM PressureL")
    pressure_v_data = db.execute("SELECT * FROM PressureV")
    temperature_l_data = db.execute("SELECT * FROM TemperatureL")
    temperature_v_data = db.execute("SELECT * FROM TemperatureV")

    # Data from R&M tables

    return render_template('properties.html',
                           pressure_l_data=pressure_l_data,
                           pressure_v_data=pressure_v_data,
                           temperature_l_data=temperature_l_data,
                           temperature_v_data=temperature_v_data)

@app.route("/pressure", methods=["GET", "POST"])
def pressure():
    if request.method == "POST":
        temperature = request.form.get("temperature")
        try:
            T = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")
            
        if T <= 0:
            return apology("Temperature must be a positive number")

        pressure = interpolate_press(T, Tsat_data, P_data)
        buck_pressure = Buck(T)
        affandi_press = Affandi_pressure(T)

        temps = np.array(tuplesz)
        err1 = np.zeros_like(temps)
        err2 = np.zeros_like(temps)
        for i in np.arange(0,len(temps),1):
            err1[i], err2[i] = calc_error_pressure(temps[i], Tsat_data, P_data)
        import matplotlib.pyplot as plt
        plt.plot(temps,abs(err1),'ob-',temps,abs(err2),'^r-')
        plt.xlabel('Temperature [Celsius]')
        plt.ylabel('Error [%]')
        plt.gca().legend(('Arden Buck Method','Affandi et al. Method'))
        plt.savefig('static/error_graph_p.png')  # Save in the 'static' folder
        plt.close()  # Clear the figure

        return render_template("pressresult.html", pressure=pressure, buck_pressure=buck_pressure, affandi_press=affandi_press)
        #temps = np.array([81.3,99.6,179.9,212.4,250.3,311,342.1,357,365.7,373.7])
        
    else:
        return render_template("pressure.html")



@app.route("/specific", methods=["GET", "POST"])
def specific():
    if request.method == "POST":
        #Remember to validate users input, don't convert to float straight away
        temperature = request.form.get("temperature")

        # Check if user provides one input
        if not temperature:
            return apology("Enter a Temperature")

        try:
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")
            
        if temperature <= 0:
            return apology("Temperature must be a positive number")

        vg_dict = db.execute("SELECT volume_m3_kg FROM PressureV")
        hmm = []
        for j in vg_dict:
            hmm.append(j["volume_m3_kg"])
        vg_array = np.array(hmm)
        
        vg_data = vg_array

        vg_table = np.interp(temperature,Tsat_data,vg_data)
        v_g = get_vg_temperature(temperature, P_data, Tsat_data)
        affandi_v_g = get_vg_Affandi(temperature)

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
        return render_template("result.html",vg_table=vg_table, v = v_g, affandi_v_g = affandi_v_g)
                 
    else:
        return render_template("specific.html")


@app.route("/heated", methods=["GET", "POST"])
def heated():
    if request.method == "POST":
        # Get user input
        pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")

        # Check if the fields are empty
        if not pressure and not temperature:
            return apology("Enter both fields")

        # Check if the input are numbers
        try:
            pressure = float(pressure)
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature and pressure")

        # Is the data in the super heated table for interpolation to work?
        if (pressure >= 0 and pressure <= 4 and temperature >= 50) or (pressure >= 5 and temperature >= 200):
            # For the given pressure
            # Get the temperature of the immediate and previous of the users input
            # Get the volume of the corresponding immediate temp and the previous temp
            # Perform interpolation
            immediate_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
            previous_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
            next_temp = immediate_temp[0]["sat_T_c"]
            prev_temp = previous_temp[0]["sat_T_c"]
            immediate_v = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", next_temp, pressure)
            previous_v = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", prev_temp, pressure)
            next_v = immediate_v[0]["v"]
            prev_v = previous_v[0]["v"]
            v_interp = ((temperature - prev_temp) / (next_temp - prev_temp)) * (next_v - prev_v) + prev_v
            return render_template("resultstwo.html", next_temp=next_temp, prev_temp=prev_temp, next_v=next_v, prev_v=prev_v, v_interp=v_interp)
        else:
            return apology("The data entered are not in the super heated steam region")

    else:
        return render_template("heated.html")




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
        
