#%% Import Libraries and Data 

# Third-party imports
import os

# Local imports

#%%

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