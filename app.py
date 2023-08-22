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

# Using heated steam db
db = SQL("sqlite:///databaseplus.db") 

# Global variables
list_of_dictionaries = db.execute("SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureV UNION SELECT pressure_bar, temperature_c, volume_m3_kg FROM PressureL")
# Convert the list of dictionaries to a list of tuples (Tsat, Pressure)
data_tuples = [(item['pressure_bar'], item['temperature_c'], item['volume_m3_kg']) for item in list_of_dictionaries]
# Remove every second item in list of tuples
data_tuples_filtered = data_tuples[::2]

# Convert the list of tuples to a numpy array
data_array = np.array(data_tuples_filtered)
P_data = data_array[:, 0]
Tsat_data = data_array[:, 1]

# To convert to a numpy array later
tempdict = db.execute("SELECT temperature_c FROM PressureL")
tuplesz = []
for i in tempdict:
    tuplesz.append(i["temperature_c"])


@app.route('/')
def home():
    # Homepage
    return render_template("home.html")


@app.route('/properties')
def properties():
    # Data from NIST website
    pressure_l_data = db.execute("SELECT * FROM PressureL")
    pressure_v_data = db.execute("SELECT * FROM PressureV")
    temperature_l_data = db.execute("SELECT * FROM TemperatureL")
    temperature_v_data = db.execute("SELECT * FROM TemperatureV")

    # Data from R&M tables
    super_data = db.execute("SELECT * FROM super_heated_steam")
    critical_data = db.execute("SELECT * FROM critical_heated_steam")

    return render_template('properties.html',
                           pressure_l_data=pressure_l_data,
                           pressure_v_data=pressure_v_data,
                           temperature_l_data=temperature_l_data,
                           temperature_v_data=temperature_v_data,
                           super_data=super_data,
                           critical_data=critical_data)


@app.route("/pressure", methods=["GET", "POST"])
def pressure():
    if request.method == "POST":
        # Get user input
        temperature = request.form.get("temperature")
        # Check if input is a positive number
        try:
            T = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")
            
        if T <= 0:
            return apology("Temperature must be a positive number")

        # Call upon calculations functions
        pressure = interpolate_press(T, Tsat_data, P_data)
        Buck_pressure = Buck(T)
        Affandi_press = Affandi_pressure(T)

        # Create an error graph
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
        # Save in the 'static' folder
        plt.savefig('static/error_graph_p.png')  
        plt.close()

        return render_template("pressresult.html", pressure=pressure, Buck_pressure=Buck_pressure, Affandi_press=Affandi_press)
    else:
        return render_template("pressure.html")


@app.route("/specific", methods=["GET", "POST"])
def specific():
    if request.method == "POST":
        # Get user input
        temperature = request.form.get("temperature")

        # Check if user provides an input
        if not temperature:
            return apology("Enter a Temperature")

        # Check if input is a positive number
        try:
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")
            
        if temperature <= 0:
            return apology("Temperature must be a positive number")

        # Create a specific volume numpy array
        vg_dict = db.execute("SELECT volume_m3_kg FROM PressureV")
        hmm = []
        for j in vg_dict:
            hmm.append(j["volume_m3_kg"])
        vg_data = np.array(hmm)

        # Call upon calculation functions, pass in user input and numpy arrays
        # Steam table method
        vg_table = np.interp(temperature,Tsat_data,vg_data)
        # Ideal gas method
        v_g = get_vg_temperature(temperature, P_data, Tsat_data)
        # Affandi method
        affandi_v_g = get_vg_Affandi(temperature)

        # Create an error graph
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
        # Save in the 'static' folder
        plt.savefig('static/error_graph.png')  
        plt.close()
        return render_template("result.html",vg_table=vg_table, v = v_g, affandi_v_g = affandi_v_g) 
    else:
        return render_template("specific.html")

