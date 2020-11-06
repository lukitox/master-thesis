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

# Local imports
from template_femodel import Femodel

# %% Instantiate Propeller and calculate Loads

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
                  loads= [] # Load/ Propeller object
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
