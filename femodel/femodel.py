# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pandas as pd
from math import pi

# Local imports
from util_mapdl import Material
from util_mapdl.post_functions import fc_puck

# %%


class Femodel:
    """
    Parent Class of the FE-Model. This Class contains all permanent, 
    non-changing methods around the Propeller Models.
    """
    
# %% Private Methods    
    
    def __init__(self, mapdl, propeller, n_sec, mesh_density_factor = 1):
        
        # Mapdl instance: 
        self.mapdl = mapdl
        # Propeller instance:
        self.propeller = propeller
        # Number of sections for optimization:
        self.n_sec = n_sec
        # Allocation for Properties:
        self.__element_data = None
        self.__element_chord_vector = None
        self.__element_aoa_vector = None
        # Name of the .cdb file
        self.__ansys_input_filename = '_ansys_input_file'
        
        self.__mesh_density_factor = mesh_density_factor
        
# %% User-defined private Methods
        
    def __apply_loads__():
        """
        This method is unique to the examined propelles and therefore has to
        be implemented in an inheriting class.

        """
        pass

    def __calc_element_data__(self):
        """
        This method gathers all necessary element data for assigning
        the loads.
        
        """
        
        self.mapdl.prep7()        
        
        data_array = []
        chord_vector = [] 
        alpha_vector = []
        
        for element in self.mapdl.mesh.enum:
            ## Center point of element
            self.mapdl.get('mp_x','elem',element,'cent','x')
            self.mapdl.get('mp_y','elem',element,'cent','y')
            self.mapdl.get('mp_z','elem',element,'cent','z')
            
            element_midpoint = np.array([self.mapdl.parameters['mp_x'],
                                         self.mapdl.parameters['mp_y'],
                                         self.mapdl.parameters['mp_z']])
            
            ## Leading and trailing edge coords:
            leading_edge, trailing_edge, chordlength = \
                self.__get_edges__(element_midpoint[1])
                
            ## Get section of element:
            n_sec = np.floor(((element_midpoint[1] 
                              - self.propeller.parameters['hub_radius']*1000)
                             / ((self.propeller.parameters['tip_radius']
                                 - self.propeller.parameters['hub_radius'])
                                * 1000)) * self.n_sec)
                
            ## Orthographic projection to get normalized chord length:
            # (Der 'element_midpoint' wird auf die Profilsehne projeziert)   
             
            # LE-TE = LE + lambda_ * u
            u = ((trailing_edge - leading_edge)
                 / np.linalg.norm(trailing_edge - leading_edge))
            
            lambda_ = (np.dot(element_midpoint - leading_edge, u)
                       / np.dot(u, u))
                
            projected_point = leading_edge + lambda_ * u
            
            ## Normalized chord length: 
            rel_chord = (np.linalg.norm(projected_point - leading_edge)
                              / chordlength)
                
            ## Normalized radial station:
            rel_radius = (element_midpoint[1]
                          / (self.propeller.parameters['tip_radius'] * 1000))
                            
            ## Element height:
            # Symmetric airfoil coords:
            _, profiltropfen, camber = self.propeller.get_airfoil(rel_radius)
            
            # Use only the top half of the points
            profiltropfen = profiltropfen.iloc[:profiltropfen['X'].idxmin(), :]
            
            # Append rel_chord to the DataFrame and interpolate its value
            empty_frame = pd.DataFrame([rel_chord], columns=['X'])
            empty_frame['Y'] = np.nan
            profiltropfen = profiltropfen.append(empty_frame)
            profiltropfen = profiltropfen.sort_values('X')
            profiltropfen = profiltropfen.interpolate()
            profiltropfen = profiltropfen.dropna()
            profiltropfen = profiltropfen.drop_duplicates(keep='first')
            
            # Camberline calculation for SECOFFSET:
            camber = camber.iloc[:camber['X'].idxmin(), :]

            camber = camber.append(empty_frame)
            camber = camber.sort_values('X')
            camber = camber.interpolate()
            camber = camber.dropna()
            camber = camber.drop_duplicates(keep='first')
            
            # Element height:
            elem_height = 2 * \
                np.array(profiltropfen[profiltropfen['X']==rel_chord]['Y'])[0]
                
            secoffset = -1 * np.array(camber[camber['X'] == rel_chord]['Y'])[0]
            
            ## Element area:
            element_area = self.mapdl.get('a', 'elem', element, 'area')
            
            ## Element state (contains: Cl, Cd, alpha, Re, both Cps, Cf):
            elem_state = self.propeller.state(rel_chord, rel_radius)
            
            ## Circular velocity of the Elements radial position:
            # Get the highest rpm in Loadcases
            f_max = max([float(i[1]['single_values']['rpm']) 
                         for i in self.propeller.loadcases]) / 60
            
            v_circ = 2 * pi * element_midpoint[1] * f_max
            
            ## Density of Air:
            rho = self.propeller.loadcases[0][1]['single_values']['rho(kg/m3)']
            rho = rho * 1e-12 # convert to tonne/mm^3
            
            ## Get the elements air pressure:
            # P = Cp * q
            elem_pressure = - ((elem_state['Cp_suc'] - elem_state['Cp_pres']) 
                               * (rho/2) 
                               * v_circ**2)
            
            ## Element viscous drag: ### Todo: Bug? x/y vertauschen
            # Y coordinates of the elements nodes
            nloc = [self.mapdl.get('nloc','node',node,'loc','y') 
                    for node in self.mapdl.mesh.elem[element-1][10:]]
            # Normalized average X dimensions:
            elem_dx = ((element_area / abs(max(nloc)-min(nloc)))
                             / chordlength)
            
            # Element viscous drag:
            visc_drag = ((elem_state['Cf'] * elem_dx)
                         * element_area
                         * (rho/2) 
                         * v_circ**2)
                        
            ## Angle ot attack
            # in rad:
            alpha = np.deg2rad(elem_state['alpha'])
            # vectorial:
            aoa = np.array([1,0,(np.cos(alpha)-u[0])/u[2]])
            aoa = aoa/np.linalg.norm(aoa)
            
            ## Append all the data:
            alpha_vector.append(aoa)
            
            chord_vector.append(u)       
            
            data_array.append([int(element),
                               int(n_sec),
                               np.round(element_midpoint[0],3),
                               np.round(element_midpoint[1],3),
                               np.round(element_midpoint[2],3),
                               np.round(rel_chord,3),
                               np.round(chordlength,3),
                               np.round(rel_radius,4),
                               np.round(elem_height*chordlength,3),
                               np.round(secoffset*chordlength,3),
                               np.round(element_area,3),
                               np.round(elem_state['Cp_suc'],3),
                               np.round(elem_state['Cp_pres'],3),
                               np.round(v_circ,3),
                               elem_pressure,
                               elem_state['Cl'],
                               elem_state['Cd'],
                               elem_state['Cf'],
                               elem_state['Cf'] * elem_dx,
                               visc_drag,
                               elem_state['alpha'],
                               ])
            
        
        data_array = np.array(data_array, dtype=object)
            
        df = pd.DataFrame(data_array,
                          index=data_array[:,0],
                          columns=['Element Number',
                                   'Section Number',
                                   'Midpoint X',
                                   'Midpoint Y',
                                   'Midpoint Z',
                                   'Relative Chord',
                                   'Chordlength',
                                   'Relative Radius',
                                   'Element height',
                                   'Element offset',
                                   'Element area',
                                   'Cp_suc',
                                   'Cp_pres',
                                   'Circular velocity',
                                   'Pressure by Lift',
                                   'Cl',
                                   'Cd',
                                   'Cf',
                                   'Cf*dx',
                                   'Viscous Drag',
                                   'alpha',
                                   ])
            
        self.__element_data = df
        self.__element_chord_vector = chord_vector
        self.__element_aoa_vector = alpha_vector
        
    def __define_and_mesh_geometry__():
        """
        This method is unique to the examined propelles and therefore has to
        be implemented in an inheriting class.

        """
        pass
        
    def __get_edges__(self, y):
        """
        Get the leading and trailing edge coordinates.

        Parameters
        ----------
        y : float
            Spanwise coordinate.

        Returns
        -------
        le : np.array
            Leading edge point.
        te : np.array
            Trailing edge point.
        chordlength : float
            Length of the connection vector.

        """
        
        def intersection(lnum):
            kp_0 =  100000
            kp_num = 5
            a_num = 4
            
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
        
        le_lines = [5,6,7]
        te_lines = [2,3,12]
        
        if y <= 92:
            le_line = le_lines[0]
            te_line = te_lines[0]
        elif y <= 390:
            le_line = le_lines[1]
            te_line = te_lines[1]     
        else:
            le_line = le_lines[2]
            te_line = te_lines[2]
    
        le = np.array(intersection(le_line))
        te = np.array(intersection(te_line))
        
        return le, te, np.linalg.norm(te - le)
        