def get_immediate_and_previous_temps(table_name, pressure, temperature):
    immediate_temp = db.execute(
        "SELECT sat_T_c FROM ? WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1",
        table_name, pressure, temperature
    )
    previous_temp = db.execute(
        "SELECT sat_T_c FROM ? WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1",
        table_name, pressure, temperature
    )
    next_temp = immediate_temp[0]["sat_T_c"]
    prev_temp = previous_temp[0]["sat_T_c"]
    return next_temp, prev_temp

@app.route("/heated", methods=["GET", "POST"])
def heated():
    if request.method == "POST":
        # Get user input
        selection = request.form.get("calcType")
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
        # For the given pressure
        # Get the temperature of the immediate and previous of the users input
        # Get the volume of the corresponding immediate temp and the previous temp
        # Perform interpolation
        # Temps, already in table, no need for interpolation, simply output the value
        # existing_temps = [50, 100, 150, 200, 250, 300, 350, 375, 400, 425, 450, 500, 550, 600, 700, 800]

        super_heated_data = db.execute("SELECT p, sat_T_c, v, u, h, s FROM super_heated_steam")
        critical_heated_data = db.execute("SELECT p, sat_T_c, v, h, s FROM critical_heated_steam")
        combined = super_heated_data + critical_heated_data

        # Check if pressure input is in the table, if it is not, output error
        pressure_values = []
        for row in combined:
            pressure_values.append(row["p"])
        
        if pressure not in pressure_values:
            return apology("Need to interpolate Pressure or it does not exist in the table")

        # Specific volume interpolater
        if selection == "specific_volume":
            # Check if temperature and associated data exits in table, if so, output them
            vol = None
            for i in combined:
                if i["sat_T_c"] == temperature and i["p"] == pressure:
                    vol = i["v"]
                    break
            if vol is not None:
                return render_template("resultstwoexisting.html", v_exists=vol)
            if (pressure >= 0 and pressure <= 4 and temperature >= 50 and temperature not in unacceptable) or (pressure >= 5 and pressure <= 221.2 and temperature >= 200):
                next_temp, prev_temp = get_immediate_and_previous_temps("super_heated_steam", pressure, temperature)
                #immediate_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_temp = immediate_temp[0]["sat_T_c"]
                #prev_temp = previous_temp[0]["sat_T_c"]
                immediate_v = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", next_temp, pressure)
                previous_v = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", prev_temp, pressure)
                next_v = immediate_v[0]["v"]
                prev_v = previous_v[0]["v"]
                v_interp = ((temperature - prev_temp) / (next_temp - prev_temp)) * (next_v - prev_v) + prev_v
                return render_template("resultstwo.html", next_temp=next_temp, prev_temp=prev_temp, next_v=next_v, prev_v=prev_v, v_interp=v_interp)
            elif (pressure >= 225 and pressure <= 1000 and temperature >= 350):
                next_tempsc, prev_tempsc = get_immediate_and_previous_temps("critical_heated_steam", pressure, temperature)
                #immediate_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_tempsc = immediate_tempsc[0]["sat_T_c"]
                #prev_tempsc = previous_tempsc[0]["sat_T_c"]
                immediate_vsc = db.execute("SELECT v FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", next_tempsc, pressure)
                previous_vsc = db.execute("SELECT v FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", prev_tempsc, pressure)
                next_vsc = immediate_vsc[0]["v"]
                prev_vsc = previous_vsc[0]["v"]
                v_interpsc = ((temperature - prev_tempsc) / (next_tempsc - prev_tempsc)) * (next_vsc - prev_vsc) + prev_vsc
                return render_template("resultstwosc.html", next_tempsc=next_tempsc, prev_tempsc=prev_tempsc, next_vsc=next_vsc, prev_vsc=prev_vsc, v_interpsc=v_interpsc)
            else:
                return apology("The data entered are not in the super heated steam or critical heated region")
        # Internal energy interpolater
        elif selection == "internal_energy":
            # u does not exist in critical region table so avoid it
            u = None
            # Check if interpolation is necessary
            for i in super_heated_data:
                if i["sat_T_c"] == temperature and i["p"] == pressure:
                    u = i["u"]
                    break
            if u is not None:
                return render_template("uresultexist.html", u_exists=u)
            if (pressure >= 0 and pressure <= 4 and temperature >= 50) or (pressure >= 5 and pressure <= 70 and temperature >= 200):
                next_temp, prev_temp = get_immediate_and_previous_temps("super_heated_steam", pressure, temperature)
                #immediate_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_temp = immediate_temp[0]["sat_T_c"]
                #prev_temp = previous_temp[0]["sat_T_c"]
                immediate_u = db.execute("SELECT u FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", next_temp, pressure)
                previous_u = db.execute("SELECT u FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", prev_temp, pressure)
                next_u = immediate_u[0]["u"]
                prev_u = previous_u[0]["u"]
                u_interp = ((temperature - prev_temp) / (next_temp - prev_temp)) * (next_u - prev_u) + prev_u
                return render_template("uresultstwo.html", next_temp=next_temp, prev_temp=prev_temp, next_u=next_u, prev_u=prev_u, u_interp=u_interp)
            elif (pressure >= 80 and pressure <= 1000 and temperature >= 350):
                return apology("There is no u in the from 80 bar in the super heated region and in critical heated region")
            else:
                return apology("The data entered are not in the super heated steam or critical heated region")
        # Specific enthalpy interpolater
        elif selection == "specific_enthalpy":
            h = None
            # Check if interpolation is necessary
            for i in combined:
                if i["sat_T_c"] == temperature and i["p"] == pressure:
                    h = i["h"]
                    break
            if h is not None:
                return render_template("hresultexist.html", h_exists=h)
            if (pressure >= 0 and pressure <= 4 and temperature >= 50) or (pressure >= 5 and pressure <= 221.2 and temperature >= 200):
                next_temp, prev_temp = get_immediate_and_previous_temps("super_heated_steam", pressure, temperature)
                #immediate_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_temp = immediate_temp[0]["sat_T_c"]
                #prev_temp = previous_temp[0]["sat_T_c"]
                immediate_h = db.execute("SELECT h FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", next_temp, pressure)
                previous_h = db.execute("SELECT h FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", prev_temp, pressure)
                next_h = immediate_h[0]["h"]
                prev_h = previous_h[0]["h"]
                h_interp = ((temperature - prev_temp) / (next_temp - prev_temp)) * (next_h - prev_h) + prev_h
                return render_template("hresultstwo.html", next_temp=next_temp, prev_temp=prev_temp, next_h=next_h, prev_h=prev_h, h_interp=h_interp)
            elif (pressure >= 225 and pressure <= 1000 and temperature >= 350):
                next_tempsc, prev_tempsc = get_immediate_and_previous_temps("critical_heated_steam", pressure, temperature)
                #immediate_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_tempsc = immediate_tempsc[0]["sat_T_c"]
                #prev_tempsc = previous_tempsc[0]["sat_T_c"]
                immediate_hsc = db.execute("SELECT h FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", next_tempsc, pressure)
                previous_hsc = db.execute("SELECT h FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", prev_tempsc, pressure)
                next_hsc = immediate_hsc[0]["h"]
                prev_hsc = previous_hsc[0]["h"]
                h_interpsc = ((temperature - prev_tempsc) / (next_tempsc - prev_tempsc)) * (next_hsc - prev_hsc) + prev_hsc
                return render_template("hresultstwosc.html", next_tempsc=next_tempsc, prev_tempsc=prev_tempsc, next_hsc=next_hsc, prev_hsc=prev_hsc, h_interpsc=h_interpsc)
        # Specific entropy interpolater  
        elif selection == "specific_entropy":
            s = None
            # Check if interpolation is necessary
            for i in combined:
                if i["sat_T_c"] == temperature and i["p"] == pressure:
                    s = i["s"]
                    break
            if s is not None:
                return render_template("sresultexist.html", s_exists=s)
            if (pressure >= 0 and pressure <= 4 and temperature >= 50) or (pressure >= 5 and pressure <= 221.2 and temperature >= 200):
                next_temp, prev_temp = get_immediate_and_previous_temps("super_heated_steam", pressure, temperature)
                #immediate_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_temp = db.execute("SELECT sat_T_c FROM super_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_temp = immediate_temp[0]["sat_T_c"]
                #prev_temp = previous_temp[0]["sat_T_c"]
                immediate_s = db.execute("SELECT s FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", next_temp, pressure)
                previous_s = db.execute("SELECT s FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", prev_temp, pressure)
                next_s = immediate_s[0]["s"]
                prev_s = previous_s[0]["s"]
                s_interp = ((temperature - prev_temp) / (next_temp - prev_temp)) * (next_s - prev_s) + prev_s
                return render_template("hresultstwo.html", next_temp=next_temp, prev_temp=prev_temp, next_s=next_s, prev_s=prev_s, s_interp=s_interp)
            elif (pressure >= 225 and pressure <= 1000 and temperature >= 350):
                next_tempsc, prev_tempsc = get_immediate_and_previous_temps("critical_heated_steam", pressure, temperature)
                #immediate_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1", pressure, temperature)
                #previous_tempsc = db.execute("SELECT sat_T_c FROM critical_heated_steam WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1", pressure, temperature)
                #next_tempsc = immediate_tempsc[0]["sat_T_c"]
                #prev_tempsc = previous_tempsc[0]["sat_T_c"]
                immediate_ssc = db.execute("SELECT s FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", next_tempsc, pressure)
                previous_ssc = db.execute("SELECT s FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", prev_tempsc, pressure)
                next_ssc = immediate_ssc[0]["s"]
                prev_ssc = previous_ssc[0]["s"]
                s_interpsc = ((temperature - prev_tempsc) / (next_tempsc - prev_tempsc)) * (next_ssc - prev_ssc) + prev_ssc
                return render_template("sresultstwosc.html", next_tempsc=next_tempsc, prev_tempsc=prev_tempsc, next_ssc=next_ssc, prev_ssc=prev_ssc, s_interpsc=s_interpsc)
        else:
            return apology("Not a valid selection")
    else:
        return render_template("heated.html")

