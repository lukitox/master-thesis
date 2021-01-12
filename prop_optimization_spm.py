"""
Optimization script of HeLics propeller structural analysis Template

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
from util_mapdl import Material
from propellermodel import PropellerModel

# %% Run ANSYS and instantiate FE-Model

rank = MPI.COMM_WORLD.Get_rank()
size = MPI.COMM_WORLD.Get_size()

ansys_path = ['/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-'
              + str(i) for i in range(size)]

jobname = ['job-' + str(i) for i in range(size)]

mapdl = [[] for i in range(size)]

mapdl[rank] = pyansys.launch_mapdl(run_location=ansys_path[rank],
                                   nproc=1,
                                   override=True,
                                   loglevel='error',
                                   additional_switches='-smp -d X11C',
                                   jobname=jobname[rank],
                                   allow_ignore=True,
                                   mode='console',
                                   )

femodel = [[] for i in range(size)]

femodel[rank] = PropellerModel(mapdl[rank],
                               mesh_density_factor=1,
                               propeller = [],
                               n_sec= 20,
                               )

femodel[rank].materials = {'flaxpreg': Material(mapdl[rank],
                                                'FLAXPREG-T-UD',
                                                1),
                           'balsa': Material(mapdl[rank],
                                             'balsaholz',
                                             2),
                           }

femodel[rank].element_data = pd.read_csv('./mf3218/element_data.csv',
                                         index_col=(0))

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