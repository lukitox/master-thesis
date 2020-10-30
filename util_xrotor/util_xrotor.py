'''
The interface module to XROTOR and XFOIL

'''
#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import pandas as pd
import os

#%% Interface Class to XRotor

class xsoftware:
    '''
    Parent of xfoil and xrotor class. This class contains all methods, that are common in xrotor and xfoil class.
    
    The interface is implemented as a Context Manager (ref: https://book.pythontips.com/en/latest/context_managers.html).
    
    '''
    
    def __enter__(self):
        '''Opens a text file, which will serve as input to XFOIL and XROTOR.'''
        
        self.f = open(self.input_file, 'w')
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        '''Closes the input file'''
        
        self.f.close()
        
    def run(self, argument):
        '''
        Basic method that writes all the commands into the input file and makes a line break after every command.

        Parameters
        ----------
        argument 
            XFOIL or XROTOR command. Will be converted to string type.

        Returns
        -------
        None.

        '''
        self.f.write(str(argument) + '\n')
    
    def run_array(self, array):
        '''
        Parses a numpy.array or list into the input file. This method is used for the propeller geometry input.

        Parameters
        ----------
        array : np.array or list
            array or list as input.

        Returns
        -------
        None.

        '''
        self.array = list(array)
        for rows in self.array:
            for columns in rows:
                self.run(str(columns))
                
    @staticmethod
    def _clean_up_():
        '''This method removes all input and result files. Currently unused.'''
        import glob
        
        searchterms = ['_xfoil*', '_xrotor', ':00.bl']
        
        for term in searchterms:
            filenames = glob.glob(term)
            
            for filename in filenames:
                os.remove(filename)

