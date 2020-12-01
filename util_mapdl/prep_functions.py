#%% Import Libraries and Data 

# Third-party imports
import numpy as np

# Local imports

# %%


def get_edges(mapdl, y):
    
    def intersection(lnum):
        kp_0 =  100000
        kp_num = 5
        a_num = 2
        
        mapdl.prep7()
        
        mapdl.k(kp_0+1, -1000, y, -1000)
        mapdl.k(kp_0+2, 1000, y, -1000)
        mapdl.k(kp_0+3, 1000, y, 1000)
        mapdl.k(kp_0+4, -1000, y, 1000)
        
        mapdl.a(kp_0+1, kp_0+2, kp_0+3, kp_0+4)
            
        mapdl.lina(lnum, a_num)
        
        coords = []
        for axis in ['x','y','z']:
            mapdl.get('c', 'KP', kp_num, 'loc', axis)
            coords.append(mapdl.parameters['c'])
        
        mapdl.kdele(kp_num)
        
        return coords
    
    le = np.array(intersection(4))
    te = np.array(intersection(2))
    
    return le, te, np.linalg.norm(te - le)