'''
def get_immediate_and_previous_press(table_name, pressure, temperature):
    immediate_temp = db.execute(
        #"SELECT sat_T_c FROM ? WHERE p = ? AND sat_T_c > ? ORDER BY sat_T_c LIMIT 1",
        table_name, pressure, temperature
    )
    previous_temp = db.execute(
        #"SELECT sat_T_c FROM ? WHERE p = ? AND sat_T_c < ? ORDER BY sat_T_c DESC LIMIT 1",
        table_name, pressure, temperature
    )
    next_temp = immediate_temp[0]["sat_T_c"]
    prev_temp = previous_temp[0]["sat_T_c"]
    return next_temp, prev_temp
'''

@app.route("/heatedtwo", methods=["GET", "POST"])
def heatedtwo():
    if request.method == "POST":
        # Get user input of pressure and temperature
        # Validate input
        # Find for a given temperature the immediate pressure and the previous pressure
        # Find for a given temperature AND those pressures selected, the thermodynamic properties
        # Perform linear interpolation

        # Get user input
        selection = request.form.get("calcType")
        # This changes in HTML form so make it dynamic later
        
        #pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")

        # Check if the temp field is empty
        if not temperature:
            return apology("Enter both fields")
        # Check if the input are numbers
        try:
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")

        # Duplicate from heated()
        super_heated_data = db.execute("SELECT p, sat_T_c, v, u, h, s FROM super_heated_steam")
        #critical_heated_data = db.execute("SELECT p, sat_T_c, v, h, s FROM critical_heated_steam")
        #combined = super_heated_data + critical_heated_data

        valid_super_temps = []
        for a in super_heated_data:
            valid_super_temps.append(a["sat_T_c"])

        all_v = []
        for b in super_heated_data:
            all_v.append(b["v"])
        filtered_v = [value for value in all_v if value is not None]

        if filtered_v:
            smallest_v = min(filtered_v)
            largest_v = max(filtered_v)
        else:
            # print("The list 'all_v' contains None values or is empty.")
            return apology("Error")

        if selection == "specific_volume":
            # Check if input is a number and positive
            thermodynamic_property = request.form.get("specificVolume")
            try:
                thermodynamic_property = float(thermodynamic_property)
            except ValueError:
                return apology("Enter a number")
            if thermodynamic_property < 0:
                return apology("Specific volume must be positive")

            # Does the value of specific volume already correspond to a pressure in the table?
            ### Need to also handle the case where v exists but not at the right temperature ###
            # Handle the case where only valid temps are allowed...crosslink between temperature interpolater?
            # Handle the None case

            p_exists = None
            for i in super_heated_data:
                if i["v"] == thermodynamic_property and i["sat_T_c"] == temperature:
                    p_exists = i["p"]
                    break
            if p_exists is not None:
                return render_template("pressureexists.html", p_exists=p_exists)

            if thermodynamic_property >= smallest_v and thermodynamic_property <= largest_v:
                if temperature in valid_super_temps:
                    pressureone = db.execute("SELECT p FROM super_heated_steam WHERE sat_T_c = ? AND v < ? ORDER BY p LIMIT 1", temperature, thermodynamic_property)
                    pressurezero = db.execute("SELECT p FROM super_heated_steam WHERE sat_T_c = ? AND v > ? ORDER BY p DESC LIMIT 1", temperature, thermodynamic_property)
                    # Check for None v
                    if pressureone:
                        p_one = pressureone[0]["p"]
                    else:
                        return apology("No pressure for the specificed temperature and specifc volume")
                    if pressurezero:
                        p_zero = pressurezero[0]["p"]
                    else:
                        return apology("No pressure for the specificed temperature and specifc volume")
                    specific_volume_one = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", temperature, p_one)
                    specific_volume_zero = db.execute("SELECT v FROM super_heated_steam WHERE sat_T_c = ? AND p = ?", temperature, p_zero)
                    v_one = specific_volume_one[0]["v"]
                    v_zero = specific_volume_zero[0]["v"]
                    p_interp = ((thermodynamic_property - v_zero) / (v_one - v_zero)) * (p_one - p_zero) + p_zero
                    return render_template("pressureinterp.html", p_interp=p_interp, thermodynamic_property=thermodynamic_property, v_one=v_one, v_zero=v_zero, p_one=p_one, p_zero=p_zero)
                else:
                    return apology("Not a valid temperature, perhaps use the Linear Temperature Interpolater first?")
        else:
            return apology("TODO")
    else:    
        return render_template("heatedtwo.html")