class xfoil(xsoftware):
    '''
    The interface class to XFOIL.
    '''
    
    def __init__(self):
        self.input_file = '_xfoil_input.txt'
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        '''
        Parameters
        ----------
        exc_type : TYPE
            DESCRIPTION.
        exc_value : TYPE
            DESCRIPTION.
        exc_traceback : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        super().__exit__(exc_type, exc_value, exc_traceback)
        os.system('xfoil < ' + self.input_file)
    
        os.remove(self.input_file)

class xrotor(xsoftware):
    '''
    The interface class to XROTOR.

    Parameters
    ----------
    propeller : Instance of propeller class
        Propeller to take geometry from.
    loadcase : Key of loadcase in propeller instance
        Loadcase to take parameters from and return results to.

    Returns
    -------
    None.
    '''
    def __init__(self, propeller, loadcase):

        self.input_file = '_xrotor_input.txt'
        self.oper_file  = '_xrotor_oper.txt'
        self.bend_file  = '_xrotor_bend.txt'  
        
        self.propeller = propeller
        self.loadcase = self.propeller.loadcases[loadcase]
        
        self.flag_oper = False
        self.flag_bend = False
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        os.system('xrotor < ' + self.input_file)
        
        if self.flag_oper == True: 
            self.loadcase.add_result_oper(self.oper_file)
            os.remove(self.oper_file)

        if self.flag_bend == True:
            self.loadcase.add_result_bend(self.bend_file)
            os.remove(self.bend_file)
        
        os.remove(self.input_file)
    
    def arbi(self):
        self.run('arbi')
        self.run(self.propeller.parameters['number_of_blades'])
        self.run(self.loadcase.parameters['flight_speed'])
        self.run(self.propeller.parameters['tip_radius'])
        self.run(self.propeller.parameters['hub_radius'])
        
        self.run(str(len(self.propeller.geometry)))
        self.run_array(self.propeller.geometry)
        self.run('n')
        
    def parse_airfoils(self):
        for index, section in enumerate(self.propeller.sections):
            self.run('aero')
            self.run('new')
            self.run(section[0])
            self.run('edit')
            self.run(index + 2)
            self.run('1')
            self.run(section[1].xrotor_characteristics['Zero-lift alpha (deg)'])
            self.run('2')
            self.run(section[1].xrotor_characteristics['d(Cl)/d(alpha)'])
            self.run('4')
            self.run(section[1].xrotor_characteristics['Maximum Cl'])
            self.run('5')
            self.run(section[1].xrotor_characteristics['Minimum Cl'])
            self.run('7')
            self.run(section[1].xrotor_characteristics['Minimum Cd'])
            self.run('8')
            self.run(section[1].xrotor_characteristics['Cl at minimum Cd'])
            self.run('9')
            self.run(section[1].xrotor_characteristics['d(Cd)/d(Cl**2)'])
            self.run('10')
            self.run(section[1].parameters['Re'])
            self.run('12')
            self.run(section[1].xrotor_characteristics['Cm'])
            self.run('')
            self.run('')
        
    def write_oper(self):
        self.run('writ ' + self.oper_file)
        self.flag_oper = True
    
    def write_bend(self):
        self.run('writ ' + self.bend_file)
        self.flag_bend = True        
        
#%% Propeller Class

class propeller:
    
    def __init__(self, number_of_blades, tip_radius, hub_radius):
        self.parameters = {
            'number_of_blades'  : number_of_blades,
            'tip_radius'        : tip_radius,
            'hub_radius'        : hub_radius,
            }    
        
        self.loadcases = {}
        
        self.sections = []
        
    def __repr__(self):
        return str(self.parameters)
        
    def geometry(self, data):
        self.geometry = data
        
    def add_loadcase(self, name, loadcase):
        self.loadcases[name] = loadcase
    
    def add_section(self, rR, airfoil):
        self.sections.append([rR, airfoil])
        self.sections.sort()
    
#%% Airfoil Class

class airfoil:
    
    def __init__(self, airfoil_filename, Re, Ncrit = 9, Iter = 200):
        self.parameters = {
            'airfoil_filename': airfoil_filename,
            'Re': Re,
            'Ncrit': Ncrit,
            'Iter': Iter,
            }
    
    def calculate_polar(self, alpha_start = -20, alpha_stop = 20, alpha_inc = 0.25):
        polar_file = '_xfoil_polar.txt'
        
        def clean_up():
            if os.path.exists(polar_file):
                os.remove(polar_file)
                
            if os.path.exists(':00.bl'):
                os.remove(':00.bl')
                
        clean_up()
        
        aseq = [[0, alpha_start, alpha_inc],
                [0, alpha_stop , alpha_inc]]
        
        for sequence in aseq:        
            with xfoil() as x:
                x.run('load ./util_xrotor/airfoil-database/' + self.parameters['airfoil_filename'])      ##### Todo: Relativer Pfad 
                x.run('pane')
                x.run('oper')
                x.run('vpar')
                x.run('n ' + str(self.parameters['Ncrit']))
                x.run('')
                x.run('visc ' + str(self.parameters['Re']))
                x.run('iter')
                x.run(str(self.parameters['Iter']))
                x.run('pacc')
                x.run(polar_file)
                x.run('')
                x.run('aseq ')
                x.run(sequence[0])
                x.run(sequence[1])
                x.run(sequence[2])
                x.run('')
                x.run('quit')
                
        colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46), (49, 55), (58, 64), (66, 73), (74, 82)]
        tabular_data = pd.read_fwf(polar_file, colspecs=colspecs, header= [10], skiprows=[11])
        tabular_data.sort_values('alpha', inplace=True)
        tabular_data.drop_duplicates(keep='first',inplace=True)
        tabular_data = tabular_data.reset_index()
        
        clean_up()
        
        self.polar = tabular_data
        self.__calculate_xrotor_parameters__()
        
    def __calculate_xrotor_parameters__(self):
        from scipy.optimize import curve_fit
        from scipy.signal import savgol_filter
                
        popt, pcov = curve_fit(self.__fit_cl_alpha__, np.array(self.polar['alpha']), np.array(self.polar['CL']))
        
        self.polar['fitted CL']         = self.__fit_cl_alpha__(np.array(self.polar['alpha']), *popt)
        self.polar['d(Cl)/d(alpha)']    = np.gradient(self.polar['fitted CL'], self.polar['alpha']).round(5)
        self.polar['filtered CD']       = savgol_filter(self.polar['CD'],  window_length=11, polyorder=2)
        self.polar['d(Cd)/d(Cl**2)']    = np.gradient(np.gradient(self.polar['filtered CD'], self.polar['CL']), self.polar['CL'])
        
        self.xrotor_characteristics = {
            'Zero-lift alpha (deg)' : float(-self.polar['fitted CL'][self.polar[self.polar['alpha'] == 0].index.values] / self.polar['d(Cl)/d(alpha)'].max()),
            'd(Cl)/d(alpha)'        : self.polar['d(Cl)/d(alpha)'].max() * 180/3.1416,           
            'Maximum Cl'            : self.polar['CL'].max(),
            'Minimum Cl'            : self.polar[self.polar['d(Cl)/d(alpha)'] == self.polar['d(Cl)/d(alpha)'].max()]['fitted CL'].min(), 
            'Minimum Cd'            : self.polar['CD'].min(),
            'Cl at minimum Cd'      : self.polar['CL'][self.polar.idxmin()['CD']],
            'd(Cd)/d(Cl**2)'        : self.polar['d(Cd)/d(Cl**2)'][self.polar.idxmin()['CD']],
            'Cm'                    : self.polar['CM'].min(),
            }                     
                             
    def __fit_cl_alpha__(self, x, x0, x1, a3, b1, b3, c2):
        b2 = 2*a3*x1 + b3
        c1 = b2*x0 - b1*x0 + c2
        c3 = b2*x1 + c2 - a3*x1**2 - b3*x1
        return np.piecewise(x, [x < x0, (x >= x0) & (x < x1), x > x1], [lambda x: b1*x + c1,
                                                                        lambda x: b2*x + c2,
                                                                        lambda x: a3*x**2 + b3*x + c3])
    
#%% Loadcase Class

class loadcase:

    def __init__(self, flight_speed, rpm):
        self.parameters = {
            'flight_speed': flight_speed,
            'rpm': rpm,
            }

        self.results = {}
        
    def __repr__(self):
        return str(self.parameters)
        
    def add_result_oper(self, filename):
        single_values = {}
        columns = [[(1, 12), (15, 24)], [(28, 39), (42, 51)], [(54, 65), (69, 78)]]
        for colspec in columns:
            header = pd.read_fwf(filename, colspecs=colspec, header=0, skiprows=3, nrows = 7, index_col=0)
            header.columns = ['Value']
            header.dropna(subset = ['Value'], inplace=True)
            header = header.to_dict()['Value']
            single_values.update(header)
    
        colspecs = [(1, 4), (4, 9), (10, 16), (16, 25), (25, 30), (33, 39), (40, 47), (48, 53), (54, 60), (61, 66), (67, 74)]
        tabular_data = pd.read_fwf(filename, colspecs=colspecs, header= 16)
        
        self.results['oper'] = [single_values, tabular_data]

    def add_result_bend(self, filename):
        colspecs = [(1, 3), (4, 10), (11, 18), (19, 26), (28, 34), (35, 46), (48, 59), (61, 72), (74, 85), (87, 98), (100, 111)]
        tabular_data = pd.read_fwf(filename, colspecs=colspecs, header= [1], skiprows=[2], nrows= 29)
        
        self.results['bend'] = tabular_data
