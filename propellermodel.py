# %% Import Libraries and Data

# Third-party imports
from math import pi
import numpy as np

# Local imports
from util_mapdl.post_functions import fc_puck
from femodel import Femodel

# %%


class PropellerModel(Femodel):
        
    def __define_and_mesh_geometry__(self):
        """
        All basic model settings that do not require data exchange with the 
        propeller instance (Planform Geometry, Material Parameters, 
        Meshing, BCs).
        
                
        Units: tonne,mm,s,N
        
        """
        self.mapdl.prep7() # Enter Preprocessing Routine
        
        # Space for basic parameters and settings
        self.mapdl.seltol(1e-4)
        self.mapdl.et('1','SHELL281')    
        self.mapdl.keyopt(1,8,1)

        # Material Parameters
        for key in self.materials:
            self.materials[key].assign_mp()

        # Geometry
        self.mapdl.k(1,-18.54,40,26.99) # An Tip und Hub radius anpassen?
        self.mapdl.k(2,55.62,40,0)
        self.mapdl.k(3,-8.24,412,5.81)
        self.mapdl.k(4,24.72,412,0)
        
        # self.mapdl.k(10,0,40,-10)
        # self.mapdl.k(11,0,412,-10)
        
        self.mapdl.l(1,2)
        # self.mapdl.larc(1,2,10,200)
        self.mapdl.l(2,4)
        self.mapdl.l(3,4)
        # self.mapdl.larc(3,4,11,40)
        self.mapdl.l(3,1)
        
        # self.mapdl.a(1,2,4,3)
        self.mapdl.al(1,2,3,4)
        
        # Meshing
        self.mapdl.lsel('s','line','',1)
        self.mapdl.lsel('a','line','',3)
        self.mapdl.lesize('all','','',15 * self.mesh_density_factor, -2)
        
        self.mapdl.lsel('s','line','',2)
        self.mapdl.lsel('a','line','',4)
        self.mapdl.lesize('all','','',45 * self.mesh_density_factor)
        
        # Assignment of some dummy section
        self.mapdl.mshkey(1)
        self.mapdl.mshape(0,'2d')
        self.mapdl.allsel('all')
        
        self.mapdl.sectype(100,'shell','','Dummy')
        self.mapdl.secdata(0.1,1,90.,3)
        self.mapdl.allsel('all')
        self.mapdl.amesh('all')      
    
        # Boundary conditions
        self.mapdl.nsel('s','loc','y',40)
        self.mapdl.d('all','all',0)
        
    def __apply_loads__(self):
        """
        The Load application.

        """
        # Read ANSYS Input file (Do not change!)
        self.mapdl.prep7()
        
        self.mapdl.fcum('add')
        self.mapdl.allsel('all')
        
        # Vary Geometry
        
        nodes_per_elem = len(self.mapdl.mesh.elem[1][10:])
        
        for element in self.element_data['Element Number']:            
            # assign lift
            self.mapdl.sfe(element, '', 'pres', 1,
                           self.element_data['Pressure by Lift'][element])
            
            # assign drag (distributed to the element's nodes)
            for node in self.mapdl.mesh.elem[int(element-1)][10:]:
                self.mapdl.f(node, 'fx', 
                            self.element_aoa_vector[int(element-1)][0]
                            * self.element_data['Viscous Drag'][element]
                            / nodes_per_elem)
                
                self.mapdl.f(node, 'fz',
                            self.element_aoa_vector[int(element-1)][2]
                            * self.element_data['Viscous Drag'][element]
                            / nodes_per_elem)
            
        self.mapdl.omega(0,0,(max([float(i[1]['single_values']['rpm']) 
                                  for i in self.propeller.loadcases]) 
                              * (2*pi/60)))
        
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
            self.mapdl.secoffset('user',
                                 self.element_data['Element offset'][element])
            
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
                                   global_vars[2],
                                   3)
                for index in [5,6]:
                    self.mapdl.secdata(args[sec][0]/4,
                                       self.materials['flaxpreg'].number,
                                       global_vars[index],
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
        
        global_vars = x[:7]
        
        args = []
        for section in range(self.n_sec):
            x1 = len(global_vars) + section * 3
            args.append(x[x1:(x1+3)])
        
        # Convert input for __change_design_variables__() method
        self.cdread()
        self.change_design_variables(global_vars, *args)
        self.__solve__()
        m, I_f, I_m = self.post_processing()
        self.clear()
        
        g = list(np.round(np.array(I_f+I_m)-1,3))    
        
        return  m*10e6, g, []
        
    def post_processing(self):
        """
        The post processing routine.

        Returns
        -------
        M_tot : float
            The propeller blade mass in [tonne].
        I_fib_fail : list
            The Puck fiber failure criterion.
        I_mat_fail : list
            The Puck inter-fiber failure criterion.

        """
        self.mapdl.post1() # Enter Post-processing Routine
        
        # Assign Failure Criteria Values
        for key in self.materials:
            self.materials[key].assign_fc()        
        
        self.mapdl.fctyp('dele','all')
        self.mapdl.fctyp('add','pfib')
        self.mapdl.fctyp('add','pmat')
        
        I_fib_fail = []
        I_mat_fail = []
        
        # Calculate objective and constraint values        
        for section in range(self.n_sec):
            elements = self.element_data[self.element_data['Section Number'] \
                                         == section]['Element Number']
            
            self.mapdl.esel('s', 'elem', '', min(elements), max(elements), 1)

            I_f_loc, I_m_loc = fc_puck(self.mapdl)
            
            I_fib_fail.append(I_f_loc)
            I_mat_fail.append(I_m_loc)
            
        self.mapdl.allsel('all')
        self.mapdl.get('Blade_Mass','elem','0','mtot','z')
        
        return self.mapdl.parameters['Blade_Mass'], I_fib_fail, I_mat_fail