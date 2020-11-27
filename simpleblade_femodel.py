"""
FE-Model module of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np

# Local imports
from util_mapdl import post_functions, Material

# %% 

ansys_input_filename = '_ansys_input_file' # ANSYS input file for model setup

class Femodel:
    """
    The FE-Model is implemented as a class.
    """
    
    def __init__(self, mapdl, propeller, loads, mesh_density_factor = 1, seltol = 1e-4):
        self.mapdl = mapdl
        
        # Materials
        self.m_flaxpreg = Material(self.mapdl, 'FLAXPREG-T-UD', 1)
        self.m_flaxpreg.load_from_db()
        self.m_balsa = Material(self.mapdl, 'balsaholz', 2)
        self.m_balsa.load_from_db()
        
        self.__setup__(loads, mesh_density_factor, seltol)
        
    def __setup__(self, loads, mesh_density_factor, seltol):
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
        
        # Space for basic parameters and settings
        self.mapdl.seltol(seltol)
        self.mapdl.et('1','SHELL281')    
        self.mapdl.keyopt(1,8,1)

        # Material Parameters
        self.m_flaxpreg.assign_mp()
        self.m_balsa.assign_mp()
        
        # Geometry
        self.mapdl.k(1,-10,10,0)
        self.mapdl.k(2,40,10,0)
        self.mapdl.k(3,-2,400,0)
        self.mapdl.k(4,8,400,0)
        
        self.mapdl.a(1,2,4,3)
        # Meshing
        self.mapdl.lsel('s','line','',1)
        self.mapdl.lsel('a','line','',3)
        self.mapdl.lesize('all','','',5)
        
        self.mapdl.lsel('s','line','',2)
        self.mapdl.lsel('a','line','',4)
        self.mapdl.lesize('all','','',50)
        
        # Assignment of some dummy section
        self.mapdl.mshkey(1)
        self.mapdl.mshape(0,'2d')
        self.mapdl.allsel('all')
        
        self.mapdl.sectype(100,'shell','','Dummy')
        self.mapdl.secdata(0.1,1,90.,3)
        self.mapdl.allsel('all')
        self.mapdl.amesh('all')      
    
        # Loads (Todo: here or in __change_design_variables__() method?)
        
        # Write ANSYS Input file (Do not change!)
        self.mapdl.allsel('all')
        self.mapdl.cdwrite('all', ansys_input_filename, 'cdb')
        self.mapdl.finish() # Todo: Dopplung vermeiden
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
        self.mapdl.cdread('all', ansys_input_filename, 'cdb')
        
        # Vary Geometry
        
    def __solve__(self):
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
        f : float
            Value for objective function calculation.
        g : list
            Values for inequality constraint calculation.
        h : list
            Values for equality constraint calculation.

        """
        
        self.mapdl.post1() # Enter Post-processing Routine
        
        # Assign Failure Criteria
        
        # Calculate objective and constraint values
        
        return f, list(g), list(h)
        
    def __clear__(self):
        """
        Resets ANSYS Session. No changes to the code should be necessary.

        Returns
        -------
        None.

        """
        self.mapdl.finish()
        self.mapdl.clear('NOSTART')
        
    def cdread(self):
        self.mapdl.prep7()
        self.mapdl.cdread('all', ansys_input_filename, 'cdb')
        
        self.mapdl.open_gui()
        
    def evaluate(self, x):
        """
        Evalue

        Parameters
        ----------
        x : TYPE
            DESCRIPTION.

        Returns
        -------
        f : float
            Objective function value.
        g : list
            Inequality constraints list.
        h : list
            Equalitiy constraints list.

        """
        
        # Convert input for __change_design_variables__() method
        
        self.__change_design_variables__(args, kwargs)
        self.__solve__()
        f, g, h = self.__post_processing__()
        
        # Calculate objective Function and restrictions
        
        return f, g, h
        
        