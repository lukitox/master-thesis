#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import os

## Local imports
from .xrotor import Xrotor

#%%

class Propeller:
    
    def __init__(self, number_of_blades, tip_radius, hub_radius):
        self.parameters = {'number_of_blades': number_of_blades,
                           'tip_radius': tip_radius,
                           'hub_radius': hub_radius,
                           }    
        
        self.__loadcases = []
        self.__loads = []
        self.__geometry = []
        self.__sections = []
        
    def __repr__(self):
        return str(self.parameters)
    
    def calc_loads(self):
        
        oper_file  = '_xrotor_oper.txt'
        bend_file  = '_xrotor_bend.txt'
        
        for loadcase, result in self.loadcases:
            with Xrotor(self, loadcase) as x:
                x.run('atmo 0')  # Set fluid properties from ISA 0km
                x.arbi()  # Input arbitrary rotor geometry
                x.parse_airfoils()
                x.run('oper')  # Calculate off-design operating points
                for field in loadcase.data:
                    x.run(field)
                x.run('writ ' + oper_file)
                x.run('')  # return
                x.run('bend')  # Write current operating point to disk file
                x.run('eval')  # Evaluate structural loads and deflections
                x.run('writ ' + bend_file)
                x.run('')  # return
                x.run('quit')  # Exit program
            
            result['single_values'], result['oper'] = Xrotor.read_oper_output(oper_file)
            result['bend'] = Xrotor.read_bend_output(bend_file)
            
            os.remove(oper_file)
            os.remove(bend_file)
            
    @property
    def geometry(self):
        """
        
        Returns
        -------
        List
            Propeller geometry. [r/R, c/R, beta]

        """
        return self.__geometry
    
    @geometry.setter
    def geometry(self, array):
        if type(array) == type(np.array([])):
            self.__geometry = array.tolist()
        elif type(array) == list:
            self.__geometry = array
        else:
            raise TypeError
    
    @property
    def loads(self):
        return self.__loads
    
    @loads.setter
    def loads_oper(self, path):
        single_values = {}
        columns = [[(1, 12), (15, 24)], [(28, 39), (42, 51)], [(54, 65), (69, 78)]]
        for colspec in columns:
            header = pd.read_fwf(path, colspecs=colspec, header=0, skiprows=3, nrows = 7, index_col=0)
            header.columns = ['Value']
            header.dropna(subset = ['Value'], inplace=True)
            header = header.to_dict()['Value']
            single_values.update(header)
    
        colspecs = [(1, 4), (4, 9), (10, 16), (16, 25), (25, 30), (33, 39), (40, 47), (48, 53), (54, 60), (61, 66), (67, 74)]
        tabular_data = pd.read_fwf(path, colspecs=colspecs, header= 16)
        
        self.__loads['single_values'] = single_values
        self.__loads['oper'] = tabular_data
    
    @loads.setter
    def loads_bend(self, file):
        self.__loads['bend'] = 'bend'
    
    @property
    def loadcases(self):
        """

        Returns
        -------
        Dict
            Dictionary of loadcases.

        """
        return self.__loadcases
    
    def add_loadcase(self, loadcase):
        self.__loadcases.append([loadcase, {}])
    
    @property
    def parameters(self):
        """
        
        Returns
        -------
        Dict
            Propeller Parameters.

        """
        return self.__parameters
    
    @parameters.setter
    def parameters(self, parameters):
        self.__parameters = parameters
        
    @property 
    def sections(self):
        """
        
        Returns
        -------
        List
            Aifoil sections. [r/R, Airfoil]

        """
        return self.__sections
    
    def add_section(self, rR, airfoil):
        self.sections.append([rR, airfoil])
        self.sections.sort()