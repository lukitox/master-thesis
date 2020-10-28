#%% Import Libraries and Data 

# Third-party imports
import numpy as np
import pandas as pd
import os

#%% Interface Class to XRotor

class xsoftware:
    
    def __enter__(self):
        self.f = open(self.input_file, 'w')
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.f.close()
        
    def run(self, argument):
        self.f.write(str(argument) + '\n')
    
    def run_array(self, array):
        self.array = list(array)
        for rows in self.array:
            for columns in rows:
                self.run(str(columns))
                
    @staticmethod
    def _clean_up_():
        import glob
        
        searchterms = ['_xfoil*', '_xrotor', ':00.bl']
        
        for term in searchterms:
            filenames = glob.glob(term)
            
            for filename in filenames:
                os.remove(filename)

class xfoil(xsoftware):
    
    def __init__(self):
        self.input_file = '_xfoil_input.txt'
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        os.system('xfoil < ' + self.input_file)
    
        os.remove(self.input_file)

class xrotor(xsoftware):
    
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
        
    def write_oper(self):
        self.run('writ ' + self.oper_file)
        self.flag_oper = True
    
    def write_bend(self):
        self.run('writ ' + self.bend_file)
        self.flag_bend = True        
        
#%% Propeller Class

class propeller:
    
    def __init__(self, number_of_blades, tip_radius, hub_radius):
        self.parameters = {}
        self.parameters['number_of_blades'] = number_of_blades
        self.parameters['tip_radius'] = tip_radius
        self.parameters['hub_radius'] = hub_radius
        
        self.loadcases = {}
        
    def __repr__(self):
        return str(self.parameters)
        
    def geometry(self, data):
        self.geometry = data
        
    def add_loadcase(self, name, loadcase):
        self.loadcases[name] = loadcase
        pass
    
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
        
        if os.path.exists(polar_file):
            os.remove(polar_file)
            
        if os.path.exists(polar_file):
            os.remove(polar_file)
        
        aseq = [[0, alpha_start, alpha_inc],
                [0, alpha_stop , alpha_inc]]
        
        for sequence in aseq:        
            with xfoil() as x:
                x.run('load ./airfoil-database/' + self.parameters['airfoil_filename'])
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
        
        self.polar = tabular_data            
    
    
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
