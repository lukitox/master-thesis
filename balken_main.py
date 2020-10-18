#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 15:42:30 2020

@author: Lukas Hilbers
"""

#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import time
import pyansys
from pyOpt import Optimization
from pyOpt import ALPSO

# Local imports
import balken_femodel#_cd as balken_femodel

#%% Run ANSYS and instantiate FE-Model

ansys_path = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS'
mapdl = pyansys.launch_mapdl(run_location=ansys_path,
                             nproc=4,
                             override=True,
                             loglevel='error',
                             additional_switches='-smp -d WIN32C',
                             allow_ignore=True,
                             mode='console'
                             )

femodel = balken_femodel.femodel(mapdl)
starttime = time.time()

# Set basic parameters
mapdl.output('output','out')
mapdl.seltol('1e-4')

#%% Define Objective function 

def objfunc(x):
    mtot, I = femodel.evaluate(x)
    
    # Get objective and constraint vector
    f = np.round(mtot*10**6,3)
    g = list(np.round(np.array(I)-1,3))
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    timestamp = np.round(time.time()-starttime,1)
    print(timestamp, objfunc.counter,str(np.round(f,2)).zfill(5),str(int(x[0])).zfill(3),str(int(x[1])).zfill(3),list(np.round(x[2:],3)))
    
    time.sleep(0.01)
    fail = 0
    return f, g, fail
objfunc.counter = 0

#%% Instantiate Optimization Problem 
opt_prob = Optimization('Faserverbundbalken',objfunc)

# Add variables
t_layer = 0.185
opt_prob.addVar('y1'    ,'i',lower=4            ,upper=100  ,value=30       )
opt_prob.addVar('y2'    ,'i',lower=4            ,upper=150  ,value=90       )
opt_prob.addVar('n_top1','c',lower=1*0.1        ,upper=1.5  ,value=3*t_layer)
opt_prob.addVar('n_top2','c',lower=1*0.1        ,upper=1.5  ,value=3*t_layer)
opt_prob.addVar('n_top3','c',lower=1*t_layer    ,upper=0.75 ,value=2*t_layer)
opt_prob.addVar('n_bot1','c',lower=1*0.1        ,upper=1.5  ,value=5*t_layer)
opt_prob.addVar('n_bot2','c',lower=1*0.1        ,upper=1.5  ,value=4*t_layer)
opt_prob.addVar('n_bot3','c',lower=1*t_layer    ,upper=0.75 ,value=2*t_layer)
opt_prob.addVar('n_web1','c',lower=1*t_layer    ,upper=1.5  ,value=2*t_layer)
opt_prob.addVar('n_web2','c',lower=1*t_layer    ,upper=1.5  ,value=1*t_layer)
opt_prob.addVar('n_web3','c',lower=1*t_layer    ,upper=0.75 ,value=1*t_layer)

# Add objective
opt_prob.addObj('f')

# Add constraints
opt_prob.addConGroup('g_fib_top', 3, 'i')
opt_prob.addConGroup('g_fib_bot', 3, 'i')
opt_prob.addConGroup('g_fib_web', 3, 'i')
opt_prob.addConGroup('g_mat_top', 3, 'i')
opt_prob.addConGroup('g_mat_bot', 3, 'i')
opt_prob.addConGroup('g_mat_web', 3, 'i')

#%% Instantiate Optimizer and Solve Problem

# Instantiate Optimizer
alpso = ALPSO()
alpso.setOption('fileout',1)

filename = 'Balken_Output_ALPSO'

alpso.setOption('filename',     filename)
alpso.setOption('SwarmSize',    40      )
alpso.setOption('stopIters',    5       )      
alpso.setOption('rinit',        1.      )
alpso.setOption('itol',         0.01    )

def coldstart():    
    alpso(opt_prob, store_hst=True)
    print(opt_prob.solution(0))
    
def hotstart():
    alpso.setOption('filename',filename + '_hotstart')
    alpso(opt_prob, store_hst=True, hot_start= filename)
    print(opt_prob.solution(0)) # 0 or 1?

print('Run coldstart(), hotstart() or do what you want!')

#%% Solution Data for Test Purposes

# divisions = [200,445]
# topspar = [0.726,0.392,0.193]
# bottomspar = [0.781,0.510,0.230]
# web = [0.185,0.185,0.185]
# x=[40,89,0.726,0.392,0.193,0.781,0.510,0.230,0.185,0.185,0.185]
