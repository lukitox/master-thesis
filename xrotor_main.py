"""Xrotor Test."""

# %%Import Libraries and Data

# Third-party imports
import numpy as np

# Local imports
from util_loads import Airfoil, Loadcase, Propeller, Xfoil, Xrotor

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

mh113 = Airfoil('mh113.txt', 250000)
mh113.set_polar(alpha_start=-20, alpha_stop=20, alpha_inc=0.25)

mh121 = Airfoil('mh121.txt', 500000)
mh121.set_polar(alpha_start=-20, alpha_stop=20, alpha_inc=0.25)

prop_mf3218.add_section(0.5, mh113)
prop_mf3218.add_section(1.0, mh121)

# %% Instantiate Loadcase

maxrpm = Loadcase('Max. Rpm', 1)
maxrpm.set_data('rpm', 4000)

power = Loadcase('power', 0.1)
maxthrust.set_data('powe', 1000, 'r', 2000)

prop_mf3218.add_loadcase(maxrpm)
prop_mf3218.add_loadcase(maxthrust)

# %% Run Xrotor

prop_mf3218.calc_loads()

# %% Play around

# oper_single_values = Prop_MF3218.loadcases['Max. RPM'].results['oper'][0]
# oper_tabular_data = Prop_MF3218.loadcases['Max. RPM'].results['oper'][1]
# bend_tabular_data = Prop_MF3218.loadcases['Max. RPM'].results['bend']

# # print(Prop_MF3218.loadcases)
# # print(Prop_MF3218)

# bend_tabular_data.plot(x='r/R', y=['Mz', 'Mx'])
# oper_tabular_data.plot(x='r/R', y=['CL', 'Cd'])
