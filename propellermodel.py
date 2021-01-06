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
        self.mapdl.k(1, -9.60, 50, 0)
        self.mapdl.k(2, 22.40, 50, 0)
        
        self.mapdl.k(3, -19.80, 92, 2)
        self.mapdl.k(4, 42.98, 92, -18.35)
        
        # self.mapdl.k(5, -12.24, 142, 2)
        self.mapdl.k(6, 40.92, 142, -13.26)
        
        # self.mapdl.k(7, -11.67, 172, 2)
        self.mapdl.k(8, 39.42, 172, -10.8)
        
        # self.mapdl.k(9, -11.1, 202, 2)
        self.mapdl.k(10, 37.78, 202, -8.75)
        
        # self.mapdl.k(11, -10.52, 232, 2)
        self.mapdl.k(12, 36.04, 232, -7.08)

        # self.mapdl.k(13, -9.95, 262, 2)
        self.mapdl.k(14, 34.21, 262, -5.75)
        
        # self.mapdl.k(15, -9.37, 292, 2)
        self.mapdl.k(16, 32.33, 292, -4.73)
        
        # self.mapdl.k(17, -8.8, 322, 2)
        self.mapdl.k(18, 30.39, 322, -3.98)
        
        # self.mapdl.k(19, -8.23, 352, 2)
        self.mapdl.k(20, 28.43, 352, -3.46)
        
        self.mapdl.k(21, -11.25, 390, 2)
        self.mapdl.k(22, 25.93, 390, -2.89)
        
        self.mapdl.k(23, -8.10, 412, 2)
        self.mapdl.k(24, 18.67, 412, -1.52)
             
        # root side
        self.mapdl.l(1,2)
        
        # trailing edge
        self.mapdl.l(2,4)
        self.mapdl.l(4,6)
        self.mapdl.l(6,8)
        self.mapdl.l(8,10)
        self.mapdl.l(10,12)
        self.mapdl.l(12,14)
        self.mapdl.l(14,16)
        self.mapdl.l(16,18)
        self.mapdl.l(18,20)
        self.mapdl.l(20,22)
        self.mapdl.l(22,24)
                
        self.mapdl.lsel('s','line','','3','11')
        self.mapdl.lcomb('all')
        self.mapdl.allsel('all')
        
        # tip side
        self.mapdl.l(23,24)
        
        # leading edge
        self.mapdl.l(1,3)
        self.mapdl.l(3,21)
        self.mapdl.l(21,23)
        
        self.mapdl.l(3,4)
        self.mapdl.l(21,22)
        self.mapdl.al(1,2,8,5)
        self.mapdl.al(8,3,9,6)
        self.mapdl.al(9,12,4,7)
        self.mapdl.lesize(5,'','',5 * self.mesh_density_factor)
        self.mapdl.lesize(1,'','',15 * self.mesh_density_factor, -2)
        self.mapdl.lesize(6,'','',37 * self.mesh_density_factor)
        self.mapdl.lesize(8,'','',15 * self.mesh_density_factor, -2)
        self.mapdl.lesize(7,'','',3 * self.mesh_density_factor)
        self.mapdl.lesize(9,'','',15 * self.mesh_density_factor, -2)
        
        # Assignment of some dummy section
        self.mapdl.mshkey(1)
        self.mapdl.mshape(0,'2d')
        self.mapdl.allsel('all')
        
        self.mapdl.sectype(100,'shell','','Dummy')
        self.mapdl.secdata(0.1,1,90.,3)
        self.mapdl.allsel('all')
        self.mapdl.amesh('all')     
        
        # Boundary conditions
        self.mapdl.nsel('s','loc','y',50)
        self.mapdl.d('all','all',0)
        
        self.mapdl.allsel('all')
                
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
            
        # self.mapdl.omega(0,0,(max([float(i[1]['single_values']['rpm']) 
        #                           for i in self.propeller.loadcases]) 
        #                       * (2*pi/60)))
        
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
        
    def convergence_study(self, mesh_density):
        output = []
        
        for factor in mesh_density:
            self.clear()
            
            self.mesh_density_factor = factor
            
            print(factor)
            
            self.pre_processing()
            
            global_vars = [0 for i in range(7)]
            args=[[0.37, 1, 0.5] for i in range(20)]
            
            self.cdread()
            self.change_design_variables(global_vars, *args)
            self.__solve__()
            
            self.mapdl.post1() # Enter Post-processing Routine
        
            # Assign Failure Criteria Values
            for key in self.materials:
                self.materials[key].assign_fc()
                
            self.mapdl.run('tipnode = NODE(0,412,0)')
            self.mapdl.get('tipnode_dis_y','NODE','tipnode','U','Y')
            self.mapdl.get('tipnode_dis_z','NODE','tipnode','U','Z')
            
            self.mapdl.run('maxnode = NODE(0,92,0)')
            
            self.mapdl.get('maxnode_dis_y','NODE','maxnode','U','Y')
            self.mapdl.get('maxnode_dis_z','NODE','maxnode','U','Z')
    
            # self.mapdl.layer(7)
            # self.mapdl.nsle('s','corner')
            # self.mapdl.nsel('r','loc','y',92)
            # self.mapdl.seltol(0.1)
            # self.mapdl.nsel('s','loc','x',0)
            # node = self.mapdl.mesh.nnum[0]
            # self.mapdl.allsel('all')
            
            
            # self.mapdl.get('maxnode_s_y','NODE',node,'s','Y')
            
            self.mapdl.parameters
            
            rv = [self.mapdl.parameters['tipnode_dis_y'],
                  self.mapdl.parameters['tipnode_dis_z'],
                  self.mapdl.parameters['maxnode_dis_y'],
                  self.mapdl.parameters['maxnode_dis_z'],
                  # self.mapdl.parameters['maxnode_s_y'],
                  ]
            
            output.append(rv)
            
            print(rv)
            
        return output
    
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
        
        return  m*1e6, g, []
        
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
            
            elements = list(elements)
                
            self.mapdl.esel('s','elem','',elements[0])
            for element in elements[1:]:
                self.mapdl.esel('a','elem','',element)
            
            I_f_loc, I_m_loc = fc_puck(self.mapdl)
            
            I_fib_fail.append(I_f_loc)
            I_mat_fail.append(I_m_loc)
            
        self.mapdl.allsel('all')
        self.mapdl.get('Blade_Mass','elem','0','mtot','z')
        
        return self.mapdl.parameters['Blade_Mass'], I_fib_fail, I_mat_fail
    
    def reaction_forces(self):
        self.mapdl.post1()
        
        # self.mapdl.nsel('s','loc','y',50)
        # nodes = self.mapdl.mesh.nnum
        
        rforces, nnum, dof = self.mapdl.result.nodal_reaction_forces(0)
        
        rforces_sorted = [[] for i in range(6)]
        
        for idx, x in enumerate(rforces):
            rforces_sorted[int(dof[idx]-1)].append(x)
        
        fsum = []    
        for x in rforces_sorted:
            fsum.append(sum(x))
            
        return fsum