#%% Import Libraries and Data 

# Third-party imports
import os

## Local imports
from .xsoftware import xsoftware

#%%

class xrotor(xsoftware):
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