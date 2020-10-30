#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.signal


# Local imports
from util_xrotor import util_xrotor as ux

#%% Generate some xfoil polar

filename = 'mh113_polar.txt'

with ux.xfoil() as x:
    x.run('load ./util_loads/airfoil-database/mh113.txt')
    x.run('pane')
    x.run('oper')
    x.run('vpar')
    x.run('n 9')
    x.run('')
    x.run('visc 500000')
    x.run('iter')
    x.run('400')
    x.run('pacc')
    x.run(filename)
    x.run('')
    x.run('aseq -20 20 0.25')
    x.run('')
    x.run('quit')
    
#%% Read Xfoil 

colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46), (49, 55), (58, 64), (66, 73), (74, 82)]
tabular_data = pd.read_fwf(filename, colspecs=colspecs, header= [10], skiprows=[11])

def func(x, x0, x1, a3, b1, b3, c2):
    b2 = 2*a3*x1 + b3
    c1 = b2*x0 - b1*x0 + c2
    c3 = b2*x1 + c2 - a3*x1**2 - b3*x1
    return np.piecewise(x, [x < x0, (x >= x0) & (x < x1), x > x1], [lambda x: b1*x + c1,
                                                                    lambda x: b2*x + c2,
                                                                    lambda x: a3*x**2 + b3*x + c3])
    
xdata = np.array(tabular_data['alpha'])
ydata = np.array(tabular_data['CL']) 

popt, pcov = curve_fit(func, xdata, ydata)

plt.plot(xdata, func(xdata, *popt))
plt.plot(tabular_data['alpha'], tabular_data['CL'])

data = np.transpose(np.array([np.arange(-20, 20, 0.25), func(np.arange(-20, 20, 0.25), *popt)]))

ca_alpha = 2*popt[2]*popt[1]+popt[4] * 180 / 3.141
ca_max = max(data[:,1])
ca_0 = -popt[5] / (2*popt[2]*popt[1]+popt[4])
ca_min = float(func(popt[0], *popt))


filtered_cd = scipy.signal.savgol_filter(tabular_data['CD'], window_length=11, polyorder=2)


tabular_data.plot(x='CL',y='CD')
dcd_dcl = np.gradient(np.gradient(filtered_cd, tabular_data['CL']), tabular_data['CL'])
plt.plot(ydata, dcd_dcl)


arr = np.transpose(np.array([tabular_data['CL'], dcd_dcl]))
