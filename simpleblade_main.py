"""
Main script of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pyansys
from pyOpt import Optimization
from pyOpt import ALPSO
import time

# Local imports
from util_loads import Propeller, Airfoil, Loadcase
from util_mapdl import Material
from propellermodel import PropellerModel

# %% Instantiate Airfoils and assign radial sections

airfoil = Airfoil('mf3218.xfo', 350000)

sections = [[0.121, airfoil],
            [1., airfoil]]


# %% Instantiate Propeller and assign geometry and airfoils

propeller = Propeller(number_of_blades=2,
                      tip_radius=0.412,
                      hub_radius=0.04,
                      )

propeller.geometry = np.array([[0.121, 0.078, 0.],
                               [0.155, 0.100, 5.99],
                               [0.223, 0.160, 17.97],
                               [0.345, 0.149, 14.44],
                               [0.417, 0.142, 12.68],
                               [0.490, 0.135, 11.18],
                               [0.563, 0.128, 9.94],
                               [0.636, 0.121, 8.97],
                               [0.709, 0.114, 8.26],
                               [0.782, 0.107, 7.81],
                               [0.854, 0.100, 7.63],
                               [0.947, 0.091, 7.5],
                               [1., 0.066, 7.5],                               
                               ])

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

femodel = PropellerModel(mapdl,
                         mesh_density_factor=1,
                         propeller = propeller,
                         n_sec= 20,
                         )

femodel.materials = {'flaxpreg': Material(mapdl,
                                          'FLAXPREG-T-UD',
                                          1),
                     'balsa': Material(mapdl,
                                       'balsaholz',
                                       2),
                     }

femodel.pre_processing()


# %% Define Objective function 

def objfunc(x):
    f, g, h = femodel.evaluate(x)
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    print(np.round(time.time(),1), objfunc.counter, np.round(np.array(x),2))
    
    time.sleep(0.01)
    fail = 0
    
    return f, g, fail
objfunc.counter = 0

# %% Instantiate Optimization Problem 

optprob = Optimization(name='Propeller',
                        obj_fun=objfunc
                        )

# Add variables
for i in range(7):                        
    optprob.addVar('phi' + str(i), 'c', lower=-100, upper=100)
for i in range (20):
    optprob.addVar('tpm' + str(i), 'c', lower=0.185 * 2, upper=0.185 * 8)
    optprob.addVar('rho' + str(i), 'c', lower=0., upper=1.)
    optprob.addVar('div' + str(i), 'c', lower=0.1, upper= 0.9)

# Add objective
optprob.addObj('f')

# Add constraints
for i in range(20): 
    optprob.addCon('gf' + str(i), 'i')
# Add constraints
for i in range(20): 
    optprob.addCon('gm' + str(i), 'i')

# %% Instantiate Optimizer
alpso = ALPSO()
alpso.setOption('fileout',1)

alpso_path = "/home/y0065120/Dokumente/Leichtwerk/Projects/ALPSO/"
filename = 'Simpleblade_Output_ALPSO'

alpso.setOption('filename', alpso_path+filename)
alpso.setOption('SwarmSize', 40)
alpso.setOption('stopIters', 5)      
alpso.setOption('rinit', 1.)
alpso.setOption('itol', 0.01)

def coldstart():    
    alpso(optprob, store_hst=True)
    print(optprob.solution(0))
    
def hotstart():
    alpso.setOption('filename',filename + '_hotstart')
    alpso(optprob, store_hst=True, hot_start= alpso_path+filename)
    print(optprob.solution(0)) # 0 or 1?
