#%% Import Libraries and Data 

# Third-party imports
import os
from subprocess import DEVNULL, STDOUT, run
import pandas as pd

# Local imports
from .xsoftware import Xsoftware

#%%


class Xrotor(Xsoftware):
    """
    The interface class to XROTOR.

    XROTOR access works with a context manager:

    .. code-block:: python

        from util_loads import Xrotor

        with Xrotor(propeller= SomeProp, loadcase= 'SomeLoadcase', mode='hide') as x:
            x.run('atmo 0')
            #...
            x.run('quit')

    Parameters
    ----------
    propeller : Instance of propeller class
        Propeller to take geometry from.
        
    loadcase : Key of loadcase in propeller instance
        Loadcase to take parameters from and return results to.
        
    mode : str, optional
        Mode to launch Xrotor.  Must be one of the following:
            
        - ``'hide'`` Hide popup windows and suppress output to console.
        - ``'show'`` Show popup windows and output to console.
            
    """
    def __init__(self, propeller, loadcase, mode='hide'):
        super().__init__()
        self.input_file = '_xrotor_input.txt'
        
        self.__propeller = propeller
        self.__loadcase = loadcase
        self.__mode = mode
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        
        if self.__mode == 'hide':
            run(['Xvfb :1 &'], shell=True, stdout=DEVNULL, stderr=STDOUT)
            run(['DISPLAY=:1 xrotor < ' + self.input_file], shell=True, stdout=DEVNULL, stderr=STDOUT)
            run(['kill -15 $!'], shell=True, stdout=DEVNULL, stderr=STDOUT)
        elif self.__mode == 'show':
            os.system('xrotor < ' + self.input_file)
        else:
            raise ValueError('Invalid mode %s' % self.__mode)
        
        os.remove(self.input_file)
    
    def arbi(self):
        """
        Runs XROTORs ARBI command and parses the given propeller geometry.

        .. code-block:: none

            ARBI   Input arbitrary rotor geometry

        Returns
        -------
        None.

        """
        self.run('arbi')
        self.run(self.__propeller.parameters['number_of_blades'])
        self.run(self.__loadcase.flight_speed)
        self.run(self.__propeller.parameters['tip_radius'])
        self.run(self.__propeller.parameters['hub_radius'])
        
        self.run(str(len(self.__propeller.geometry)))
        self.run_array(self.__propeller.geometry)
        self.run('n')
        
    def parse_airfoils(self):
        """
        Enters XROTORs AERO routine and parses the given propeller airfoil data

        .. code-block:: none

            .AERO   Display or change airfoil characteristics

        Returns
        -------
        None.

        """
        for index, section in enumerate(self.__propeller.sections):
            self.run('aero')
            self.run('new')
            self.run(section[0])
            self.run('edit')
            self.run(index + 2)
            self.run('1')
            self.run(section[1].xrotor_characteristics['Zero-lift alpha (deg)'])
            self.run('2')
            self.run(section[1].xrotor_characteristics['d(Cl)/d(alpha)'])
            self.run('3')
            self.run(section[1].xrotor_characteristics['d(Cl)/d(alpha)@stall'])
            self.run('4')
            self.run(section[1].xrotor_characteristics['Maximum Cl'])
            self.run('5')
            self.run(section[1].xrotor_characteristics['Minimum Cl'])
            self.run('6')
            self.run(section[1].xrotor_characteristics['Cl increment to stall'])
            self.run('7')
            self.run(section[1].xrotor_characteristics['Minimum Cd'])
            self.run('8')
            self.run(section[1].xrotor_characteristics['Cl at minimum Cd'])
            self.run('9')
            self.run(section[1].xrotor_characteristics['d(Cd)/d(Cl**2)'])
            self.run('10')
            self.run(section[1].parameters['Re'])
            self.run('12')
            self.run(section[1].xrotor_characteristics['Cm'])
            self.run('')
            self.run('')
        
    @staticmethod
    def read_bend_output(filename):
        """
        Reads the output file of XROTORs BEND Routine and returns the content as DataFrame
        
        .. code-block:: none
        
            .BEND   Calculate structural loads and deflections

        Parameters
        ----------
        filename : String
            Name of output file of XROTORs bend routine.

        Returns
        -------
        DataFrame

        """
        colspecs = [(1, 3), (4, 10), (11, 18), (19, 26), (28, 34), (35, 46),
                    (48, 59), (61, 72), (74, 85), (87, 98), (100, 111)]
        tabular_data = pd.read_fwf(filename, colspecs=colspecs, header=[1], skiprows=[2], nrows=29)
        
        return tabular_data
    
    @staticmethod
    def read_oper_output(filename):
        """
        Reads the output file of XROTORs OPER Routine and returns the content as DataFrames
        
        .. code-block:: none
        
            .OPER   Calculate off-design operating points

        Parameters
        ----------
        filename : String
            Name of output file of XROTORs bend routine.

        Returns
        -------
        DataFrame
            Single Values
        DataFrame 
            Tabular Data

        """
        single_values = {}
        columns = [[(1, 12), (15, 24)], [(28, 39), (42, 51)], [(54, 65), (69, 78)]]
        for colspec in columns:
            header = pd.read_fwf(filename, colspecs=colspec, header=0, skiprows=3, nrows=7, index_col=0)
            header.columns = ['Value']
            header.dropna(subset=['Value'], inplace=True)
            header = header.to_dict()['Value']
            single_values.update(header)
    
        colspecs = [(1, 4), (4, 9), (10, 16), (16, 25), (25, 30), (33, 39),
                    (40, 47), (48, 53), (54, 60), (61, 66), (67, 74)]
        tabular_data = pd.read_fwf(filename, colspecs=colspecs, header=16)
        
        return single_values, tabular_data
