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
import os

# Local imports
from util_mapdl import Material
from femodel import Threepartmodel

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

n_sec = 20

femodel[rank] = Threepartmodel(mapdl[rank],
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

np.set_printoptions(formatter={'float': lambda x: format(x, '3.2f')})
starttime = time.time()

tip_vector = [0, 0.5, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0.5]

def objfunc(x):
    comm = MPI.COMM_WORLD
    
    size = comm.Get_size()
    rank = comm.Get_rank()  
    
    x = list(x) + tip_vector
    
    f, g, h = femodel[rank].evaluate(x)
        
    g_beta = []
    i_ref = 1.
    for i_sec in g[1:14]:
        if i_sec >= i_ref:
            g_beta.append(i_sec - x[0])
        elif i_sec < i_ref: 
            g_beta.append(x[0] - i_sec)
        else:
            raise RuntimeError('This should never happen!')
            
    g = list(np.array(g) - 1)
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    print("process "+ str(rank) + " of " + str(size))
    print(np.round(time.time() - starttime,1), objfunc.counter)
    print(str(np.round(np.array(x[:3]),2)))    
    print(str(np.round(np.array(x[3:31]),2)))
    
    time.sleep(0.01)
    fail = 0
    
    if rank == 0 and objfunc.counter % 10 == 0:
        os.system('rm -f /tmp/tmp_*')
    
    return abs(x[0] - i_ref), g + g_beta, fail
objfunc.counter = 0

# %% Instantiate Optimization Problem 

optprob = Optimization(name='Propeller',
                        obj_fun=objfunc
                        )

# Add variables
optprob.addVar('beta', 'c', lower=0., upper=1.)
for i in range(2):                        
    optprob.addVar('phi' + str(i), 'p', lower=0., upper=180., value=90)
for i in range (14):
    optprob.addVar('rho' + str(i), 'c', lower=0., upper=0.8)#, value=0.5)
    optprob.addVar('div' + str(i), 'c', lower=0.3, upper=0.7, value=0.5)

# Add objective
optprob.addObj('f')

# Add constraints
for i in range(n_sec): 
    optprob.addCon('gf' + str(i), 'i')
# Add constraints
for i in range(n_sec): 
    optprob.addCon('gm' + str(i), 'i')
for i in range(13): 
    optprob.addCon('g_beta' + str(i), 'i')

# %% Instantiate Optimizer
alpso = ALPSO(pll_type='SPM')
alpso.setOption('fileout',1)

alpso_path = '/home/y0065120/Dokumente/Leichtwerk/Projects/ALPSO/'
filename = 'Simpleblade_Output_ALPSO'

alpso.setOption('filename', alpso_path+filename)
alpso.setOption('SwarmSize', 84)
alpso.setOption('stopIters', 5)      
alpso.setOption('rinit', 1.)
alpso.setOption('itol', 0.01)
alpso.setOption('xinit', 1)
alpso.setOption('vcrazy', 1e-3)
alpso.setOption('stopCriteria', 0)
alpso.setOption('c1',3.5)
alpso.setOption('c2',0.3)
alpso.setOption('w2',0.7)


def coldstart():    
    alpso(optprob, store_hst=True)
    print(optprob.solution(0))
    
def hotstart():
    alpso.setOption('filename',alpso_path+filename + '_hotstart')
    alpso(optprob, store_hst=True, hot_start= alpso_path+filename)
    print(optprob.solution(0))

coldstart()
