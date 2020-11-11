#%% Import Libraries and Data 

# Third-party imports
import numpy as np

## Local imports

#%%

class Propeller:
    
    def __init__(self, number_of_blades, tip_radius, hub_radius):
        self.parameters = {'number_of_blades': number_of_blades,
                           'tip_radius': tip_radius,
                           'hub_radius': hub_radius,
                           }    
        
        self.__loadcases = {}
        self.__geometry = []
        self.__sections = []
        
    def __repr__(self):
        return str(self.parameters)
    
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
    def loadcases(self):
        """
        

        Returns
        -------
        Dict
            Dictionary of loadcases.

        """
        return self.__loadcases
    
    def add_loadcase(self, name, loadcase):
        self.__loadcases[name] = loadcase
    
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