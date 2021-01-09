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
import pandas as pd

# Local imports
from util_loads import Propeller, Airfoil, Loadcase
from util_mapdl import Material
from propellermodel import PropellerModel

rank = MPI.COMM_WORLD.Get_rank()

# %% Instantiate Airfoils and assign radial sections

airfoil = Airfoil('mf3218.xfo', 500000, iter_limit=600)
airfoildick = Airfoil('mf3218-dick.xfo', 500000, iter_limit=600)
rectangle = Airfoil('rectangle2.txt',500000)

# %% Instantiate Propeller and assign geometry and airfoils

propeller = Propeller(number_of_blades=2,
                      tip_radius=0.412,
                      hub_radius=0.04,
                      )

propeller.geometry = np.array([[0.10,0.078,0],
                               [0.121, 0.078, 0.],
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

propeller.sections = [[0.121, airfoil],
                      [0.223, airfoil],
                      [1., airfoil]]

propeller.geometric_sections = [[0.121, rectangle],
                                [0.223, airfoildick],
                                [1., airfoildick]]

# for x in propeller.sections:
#     x[1].set_polar(alpha_start=-7, alpha_stop=20, alpha_inc=0.25) 
    
# airfoil.xrotor_characteristics['Cm'] = -0.14
# airfoil.xrotor_characteristics['d(Cl)/d(alpha)'] = 6.28
# airfoil.xrotor_characteristics['Minimum Cl'] = 0.



# %% Instantiate Loadcases

propeller.add_loadcase(loadcase=Loadcase(name='Max RPM', flight_speed=0.01))
# ...

propeller.loadcases[0][0].set_data('rpm',4000)
# ...

# %% Calculate loads

# propeller.calc_loads()
# propeller.set_load_envelope()

# %% Run ANSYS and instantiate FE-Model

nproc = 4

ansys_path = ['/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-a/',
              '/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-b/',
              '/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-c/',
              '/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-d/']

jobname = ['job-a', 'job-b', 'job-c', 'job-d']

mapdl = [[] for i in range(nproc)]

mapdl[rank] = pyansys.launch_mapdl(run_location=ansys_path[rank],
                                   nproc=1,
                                   override=True,
                                   loglevel='error',
                                   additional_switches='-smp -d X11C',
                                   jobname=jobname[rank],
                                   allow_ignore=True,
                                   mode='console',
                                   )

femodel = [[] for i in range(nproc)]

femodel[rank] = PropellerModel(mapdl[rank],
                               mesh_density_factor=1,
                               propeller = propeller,
                               n_sec= 20,
                               )

femodel[rank].materials = {'flaxpreg': Material(mapdl[rank],
                                                'FLAXPREG-T-UD',
                                                1),
                           'balsa': Material(mapdl[rank],
                                             'balsaholz',
                                             2),
                           }

femodel[rank].element_data = pd.read_csv('element_data.csv', index_col=(0))

# %% Define Objective function 

def objfunc(x):
    comm = MPI.COMM_WORLD
    
    size = comm.Get_size()
    rank = comm.Get_rank()  
    
    f, g, h = femodel[rank].evaluate(x)
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    print("process "+ str(rank) + " of " + str(size))
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
    optprob.addVar('phi' + str(i), 'p', lower=0., upper=180.)
for i in range (20):
    optprob.addVar('tpm' + str(i), 'c', lower=0., upper=0.185 * 4)
    optprob.addVar('rho' + str(i), 'c', lower=0., upper=1.)
    optprob.addVar('div' + str(i), 'c', lower=0., upper=1.)

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

coldstart()