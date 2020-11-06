"""
FE-Model module of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np

# Local imports
from util_mapdl import post_functions, prep_functions

# %% 

ansys_input_filename = '_ansys_input_file' # ANSYS input file for model setup

class Femodel:
    
    def __init__(self, mapdl, mesh_density_factor = 1):
        self.mapdl = mapdl
        
        self.__setup__(mesh_density_factor)
        
    def __setup__(self, mesh_density_factor):
        """
        Setup method. 
        Implement all basic model setup (Geometry, Material Parameters, 
        Meshing...) that will not be varied.
        
        Writes an APDL input file to ANSYS working directory.
        
        Units: tonne,mm,s,N

        Returns
        -------
        None.
        
        """
        self.mapdl.prep7() # Enter Preprocessing Routine
        
        # Space for basic Parameters

        # Material Parameters
        
        # Geometry
        
        # Meshing
        
        # Assignment of some dummy section
        
        # Loads (Todo: here or in __change_design_variables__() method?)
        
        # Write ANSYS Input file (Do not change!)
        self.mapdl.allsel('all')
        self.mapdl.cdwrite('db', ansys_input_filename, 'cdb')
        self.mapdl.finish()
        self.mapdl.clear('nostart')
        
    def __change_design_variables__(self, *args, **kwargs):
        """
        Implement the parameter variation here.
        
        This method lets ANSYS read the input file created in __setup__() 
        and adds the design variation.
        After that, preprocessing is finished.

        Parameters
        ----------
        *args : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        # Read ANSYS Input file (Do not change!)
        self.mapdl.prep7()
        self.mapdl.cdread('db', ansys_input_filename, 'cdb')
        
        # Vary Geometry
        
    def __solution__(self):
        """
        Solve the FE-Model. No changes to the code should be necessary.

        Returns
        -------
        None.

        """
        self.mapdl.run('/SOLU')
        self.mapdl.antype('static')
        self.mapdl.outres('all','all')
        self.mapdl.solve()
        self.mapdl.finish()
        
    def __post_processing__(self):
        """
        Post-processing routine.

        Returns
        -------
        float
            Value for objective function calculation.
        list
            Values for inequality constraint calculation.
        list
            Values for equality constraint calculation.

        """
        
        self.mapdl.post1() # Enter Post-processing Routine
        
        # Assign Failure Criteria
        
        # Calculate objective and constraint values
        
        return f, list(g), list(h)
        
        