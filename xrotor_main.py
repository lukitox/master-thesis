"""Xrotor Test."""

# %%Import Libraries and Data

# Third-party imports
import numpy as np

# Local imports
from util_loads import Airfoil, Loadcase, Propeller

# %% Instantiate Propeller

prop_mf3218 = Propeller(number_of_blades=2,
                        tip_radius=0.412,
                        hub_radius=0.04,
                        )

#                                r/R   c/R  beta
prop_mf3218.geometry = np.array([[0.17, 0.10, 17],
                                 [0.22, 0.14, 20],
                                 [0.27, 0.16, 18],
                                 [0.32, 0.15, 16],
                                 [0.37, 0.15, 15],
                                 [0.42, 0.14, 14],
                                 [0.47, 0.14, 13],
                                 [0.52, 0.13, 13],
                                 [0.57, 0.13, 12],
                                 [0.62, 0.12, 12],
                                 [0.67, 0.12, 11],
                                 [0.72, 0.11, 11],
                                 [0.77, 0.11, 11],
                                 [0.82, 0.10, 11],
                                 [0.87, 0.10, 10],
                                 [0.92, 0.09, 10],
                                 [0.97, 0.08, 7],
                                 [1.00, 0.01, 7],
                                 ])

mh112 = Airfoil('mh112.txt', 300000)
mh113 = Airfoil('mh113.txt', 300000)
mh114 = Airfoil('mh114.txt', 300000)
mh115 = Airfoil('mh115.txt', 500000)
mh116 = Airfoil('mh116.txt', 500000)
mh117 = Airfoil('mh117.txt', 500000)

prop_mf3218.sections = [[0.15, mh112],
                        [0.30, mh113],
                        [0.45, mh114],
                        [0.60, mh115],
                        [0.80, mh116],
                        [1.00, mh117]]

for airfoil in prop_mf3218.sections:
    airfoil[1].set_polar(alpha_start=-20, alpha_stop=20, alpha_inc=0.25) 


# %% Instantiate Loadcase

maxrpm = Loadcase('Max. Rpm', 1)
maxrpm.set_data('rpm', 4000)

power = Loadcase('power', 0.1)
power.set_data('powe', 1000, 'r', 2000)

prop_mf3218.add_loadcase(maxrpm)
prop_mf3218.add_loadcase(power)

# %% Run Xrotor

prop_mf3218.calc_loads()

# %% Calc Load envelope

prop_mf3218.set_load_envelope()

# %% Calc pressure Distribution

X, Y, Cp_suc, Cp_pres = prop_mf3218.pressure_distribution(0)

# %% Plot

import matplotlib.pyplot as plt

fig = plt.figure()
ax = plt.axes(projection='3d')

ax.plot_surface(X, Y, Cp_suc, cmap='viridis', edgecolor='none')
ax.set_title('Surface plot')
plt.show()

