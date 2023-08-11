# Functions used to interpolate
import numpy as np

from flask import redirect, render_template, session
from functools import wraps
'''
data = np.array([[0.5,81.3,3.239],
    [1,99.6,1.694],
    [10,179.9,0.1944],
    [20,212.4,0.09957],
    [40,250.3,0.04977],
    [100,311,0.01802],
    [150,342.1,0.01035],
    [180,357,0.00751],
    [200,365.7,0.00585],
    [220,373.7,0.00368]])

P_data = data[:,0]
Tsat_data = data[:,1]
vg_data = data[:,2]
'''
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def get_vg_temperature(T, P_data, Tsat_data):
    # Calculate specific volume using ideal gas equation, given Temperature
    # Assume given Temperature (do one for given Pressure?)
    # Assume given R&M table and need to interpolate to get Pressure if Temperature NOT in the table
    # numpy.interp(x, xp, fp)
    # x = x-coordinates at which to evaluate the interpolated values
    # xp = x-coordinates of the data points, must be increasing if the argument period is not specified
    # fp = y-coordinates of the data points, same length as xp
    P_bar = np.interp(T,Tsat_data,P_data)
    R = 461.5
    P_Pa = P_bar * 100000
    vg = R * (T+273.15) / P_Pa
    
    return vg

def get_vg_pressure(P, P_data, Tsat_data):
    T_C = np.interp(P, P_data, Tsat_data)
    R = 461.5
    T_K = T_C + 273.15
    # Convert P to Pa?
    Pa = P * 100000
    vg = R * T_K / Pa
    
    return vg

