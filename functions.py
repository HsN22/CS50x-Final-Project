# Functions used to interpolate
import numpy as np

from flask import redirect, render_template, session
from functools import wraps

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

def interpolate_temp(P, P_data, Tsat_data):

    T_C = np.interp(P, P_data, Tsat_data)

    return T_C

def interpolate_press(T,Tsat_data, P_data):

    P_bar = np.interp(T,Tsat_data, P_data)

    return P_bar




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

def get_vg_Affandi(T):
    
    a = -7.75883
    b = 3.23753
    c = 2.05755
    d = -0.06052
    e = 0.00529
    
    Tcrit = 647.096
    # Tr is the reduced temperature which is defined as T/Tcr. Tcr is critical temperature; for steam it is 647.096 K
    Tr = (T+273.15)/Tcrit   
    
    log_vg = a + b * (np.log(1/Tr))**0.4 + c/Tr**2 + d/Tr**4 + e/Tr**5
    
    vg = np.exp(log_vg)
    
    return vg

def calc_error(T, Tsat_data, vg_data, P_data):
    vg_table = np.interp(T,Tsat_data,vg_data)
    
    # Now get the data using the ideal gas method
    vg_idealgas = get_vg_temperature(T, P_data, Tsat_data)
    
    # Now get the data using the Affandi method
    vg_Affandi = get_vg_Affandi(T)
    
    # Now get the errors
    Error_ideal_gas = (100 * ( vg_table - vg_idealgas) / vg_table)
    Error_Affandi = (100 * ( vg_table - vg_Affandi) / vg_table)
    
    return Error_ideal_gas, Error_Affandi

def get_h2(pressurecalc, s_g, s_f, s_fg, h_f, h_g, h_fg):
    x = (pressurecalc - s_f) / s_fg
    h2 = h_f + x*h_fg
    return h2

