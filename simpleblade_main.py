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
from mpi4py import MPI


# Local imports
from util_loads import Propeller, Airfoil, Loadcase
from util_mapdl import Material
from propellermodel import PropellerModel

# %% Instantiate Airfoils and assign radial sections

mh112 = Airfoil('mh112.txt', 300000)
mh113 = Airfoil('mh113.txt', 300000)
mh114 = Airfoil('mh114.txt', 300000)
mh115 = Airfoil('mh115.txt', 500000)

sections = [[0.15, mh112],
            [0.30, mh113],
            [0.45, mh114],
            [0.60, mh115],
            [1.00, mh115]]

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

ansys_path_a = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS_a'
ansys_path_b = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS_b'

mapdl_a = pyansys.launch_mapdl(run_location=ansys_path_a,
                               nproc=2,
                               override=True,
                               loglevel='error',
                               additional_switches='-smp -d X11C',
                               allow_ignore=True,
                               mode='console',
                               )

mapdl_b = pyansys.launch_mapdl(run_location=ansys_path_b,
                               nproc=2,
                               override=True,
                               loglevel='error',
                               additional_switches='-smp -d X11C',
                               allow_ignore=True,
                               mode='console',
                               )


femodel_a = PropellerModel(mapdl_a,
                           mesh_density_factor=1,
                           propeller = propeller,
                           n_sec= 20,
                           )

femodel_b = PropellerModel(mapdl_a,
                           mesh_density_factor=1,
                           propeller = propeller,
                           n_sec= 20,
                           )


femodel_a.materials = {'flaxpreg': Material(mapdl_a, 'FLAXPREG-T-UD', 1),
                       'balsa': Material(mapdl_a, 'balsaholz', 2),
                     }

femodel_b.materials = {'flaxpreg': Material(mapdl_b, 'FLAXPREG-T-UD', 1),
                       'balsa': Material(mapdl_b, 'balsaholz', 2),
                     }

femodel_a.pre_processing()

femodel_b.__define_and_mesh_geometry__()
femodel_b.element_data = femodel_a.element_data
femodel_b.__apply_loads__()

mapdl_b.allsel('all')
mapdl_b.cdwrite('all', '_ansys_input_file', 'cdb')
mapdl_b.finish()
mapdl_b.clear('nostart')


# %% Define Objective function 

def objfunc(x):
    
    rank = MPI.COMM_WORLD.Get_rank()
    
    if rank == 0:
        f, g, h = femodel_a.evaluate(x)
    elif rank == 1:
        f, g, h = femodel_b.evaluate(x)
    else:
        raise ValueError('Rank does not exist.')
        
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
alpso = ALPSO(pll_type='SPM')
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
    
hotstart()
    
