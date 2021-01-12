"""
Propeller FE-Modell mit dreiteiligem Lagenaufbau.

Created on Jan 12 2021

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports

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
        # self.mapdl.cdread('all', ansys_input_filename, 'cdb')
                
        # Vary Geometry
        for element in self.element_data['Element Number']:
            self.mapdl.sectype(element,'shell','','')
            # self.mapdl.secoffset('user',
            #                      self.element_data['Element offset'][element])
            
            sec = int(self.element_data['Section Number'][element])
            el_height = self.element_data['Element height'][element]
            core = el_height - args[sec][0]
            
            if args[sec][0] > el_height:
                for index in [0,1,5,6]:
                    self.mapdl.secdata(args[sec][0]/4,
                                       self.materials['flaxpreg'].number,
                                       global_vars[index],
                                       3)
            else:
                for index in [0,1]:
                    self.mapdl.secdata(args[sec][0]/4,
                                       self.materials['flaxpreg'].number,
                                       global_vars[index],
                                       3)
                self.mapdl.secdata((core
                                    * args[sec][1] 
                                    * args[sec][2]),
                                   self.materials['flaxpreg'].number,
                                   global_vars[2],
                                   3)
                self.mapdl.secdata((core
                                    * (1 - args[sec][1])),
                                   self.materials['balsa'].number,
                                   global_vars[3],
                                   3)
                self.mapdl.secdata((core
                                    * args[sec][1] 
                                    * (1 - args[sec][2])),
                                   self.materials['flaxpreg'].number,
                                   global_vars[4],
                                   3)
                for index in [5,6]:
                    self.mapdl.secdata(args[sec][0]/4,
                                       self.materials['flaxpreg'].number,
                                       global_vars[index],
                                       3)            
            
            self.mapdl.emodif(element, 'secnum', element)
                        
        self.mapdl.allsel('all')