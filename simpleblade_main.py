"""
Main script of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pyansys
# from pyOpt import Optimization
# from pyOpt import ALPSO


# Local imports
from simpleblade_femodel import Femodel
from util_loads import Propeller, Airfoil, Loadcase

# %% Instantiate Airfoils and assign radial sections

mh112 = Airfoil('mh112.txt', 300000)
mh113 = Airfoil('mh113.txt', 300000)
mh114 = Airfoil('mh114.txt', 300000)
mh115 = Airfoil('mh115.txt', 500000)
# mh116 = Airfoil('mh116.txt', 500000)
# mh117 = Airfoil('mh117.txt', 500000)
# ...

sections = [[0.15, mh112],
            [0.30, mh113],
            [0.45, mh114],
            [0.60, mh115],
            [0.80, mh115],
            [1.00, mh115]]
# ...

# %% Instantiate Propeller and assign geometry and airfoils

propeller = Propeller(number_of_blades=2,
                      tip_radius=0.412,
                      hub_radius=0.04,
                      )

propeller.geometry = np.array([[0.17, 0.10, 17],
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
# ...

propeller.sections = sections

for airfoil in propeller.sections:
    airfoil[1].set_polar(alpha_start=-20, alpha_stop=20, alpha_inc=0.25) 

# %% Instantiate Loadcases

propeller.add_loadcase(loadcase=Loadcase(name='Max RPM', flight_speed=0.01))
# ...

propeller.loadcases[0][0].set_data('rpm',4000)
# ...

# %% Calculate loads

propeller.calc_loads()
propeller.set_load_envelope()

# %% Run ANSYS and instantiate FE-Model

ansys_path = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS'
mapdl = pyansys.launch_mapdl(run_location=ansys_path,
                             nproc=4,
                             override=True,
                             loglevel='error',
                             additional_switches='-smp -d X11C',
                             allow_ignore=True,
                             mode='console',
                             )

femodel = Femodel(mapdl,
                  mesh_density_factor=1,
                  seltol=1e-4,
                  propeller = propeller,
                  n_sec= 5, # propeller.loadcases # Todo: Load/ Propeller object
                  )

femodel.cdread()

global_vars = [45, -45, 0, 0, 0, -45, 45]

femodel.__change_design_variables__(global_vars,
                                    [0.74, 0.8, 0.5], 
                                    [0.74, 0.7, 0.5],
                                    [0.74, 0.6, 0.5],
                                    [0.74, 0.5, 0.5],
                                    [0.74, 0.4, 0.5])

# %% Define Objective function 

# def objfunc(x):
#     f, g, h = femodel.evaluate(x)
    
#     # Print current Function Evaluation for monitoring purpuses
#     objfunc.counter+= 1
#     print(np.round(time.time(),1), objfunc.counter, x)
    
#     time.sleep(0.01)
#     fail = 0
    
#     return f, g, fail
# objfunc.counter = 0

# # %% Instantiate Optimization Problem 

# optprob = Optimization(name='Propeller',
#                        obj_fun=objfunc
#                        )

# # Add variables                        
# optprob.addVar('y1','i',lower=4, upper=100, value=30)
# # ...

# # Add objective
# optprob.addObj('f')

# # Add constraints


