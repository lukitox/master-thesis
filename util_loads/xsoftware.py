#%% Import Libraries and Data 

# Third-party imports
import os

# Local imports

#%%

class Xsoftware:
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
                
class Xfoil(Xsoftware):
    '''
    The interface class to XFOIL.
    
    XFOIL access works with a context manager:
    
    .. code-block:: python
    
        import util_loads as ux
        
        with ux.xfoil() as x:
            x.run('aero')
            #...
            x.run('quit')
    
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
        
class Xrotor(Xsoftware):
    '''
    The interface class to XROTOR.

    XROTOR access works with a context manager:
    
    .. code-block:: python
    
        import util_loads as ux
        
        with ux.xrotor(propeller= SomeProp, loadcase= 'SomeLoadcase') as x:
            x.run('atmo 0')
            #...
            x.run('quit')

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
        self.loadcase = loadcase
        
        self.flag_oper = False
        self.flag_bend = False
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)
        os.system('xrotor < ' + self.input_file)
        
        # if self.flag_oper == True: 
        #     self.loadcase.add_result_oper(self.oper_file)
        #     os.remove(self.oper_file)

        # if self.flag_bend == True:
        #     self.loadcase.add_result_bend(self.bend_file)
        #     os.remove(self.bend_file)
        
        os.remove(self.input_file)
    
    def arbi(self):
        '''
        Runs XROTOR's ARBI command and parses the given propeller geometry.
        
        .. code-block:: none
        
            ARBI   Input arbitrary rotor geometry
        
        Returns
        -------
        None.

        '''
        self.run('arbi')
        self.run(self.propeller.parameters['number_of_blades'])
        self.run(self.loadcase.parameters['flight_speed'])
        self.run(self.propeller.parameters['tip_radius'])
        self.run(self.propeller.parameters['hub_radius'])
        
        self.run(str(len(self.propeller.geometry)))
        self.run_array(self.propeller.geometry)
        self.run('n')
        
    def parse_airfoils(self):
        '''
        Enters XROTOR's AERO routine and parses the given propeller airfoil data
        
        .. code-block:: none
            
            .AERO   Display or change airfoil characteristics

        Returns
        -------
        None.

        '''
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
        '''
        Writes the output of XROTOR's OPER Routine to textfile and returns results to the given loadcase.
        
        .. code-block:: none
        
            .OPER   Calculate off-design operating points
            WRIT f  Write current operating point to disk file

        Returns
        -------
        None.

        '''
        self.run('writ ' + self.oper_file)
        self.flag_oper = True
    
    def write_bend(self):
        '''
        Writes the output of XROTOR's BEND Routine to textfile and returns results to the given loadcase.
        
        .. code-block:: none
        
            .BEND   Calculate structural loads and deflections
            WRIT f  Write structural solution to disk file

        Returns
        -------
        None.

        '''
        self.run('writ ' + self.bend_file)
        self.flag_bend = True    
        
    @staticmethod
    def read_bend_output(path):
        colspecs = [(1, 3), (4, 10), (11, 18), (19, 26), (28, 34), (35, 46), (48, 59), (61, 72), (74, 85), (87, 98), (100, 111)]
        tabular_data = pd.read_fwf(filename, colspecs=colspecs, header= [1], skiprows=[2], nrows= 29)
        
        return tabular_data
    
    @staticmethod
    def read_oper_output(path):
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
        
        return single_values, tabular_data