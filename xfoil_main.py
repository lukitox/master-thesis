#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from util_xrotor import util_xrotor as ux

#%% Renerate some xfoil polar

with ux.xfoil() as x:
    x.run('load mh121.txt')
    x.run('pane')
    x.run('oper')
    x.run('visc 100000')
    x.run('iter')
    x.run('400')
    x.run('pacc')
    x.run('mh121_polar.txt')
    x.run('')
    x.run('aseq -5 8 1')
    x.run('')
    x.run('quit')
    
#%% Play around