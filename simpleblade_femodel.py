"""
FE-Model module of HeLics propeller structural analysis Template

Created on Nov 06 2020

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pandas as pd
from math import pi

# Local imports
from util_mapdl import Material

# %% 

ansys_input_filename = '_ansys_input_file' # ANSYS input file for model setup

class Femodel:
    """
    The FE-Model is implemented as a class.
    """
    
    def __init__(self, mapdl, propeller, loads, mesh_density_factor = 1, seltol = 1e-4):
        
        self.mapdl = mapdl
        self.propeller = propeller
        self.__element_data = None
        self.__element_chord_vector = None
        self.__element_aoa_vector = None
        
        self.__materials = {'flaxpreg': Material(self.mapdl,
                                                 'FLAXPREG-T-UD',
                                                 1),
                            'balsa': Material(self.mapdl,
                                              'balsaholz',
                                              2),
                            }
        for key in self.__materials:
            self.__materials[key].load_from_db()
        
        self.__setup__(mesh_density_factor, seltol)
        self.__calc_element_data__()
        self.__apply_loads__()
        
    def __setup__(self, mesh_density_factor, seltol):
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
        for key in self.materials:
            self.materials[key].assign_mp()

        # Geometry
        self.mapdl.k(1,-18.54,10,26.99)
        self.mapdl.k(2,55.62,10,0)
        self.mapdl.k(3,-8.24,412,5.81)
        self.mapdl.k(4,24.72,412,0)
        
        self.mapdl.k(10,0,10,-10)
        self.mapdl.k(11,0,412,-10)
        
        self.mapdl.larc(1,2,10,200)
        self.mapdl.l(2,4)
        self.mapdl.larc(3,4,11,40)
        self.mapdl.l(3,1)
        
        # self.mapdl.a(1,2,4,3)
        self.mapdl.al(1,2,3,4)
        
        # Meshing
        self.mapdl.lsel('s','line','',1)
        self.mapdl.lsel('a','line','',3)
        self.mapdl.lesize('all','','',15,-2)
        
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
    
        # Boundary conditions
        self.mapdl.nsel('s','loc','y',10)
        self.mapdl.d('all','all',0)
        
        # Write ANSYS Input file (Do not change!)
        # self.mapdl.allsel('all')
        # self.mapdl.cdwrite('all', ansys_input_filename, 'cdb')
        # self.mapdl.finish() # Todo: Dopplung vermeiden
        # self.mapdl.clear('nostart')
        
    def __calc_element_data__(self):
        
        self.mapdl.prep7()        
        
        data_array = []
        chord_vector = [] 
        alpha_vector = []
        enum = self.mapdl.mesh.enum
        
        for element in enum:
            self.mapdl.get('mp_x','elem',element,'cent','x')
            self.mapdl.get('mp_y','elem',element,'cent','y')
            self.mapdl.get('mp_z','elem',element,'cent','z')
            
            element_midpoint = np.array([self.mapdl.parameters['mp_x'],
                                         self.mapdl.parameters['mp_y'],
                                         self.mapdl.parameters['mp_z']])
                        
            leading_edge, trailing_edge, chordlength = \
                self.__get_edges__(element_midpoint[1])
                
            # Orthographic projection to get relative chord length:
            u = trailing_edge - leading_edge
            u = u/np.linalg.norm(u)
                
            lambda_ = np.dot(element_midpoint - leading_edge,u)/ \
                np.dot(u, u)
                
            projected_point = leading_edge + lambda_ * u
            
            relative_chord = np.linalg.norm(projected_point - leading_edge)/ \
                chordlength
                
            # relative Radius
            relative_radius = element_midpoint[1]/ \
                (self.propeller.parameters['tip_radius']*1000)
            relative_radius = np.round(relative_radius, 4)
            
            # section height
            coords, profiltropfen, camberline = self.propeller.get_airfoil(relative_radius)
            
            profiltropfen = profiltropfen.iloc[:profiltropfen['X'].idxmin(), :]
            empty_frame = pd.DataFrame([relative_chord], columns=['X'])
            empty_frame['Y'] = np.nan
            profiltropfen = profiltropfen.append(empty_frame)
            profiltropfen = profiltropfen.sort_values('X')
            profiltropfen = profiltropfen.interpolate()
            profiltropfen = profiltropfen.dropna()
            profiltropfen = profiltropfen.drop_duplicates(keep='first')
            
            sec_height = 2*np.array(profiltropfen[profiltropfen['X']==relative_chord]['Y'])[0]
            
            # element area
            element_area = self.mapdl.get('a', 'elem', element, 'area')
            
            # state
            state = self.propeller.state(relative_chord, relative_radius)
            
            # circular velocity
            f_max = max([float(i[1]['single_values']['rpm']) for i in self.propeller.loadcases])/60
            v_circ = 2*pi*element_midpoint[1]*f_max
            
            # air density
            rho = self.propeller.loadcases[0][1]['single_values']['rho(kg/m3)']
            rho = rho * 1e-12 # convert to tonne/mm^3
            
            # pressure 
            p = -(state['Cp_suc'] - state['Cp_pres']) * (rho/2) * v_circ**2  # Vorzeichen?
            
            # viscous drag
            nloc = [self.mapdl.get('nloc','node',node,'loc','x') for node in self.mapdl.mesh.elem[element-1][10:]]
            element_len_y = (element_area/ abs(max(nloc)-min(nloc)))/chordlength
            
            c_f = state['Cf']
            c_f_dx = state['Cf'] * element_len_y
            
            D_v = c_f_dx*element_area * (rho/2) * v_circ**2 
            
            # Angle ot attack
            alpha = np.deg2rad(state['alpha'])
            
            aoa = np.array([1,0,(np.cos(alpha)-u[0])/u[2]])
            aoa = aoa/np.linalg.norm(aoa)
            
            alpha_vector.append(aoa)
            
            data_array.append([element,
                               element_midpoint[0],
                               element_midpoint[1],
                               element_midpoint[2],
                               relative_chord,
                               chordlength,
                               relative_radius,
                               sec_height*chordlength,
                               element_area,
                               state['Cp_suc'],
                               state['Cp_pres'],
                               v_circ,
                               p,
                               state['Cd'],
                               c_f,
                               c_f_dx,
                               D_v,
                               state['alpha'],
                               ])
            
            chord_vector.append(u)
        
        data_array = np.array(data_array)
            
        df = pd.DataFrame(data_array, index=data_array[:,0], columns=['Element Number',
                                                                      'Midpoint X',
                                                                      'Midpoint Y',
                                                                      'Midpoint Z',
                                                                      'Relative Chord',
                                                                      'Chordlength',
                                                                      'Relative Radius',
                                                                      'Element height',
                                                                      'Element area',
                                                                      'Cp_suc',
                                                                      'Cp_pres',
                                                                      'Circular velocity',
                                                                      'Pressure by Lift',
                                                                      'Cd',
                                                                      'Cf',
                                                                      'Cf*dx',
                                                                      'Viscous Drag',
                                                                      'alpha',
                                                                      ])
            
        self.__element_data = df
        self.__element_chord_vector = chord_vector
        self.__element_aoa_vector = alpha_vector        
        
    def __apply_loads__(self):
        # Read ANSYS Input file (Do not change!)
        self.mapdl.prep7()
        # self.mapdl.cdread('all', ansys_input_filename, 'cdb')
        
        self.mapdl.fcum('add')
        self.mapdl.allsel('all')
        
        # Vary Geometry
        
        nodes_per_elem = len(self.mapdl.mesh.elem[1][10:])
        
        for element in self.element_data['Element Number']:            
            # assign lift
            self.mapdl.sfe(element,'','pres',1,self.element_data['Pressure by Lift'][element])
            
            # assign drag (distributed to the element's nodes)
            for node in self.mapdl.mesh.elem[int(element-1)][10:]:
                self.mapdl.f(node,'fx',self.element_aoa_vector[int(element-1)][0]*self.element_data['Viscous Drag'][element]/nodes_per_elem)
                self.mapdl.f(node,'fz',self.element_aoa_vector[int(element-1)][2]*self.element_data['Viscous Drag'][element]/nodes_per_elem)
            
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
        # self.mapdl.cdread('all', ansys_input_filename, 'cdb')
        
        self.mapdl.fcum('add')
        
        # Vary Geometry
        for element in self.element_data['Element Number']:
            self.mapdl.sectype(element,'shell','','')
            self.mapdl.secdata(self.element_data['Element height'][element],
                               1, # self.m_flaxpreg.number,
                               0., 
                               3)
            self.mapdl.emodif(element, 'secnum', element)
            
            # # assign lift
            # self.mapdl.sfe(element,'','pres',1,self.element_data['Pressure by Lift'][element])
            
            # # assign drag (distributed to the element's nodes)
            # for node in self.mapdl.mesh.elem[int(element-1)][10:]:
            #     self.mapdl.f(node,'fx',self.element_chord_vector[int(element-1)][0]*self.element_data['Drag'][element])
            #     self.mapdl.f(node,'fz',self.element_chord_vector[int(element-1)][2]*self.element_data['Drag'][element])
            
        self.mapdl.allsel('all')
        
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
        
        # self.mapdl.open_gui()
        
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
        
        self.__change_design_variables__()
        self.__solve__()
        f, g, h = self.__post_processing__()
        
        # Calculate objective Function and restrictions
        
        return f, g, h
    
    @property
    def element_data(self):
        return self.__element_data
    
    @property
    def element_aoa_vector(self):
        return self.__element_aoa_vector
    
    @property
    def element_chord_vector(self):
        return self.__element_chord_vector
    
    @property
    def materials(self):
        return self.__materials
    
    @materials.setter
    def materials(self, materials):
        self.__materials = materials
    
    def __get_edges__(self, y):
        
        def intersection(lnum):
            kp_0 =  100000
            kp_num = 5
            a_num = 2
            
            self.mapdl.prep7()
            
            self.mapdl.k(kp_0+1, -1000, y, -1000)
            self.mapdl.k(kp_0+2, 1000, y, -1000)
            self.mapdl.k(kp_0+3, 1000, y, 1000)
            self.mapdl.k(kp_0+4, -1000, y, 1000)
            
            self.mapdl.a(kp_0+1, kp_0+2, kp_0+3, kp_0+4)
                
            self.mapdl.lina(lnum, a_num)
            
            coords = []
            for axis in ['x','y','z']:
                self.mapdl.get('c', 'KP', kp_num, 'loc', axis)
                coords.append(self.mapdl.parameters['c'])
            
            self.mapdl.kdele(kp_num)
            
            return coords
    
        le = np.array(intersection(4))
        te = np.array(intersection(2))
        
        return le, te, np.linalg.norm(te - le)