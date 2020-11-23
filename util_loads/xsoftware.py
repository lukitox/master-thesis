#%% Import Libraries and Data 

# Third-party imports
import os
import subprocess
import warnings

# Local imports

#%%


class Xsoftware:
    """
    Parent of xfoil and xrotor class. This class contains all methods, 
    that are common in xrotor and xfoil class.

    The interface is implemented as a Context Manager
    (ref: https://book.pythontips.com/en/latest/context_managers.html).

    """

    def __init__(self):
        self.input_file = None
        self.name = None

    def __enter__(self):
        """Opens a text file, which will serve as input to XFOIL and XROTOR."""
        
        self.f = open(self.input_file, 'w')
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Closes the input file, and starts the Xfoil/ Xrotor Job. """
        
        self.f.close()
        
        if self.mode == 'hide':
            sp_stdout = subprocess.DEVNULL
            sp_stderr = subprocess.STDOUT
        elif self.mode == 'show':
            sp_stdout = None
            sp_stderr = None
        else:
            raise ValueError('Invalid mode %s' % self.mode)

        # args = ['Xvfb :1 &',
        #         'DISPLAY=:1 xfoil < ' + self.input_file,
        #         'kill -15 $!']
        
        args = [self.name + ' < ' + self.input_file,]
        
        process = subprocess.Popen(args,
                                   shell=True,
                                   stdout=sp_stdout,
                                   stderr=sp_stderr,
                                   )
        try: 
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            warnings.warn(self.name + ' timed out - killing.',RuntimeWarning)
            process.kill()
        
        os.remove(self.input_file)
        
    def run(self, argument):
        """
        Basic method that writes all the commands into the input file and 
        makes a line break after every command.

        Parameters
        ----------
        argument
            XFOIL or XROTOR command. Will be converted to string type.

        """
        self.f.write(str(argument) + '\n')
    
    def run_array(self, array):
        """
        Parses a numpy.array or list into the input file. This method is used 
        for the propeller geometry input.

        Parameters
        ----------
        array : np.array or list
            array or list as input.

        """
        for rows in list(array):
            for columns in rows:
                self.run(str(columns))
