#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Local imports
from util_xrotor import util_xrotor as ux
from scipy.optimize import curve_fit

#%% Renerate some xfoil polar

filename = 'mh113_polar.txt'

with ux.xfoil() as x:
    x.run('load mh113.txt')
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
    
#%% Play around

colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46), (49, 55), (58, 64), (66, 73), (74, 82)]
tabular_data = pd.read_fwf(filename, colspecs=colspecs, header= [10], skiprows=[11])

# def func(x, x0, b, b2, c):
#     a = (c-b)/(x0**2)
#     m = 2*(c-b)/x0 + b2 # (2*a*x0 + b2)
#     return np.piecewise(x, [x < x0], [lambda x: m*x +b, lambda x: a * x**2 + b2 * x + c])

# def func(x, x0, x1, a1, a3, b1, c1):
#     c2 = -a1 * x0**2 + c1
#     b2 = 2 * a1 * x0**2 + b1
#     b3 = b2 - 2 * a3 * x1
#     c3 = b2 * x1 + c2 - a3 * x1**2 - b3 * x1
#     return np.piecewise(x, [x < x1, (x >= x1) & (x < x0), x >= x0 ], [lambda x: a1 * x**2 + b1 * x + c1,
#                                                                       lambda x: b2 * x + c2,
#                                                                       lambda x: a3 * x**3 + b3 * x + c3])

# def func(x, x0, x1, a1, a3, b1, b3, c3):
#     xx = np.sort([x0, x1])
#     # xx = [x0, x1]
#     b2 = 2*a3*xx[1] + b3
#     c2 = a3*xx[1]**2 + b3*xx[1] + c3 - b2*xx[1]
#     c1 = b2*xx[0] + c2 - a1*xx[0]**2 - b1*xx[0]
    
#     return np.piecewise(x, [x <xx[0], (x >=xx[0]) & (x <xx[1]), x >=xx[1] ], [lambda x: a1 * x**2 + b1 * x + c1,
#                                                                               lambda x: b2 * x + c2,
#                                                                               lambda x: a3 * x**3 + b3 * x + c3])

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



