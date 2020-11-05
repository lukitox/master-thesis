#%% Import Libraries and Data 

# Third-party imports
import os

## Local imports
from .xsoftware import xsoftware

#%%
class xfoil(xsoftware):
    '''
    The interface class to XFOIL.
    
    XFOIL access works with a context manager:
    
    .. code-block:: python
    
        import util_loads as ux
        
        with ux.xfoil() as x:
            x.run('aero')
            #...
            x.run('quit')
    
    '''
    
    def __init__(self):
        self.input_file = '_xfoil_input.txt'
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        '''
        Parameters
        ----------
        exc_type : TYPE
            DESCRIPTION.
        exc_value : TYPE
            DESCRIPTION.
        exc_traceback : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        super().__exit__(exc_type, exc_value, exc_traceback)
        os.system('xfoil < ' + self.input_file)
    
        os.remove(self.input_file)