# %% Public Methods

    def cdread(self):
        """
        Read in the .cdb database file generated by the pre-processing 
        method.

        """
        
        self.mapdl.prep7()
        self.mapdl.cdread('all', self.__ansys_input_filename, 'cdb')

    def change_design_variables(self, global_vars, *args):
        """
        This method is unique to the examined propelles and therefore has to
        be implemented in an inheriting class.

        """
        pass

    def clear(self):
        """Resets the MAPDL Session. """
        
        self.mapdl.finish()
        self.mapdl.clear('NOSTART')
        
    def evaluate():
        """
        This method is unique to the examined propelles and therefore has to
        be implemented in an inheriting class.

        """
        pass        

    def pre_processing(self):
        """
        This method does all preprocessing, except for the geometry variation.
        It executes the following methods in sequence:
            - __define_and_mesh_geometry__()
            - __calc_element_data__()
            - __apply_loads__()

        After that, it writes the model to a .cdb file and clears it.

        """
        self.__define_and_mesh_geometry__()
        self.__calc_element_data__()
        self.__apply_loads__()
        
        self.mapdl.allsel('all')
        self.mapdl.cdwrite('all', self.__ansys_input_filename, 'cdb')
        self.mapdl.finish()
        self.mapdl.clear('nostart')
        
    def post_processing(self):
        """
        This method is unique to the examined propelles and therefore has to
        be implemented in an inheriting class.

        """
        pass
        
    def __solve__(self):
        """Solve the FE-Model. """
        
        self.mapdl.run('/SOLU')
        self.mapdl.antype('static')
        self.mapdl.outres('all','all')
        self.mapdl.solve()
        self.mapdl.finish()
    