@app.route("/heatedtwosc", methods=["GET", "POST"])
def heatedtwosc():
    if request.method == "POST":
        # Get user input of pressure and temperature
        # Validate input
        # Find for a given temperature the immediate pressure and the previous pressure from the SUPERCRITICAL table
        # Find for a given temperature AND those pressures selected, the thermodynamic properties from the SUPERCRITICAL table
        # Perform linear interpolation

        # Get user input
        selection = request.form.get("calcType")
        # This changes in HTML form so make it dynamic later
        
        #pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")

        # Check if the temp field is empty
        if not temperature:
            return apology("Enter both fields")
        # Check if the input are numbers
        try:
            temperature = float(temperature)
        except ValueError:
            return apology("Enter valid positive numbers for temperature")

        # Duplicate from heated()
        critical_heated_data = db.execute("SELECT p, sat_T_c, v, h, s FROM critical_heated_steam")
    

        valid_critical_temps = []
        for a in critical_heated_data:
            valid_critical_temps.append(a["sat_T_c"])

        all_v = []
        for b in critical_heated_data:
            all_v.append(b["v"])
        filtered_v = [value for value in all_v if value is not None]

        if filtered_v:
            smallest_v = min(filtered_v)
            largest_v = max(filtered_v)
        else:
            # print("The list 'all_v' contains None values or is empty.")
            return apology("Error")
        

        if selection == "specific_volume":
            # Check if input is a number and positive
            thermodynamic_property = request.form.get("specificVolume")
            try:
                thermodynamic_property = float(thermodynamic_property)
            except ValueError:
                return apology("Enter a number")
            if thermodynamic_property < 0:
                return apology("Specific volume must be positive")

            # Does the value of specific volume already correspond to a pressure in the table?
            ### Need to also handle the case where v exists but not at the right temperature ###
            # Handle the case where only valid temps are allowed...crosslink between temperature interpolater?
            # Handle the None case

            p_exists = None
            for i in critical_heated_data:
                if i["v"] == thermodynamic_property and i["sat_T_c"] == temperature:
                    p_exists = i["p"]
                    break
            if p_exists is not None:
                return render_template("pressureexistssc.html", p_exists=p_exists)            

            if thermodynamic_property >= smallest_v and thermodynamic_property <= largest_v:
                if temperature in valid_critical_temps:
                    pressureone = db.execute("SELECT p FROM critical_heated_steam WHERE sat_T_c = ? AND v < ? ORDER BY p LIMIT 1", temperature, thermodynamic_property)
                    pressurezero = db.execute("SELECT p FROM critical_heated_steam WHERE sat_T_c = ? AND v > ? ORDER BY p DESC LIMIT 1", temperature, thermodynamic_property)
                    # Check for None values
                    if pressureone:
                        p_one = pressureone[0]["p"]
                    else:
                        return apology("No pressure for the specificed temperature and specifc volume")
                    if pressurezero:
                        p_zero = pressurezero[0]["p"]
                    else:
                        return apology("No pressure for the specificed temperature and specifc volume")
                    specific_volume_one = db.execute("SELECT v FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", temperature, p_one)
                    specific_volume_zero = db.execute("SELECT v FROM critical_heated_steam WHERE sat_T_c = ? AND p = ?", temperature, p_zero)
                    v_one = specific_volume_one[0]["v"]
                    v_zero = specific_volume_zero[0]["v"]
                    p_interp = ((thermodynamic_property - v_zero) / (v_one - v_zero)) * (p_one - p_zero) + p_zero
                    return render_template("pressureinterp.html", p_interp=p_interp, thermodynamic_property=thermodynamic_property, v_one=v_one, v_zero=v_zero, p_one=p_one, p_zero=p_zero) 
                else:
                    return apology("Not a valid temperature, perhaps use the Linear Temperature Interpolater first?")
            else:
                return apology("Specific volume for specified temperature does not exist in tables, with our without interpolation")
        else:
            return apology("TODO")
    else:
        return render_template("heatedtwosc.html")



@app.route("/adibatic", methods=["GET", "POST"])
def adibatic():
    if request.method == "POST":
        # Get user input
        pressure = request.form.get("pressure")
        temperature = request.form.get("temperature")
        
        # Make sure both fields are not empty
        if not pressure or not temperature:
            return apology("Enter values for both temperature and pressure")
        
        # Make sure positive numbers are entered
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
        
        # Call upon final specific enthalpy calculater function
        h2 = get_h2(pressurecalc, s_g, s_f, s_fg, h_f, h_g, h_fg)

        return render_template("adibaticres.html" , h2=h2)
    else:
        return render_template("adibatic.html")