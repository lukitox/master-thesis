#%% Import Libraries and Data 

# Third-party imports
import pandas as pd

## Local imports

#%%

class Loadcase:

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

# Todo: Methode für einhüllenden Lastverlauf