# %% Properties
        
    @property
    def element_data(self):
        """
        Big DataFrame with all important Data mapped onto the elements.
        (Pressure Distribution, Drag, Circular Velocity, Section IDs...)

        Returns
        -------
        element_data : DataFrame

        """
        return self.__element_data
    
    @property
    def element_aoa_vector(self):
        """
        The angle of attack data for all elements. This array is needed to 
        assign the viscous drag's direction.

        Returns
        -------
        element_aoa_vector : np.array

        """
        return self.__element_aoa_vector
    
    @property
    def element_chord_vector(self):
        """
        Vecor data of the chordline directions.

        Returns
        -------
        element_chord_vector : np.array

        """
        return self.__element_chord_vector
    
    @property
    def materials(self):
        """
        The Materials assigned to the Model.

        Returns
        -------
        materials : Dict

        """
        return self.__materials
    
    @materials.setter
    def materials(self, materials):
        self.__materials = materials
        
        for key in materials:
            self.__materials[key].load_from_db()
            
    @property
    def mesh_density_factor(self):
        """
        Integer factor to control the mesh density.

        Returns
        -------
        mesh_density_factor : int

        """
        return self.__mesh_density_factor
            
    @mesh_density_factor.setter
    def mesh_density_factor(self, mesh_density_factor):
        self.__mesh_density_factor = mesh_density_factor
