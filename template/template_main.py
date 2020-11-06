"""
Main script of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import time
import numpy as np
import pyansys
from pyOpt import Optimization
from pyOpt import ALPSO


# Local imports
from template_femodel import Femodel
from util_loads import propeller, airfoil, loadcase

# %% Instantiate Airfoils and assign radial sections

airfoil1 = airfoil('mh113.txt', Re=250000, Ncrit=9, Iter=200)
airfoil2 = airfoil('mh121.txt', Re=500000, Ncrit=9, Iter=200)
# ...

sections = [# r/R, Airfoil
            [0.25, airfoil1],
            [1.00, airfoil2]]
# ...

for section in sections:   
    section[1].calculate_polar(alpha_start=-20,
                               alpha_stop=20,
                               alpha_inc=0.2)

# %% Instantiate Propeller and assign geometry and airfoils

propeller = propeller(number_of_blades=2,
                      tip_radius=0.412,
                      hub_radius=0.04,
                      )

propeller.geometry = np.array([[0.17, 0.10, 17],
                               [0.52, 0.13, 13],
                               [1.00, 0.08, 7]])
# ...

propeller.sections = sections

# %% Instantiate Loadcases

propeller.add_loadcase(name='Max. RPM',
                       loadcase=loadcase(flight_speed=0.01, rpm=4000))
# ...

# %% Calculate loads

for name in propeller.loadcases:
    with ux.xrotor(propeller=propeller, loadcase=name) as x:
        x.run('atmo 0')  
        x.arbi()  
        x.parse_airfoils()
        x.run('oper')  
        x.run('rpm ' + propeller.loadcases[name].parameters['rpm'])  # Todo: automatisieren
        x.write_oper()  
        x.run('') 
        x.run('bend')  
        x.run('eval')  
        x.write_bend()  
        x.run('')
        x.run('quit')


# %% Run ANSYS and instantiate FE-Model

ansys_path = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS'
mapdl = pyansys.launch_mapdl(run_location=ansys_path,
                             nproc=4,
                             override=True,
                             loglevel='error',
                             additional_switches='-smp -d WIN32C',
                             allow_ignore=True,
                             mode='console', # 'corba' on Windows 
                             )

femodel = Femodel(mapdl,
                  mesh_density_factor=1,
                  seltol=1e-4,
                  loads= propeller.loadcases # Todo: Load/ Propeller object
                  )

# %% Define Objective function 

def objfunc(x):
    f, g, h = femodel.evaluate(x)
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    print(np.round(time.time(),1), objfunc.counter, x)
    
    time.sleep(0.01)
    fail = 0
    
    return f, g, fail
objfunc.counter = 0

# %% Instantiate Optimization Problem 

optprob = Optimization(name='Propeller',
                       obj_fun= objfunc

# Add variables                        
optprob.addVar('y1','i',lower=4, upper=100, value=30)
# ...

# Add objective
opt_prob.addObj('f')

# Add constraints


