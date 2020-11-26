#%% Import Libraries and Data 

# Third-party imports
import pathlib

# Local imports

# %%


class Material:
    
    def __init__(self, mapdl, name, number):
        self.mapdl  = mapdl
        self.__name   = name
        self.__number = number
        self.__path = str(pathlib.Path(__file__).parent.absolute())
        print(self.__path)
        
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, name):
        self.__name = name
        
    @property
    def number(self, number):
        return self.__number
    
    @number.setter
    def number(self, number):
        self.__number = number
    
    def read_csv(self, csvfile):
        import csv
        with open(csvfile, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            MP = {}
            FC = {}
            for row in reader:
                if str(row[0]).upper() == 'MP':
                    MP[str(row[1])] = float(row[2])
                    
                elif str(row[0]).upper() == 'FC':
                    FC[str(row[1])] = float(row[2]) 
                
                else: print('Fehler beim Einlesen, Typ nicht erkannt!')
                
        self.mp = MP
        self.fc = FC
        # other hinzufügen?
        
    def save_to_db(self):
        import json
        with open(self.__path+'/material-database/'+str(self.name)+'_mp_.json', 'w') as fp:
            json.dump(self.mp, fp)
        with open(self.__path+'/material-database/'+str(self.name)+'_fc_.json', 'w') as fp:
            json.dump(self.fc, fp)            
            
    def load_from_db(self):
        import json
        with open(self.path+'/material-database/'+str(self.name)+'_mp_.json', 'r') as fp:
            self.mp = json.load(fp)
        with open(self.path+'/material-database/'+str(self.name)+'_fc_.json', 'r') as fp:
            self.fc = json.load(fp)
        
    def assign_mp(self):
        for x in self.mp:
            self.mapdl.mp(str(x),self.number,self.mp[x])
    
    def assign_fc(self):
        for x in self.fc:
            #mapdl.fc('1','s','xten',286)
            self.mapdl.fc(self.number,'s',str(x),str(self.fc[x]))
