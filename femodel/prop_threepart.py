"""
Propeller FE-Modell mit dreiteiligem Lagenaufbau.

Created on Jan 12 2021

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np

# Local imports
from .propellermodel import PropellerModel

# %% 


class Threepartmodel(PropellerModel):
    
    def change_design_variables(self, global_vars, *args):
        """
        Implement the parameter variation here.
        
        This method lets ANSYS read the input file created in __setup__() 
        and adds the design variation.
        After that, preprocessing is finished.
    
        Parameters
        ----------
        global_vars : list
            List of all global variables (fiber angles...)
        *args : tuple
            Tuple with the design variables for the individual sections.
            
        """
        
        # Read ANSYS Input file (Do not change!)
        self.mapdl.prep7()
                
        # Vary Geometry
        for element in self.element_data['Element Number']:
            self.mapdl.sectype(element,'shell','','')
            
            sec = int(self.element_data['Section Number'][element])
            el_height = self.element_data['Element height'][element]
            
            layer_thickness = 0.185
            min_thickness = layer_thickness * 2
            core = el_height - min_thickness
            
            with self.mapdl.chain_commands:
                self.mapdl.secdata(min_thickness/2,
                                  self.materials['flaxpreg'].number,
                                  global_vars[0],
                                  3)           
                if core > 0:
                    height_balsa = core * (1 - args[sec][0])
                    
                    if height_balsa < 1:
                        for i in range(2):
                            self.mapdl.secdata(core / 2,
                                               self.materials['flaxpreg'].number,
                                               global_vars[0],
                                               3)
                    
                    else:
                        self.mapdl.secdata((core
                                            * args[sec][0] 
                                            * args[sec][1]),
                                           self.materials['flaxpreg'].number,
                                           global_vars[0],
                                           3)                    
                        self.mapdl.secdata((core
                                            * (1 - args[sec][0])),
                                           self.materials['balsa'].number,
                                           global_vars[1],
                                           3)      
                        self.mapdl.secdata((core
                                            * args[sec][0] 
                                            * (1 - args[sec][1])),
                                           self.materials['flaxpreg'].number,
                                           global_vars[0],
                                           3)
                
                self.mapdl.secdata(min_thickness/2,
                                  self.materials['flaxpreg'].number,
                                  global_vars[0],
                                  3) 
                
                self.mapdl.emodif(element, 'secnum', element)
                        
        self.mapdl.allsel('all')
        
    def evaluate(self, x):
        """
        This method translates the rather confusing design variable list 
        from the optimizer into a more comprehensible format which is passed
        to the change_design_variables() method.
        
        Then, the model is solved, the database is cleared, 
        and the post-processing results are returned.
        

        Parameters
        ----------
        x : list
            The design variables list coming from the Optimizer.

        Returns
        -------
        M_tot : float
            The propeller blade mass in [tonne].
        I_fib_fail : list
            The Puck fiber failure criterion.
        I_mat_fail : list
            The Puck inter-fiber failure criterion.
        """
        
        global_vars = x[1:3]
        
        args = []
        for section in range(self.n_sec):
            x1 = 1 + len(global_vars) + section * 2
            args.append(x[x1:(x1+2)])
        
        # Convert input for __change_design_variables__() method
        self.cdread()
        self.change_design_variables(global_vars, *args)
        self.__solve__()
        m, I_f, I_m = self.post_processing()
        self.clear()
        
        g = list(np.array(I_f+I_m))    
        
        return  m*1e6, g, []