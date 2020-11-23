# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pandas as pd
import bisect

# Local imports
from .xrotor import Xrotor
from .support import cleanup
from .airfoil import Airfoil

#%%


class Propeller:

    def __init__(self, number_of_blades, tip_radius, hub_radius):
        self.parameters = {'number_of_blades': number_of_blades,
                           'tip_radius': tip_radius,
                           'hub_radius': hub_radius,
                           }

        self.__loadcases = []
        self.__load_envelope = {}
        self.__geometry = []
        self.__sections = []

    def __repr__(self):
        return str(self.parameters)

    @cleanup
    def calc_loads(self):

        oper_file = '_xrotor_oper.txt'
        bend_file = '_xrotor_bend.txt'

        for loadcase, result in self.loadcases:
            with Xrotor(self, loadcase) as x:
                x.run('atmo 0')  # Set fluid properties from ISA 0km
                x.arbi()  # Input arbitrary rotor geometry
                x.parse_airfoils()
                x.run('oper')  # Calculate off-design operating points
                x.run('iter')
                x.run(200)
                for field in loadcase.data:
                    x.run(field)
                x.run('writ ' + oper_file)
                x.run('o')
                x.run('')  # return
                x.run('bend')  # Write current operating point to disk file
                x.run('eval')  # Evaluate structural loads and deflections
                x.run('writ ' + bend_file)
                x.run('o')
                x.run('')  # return
                x.run('quit')  # Exit program

            result['single_values'], result['oper'] = Xrotor.read_oper_output(oper_file)
            result['bend'] = Xrotor.read_bend_output(bend_file)

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
            raise TypeError('Must be list or np.array')

    @property
    def load_envelope(self):
        return self.__load_envelope

    def set_load_envelope(self):
        loads = [i[1] for i in self.loadcases]

        bend = [i['bend'] for i in loads]
        oper = [i['oper'] for i in loads]
        # single_values = [i['single_values'] for i in loads]

        def envelope(loadcase_list):
            return pd.concat(loadcase_list).groupby(level=0).max()

        self.__load_envelope = {'bend': envelope(bend),
                                'oper': envelope(oper),
                                # 'single_values': envelope(single_values),
                                }
        
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

    def pressure_distribution(self, loadcase):
        
        if loadcase == 'envelope':
            df = self.load_envelope['oper']
        else:
            df = self.loadcases[loadcase][1]['oper']
        
        stations = list(df['r/R']) # np.linspace(0.1,1,19)
        
        Cp_suc = np.zeros([99, len(stations)])
        Cp_pres = np.zeros([99, len(stations)])
        
        for idx, section in enumerate(stations):
            if section <= self.sections[0][0]:
                airfoil = self.sections[0][1]
                
                pressures = airfoil.cp_vs_x('cl', df['CL'][idx],[1,1])
            elif section >= self.sections[len(self.sections)-1][0]:
                airfoil = self.sections[len(self.sections)-1][1]
                
                pressures = airfoil.cp_vs_x('cl', df['CL'][idx],[1,1])
            else:
                index = bisect.bisect([x[0] for x in self.sections],section)
                left_section = self.sections[index-1]
                right_section = self.sections[index]
                
                fraction = (section - left_section[0])/ \
                    (right_section[0] - left_section[0])
                    
            #     airfoil = Airfoil('interpolated', df['REx10^3'][idx]*1000) 
                
            #     coords, profiltropfen, camberline = Airfoil.interpolate(left_section[1],
            #                                                             right_section[1],
            #                                                             fraction)
                
            #     airfoil.coordinates = coords
            
            # pressures = airfoil.cp_vs_x('cl', df['CL'][idx],[0,0])
            
                pressures = left_section[1].cp_vs_x('cl', df['CL'][idx],[1,1])*(1-fraction)+\
                    right_section[1].cp_vs_x('cl', df['CL'][idx],[1,1])*(fraction)
            
            Cp_suc[:,idx] = pressures['Cp_suc']
            Cp_pres[:,idx] = pressures['Cp_pres']
        
        X, Y = np.meshgrid(stations, np.arange(0.01, 1.00, 0.01))
        
        return X, Y, Cp_suc, Cp_pres

    @property
    def sections(self):
        """
        
        Returns
        -------
        List
            Aifoil sections. [r/R, Airfoil]

        """
        return self.__sections
    
    @sections.setter
    def sections(self, array):
        self.__sections = array

    def add_section(self, rR, airfoil):
        self.sections.append([rR, airfoil])
        self.sections.sort()