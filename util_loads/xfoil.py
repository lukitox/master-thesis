#%% Import Libraries and Data 

# Third-party imports
import os
import pandas as pd

## Local imports
from .xsoftware import Xsoftware

#%%
class Xfoil(Xsoftware):
    '''
    The interface class to XFOIL.
    
    XFOIL access works with a context manager:
    
    .. code-block:: python
    
        from util_loads import Xfoil
        
        with Xfoil() as x:
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
        
    @staticmethod
    def read_coordinates(filename):
        """
        Reads an airoil coordinates file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        DataFrame

        """
        df = pd.read_fwf(filename,
                         header = 0,
                         names=['X','Y'],
                         )
        
        return df.dropna()
    
    @staticmethod
    def read_cp_vs_x(filename):
        """
        Reads a pressure distribution file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        DataFrame

        """
        df = pd.read_fwf(filename,
                 header=0,
                 skiprows=0,
                 names=['#','x','Cp'],
                 )
        return df.drop(labels=['#'],axis=1)
    
    @staticmethod
    def read_polar(filename):
        """
        Reads a polar output file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        DataFrame

        """
        colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46),
                    (49, 55), (58, 64), (66, 73), (74, 82)]
        tabular_data = pd.read_fwf(filename,
                                   colspecs=colspecs,
                                   header=[10],
                                   skiprows=[11])
        tabular_data.sort_values('alpha', inplace=True)
        tabular_data.drop_duplicates(keep='first', inplace=True)
        
        return tabular_data.reset_index()