#%% Import Libraries and Data 

# Third-party imports

## Local imports

#%%

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