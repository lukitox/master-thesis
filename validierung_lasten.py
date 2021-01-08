#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 10:26:03 2021

@author: y0065120
"""

import matplotlib.pyplot as plt
import numpy as np

bend = propeller.loadcases[0][1]['bend']

# %% Biegemoment

bendplot = bend.plot(x='r/R', y='Mz', style='.')

Mz = [[0], [25.702]]

plt.plot(Mz[0],Mz[1], axes=bendplot, marker='o')

rR = np.linspace(0,1,100)
polybend = np.polyfit(bend['r/R'], bend['Mz'], 3)

Mz_fit = np.polyval(polybend, rR)

plt.plot(rR, Mz_fit, axes=bendplot)

difference = Mz[1]/Mz_fit[0]

# %% Schwenkmoment

schwenkplot = bend.plot(x='r/R', y='Mx', style='.-')

Mx = [[0], [3.233]]

plt.plot(Mx[0],Mx[1], axes=schwenkplot, marker='o')

poly = np.polyfit(bend['r/R'], bend['Mx'], 3)

Mx_fit = np.polyval(poly, rR)

plt.plot(rR, Mx_fit, axes=schwenkplot)

difference = Mx[1]/Mx_fit[0]

# %% Torsionsmoment

torsplot = bend.plot(x='r/R', y='T', style='.-')