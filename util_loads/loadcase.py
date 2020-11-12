#%% Import Libraries and Data 

# Third-party imports
import pandas as pd

## Local imports

#%%

class Loadcase:
    """
    This class contains the loadcase Data.
    """

    def __init__(self, name, flight_speed):
        self.__name = name
        self.__flight_speed = flight_speed
        self.__data = None

        self.results = {}
        
    def __repr__(self):
        return str(self.__name) + ' ' + str(self.__data)
    
    @property
    def name(self):
        """
        
        Returns
        -------
        String
            Loadcase Name.

        """
        return self.__name
    
    @name.setter
    def name(self, name):
        self.__name = name
        
    @property
    def flight_speed(self):
        """
        
        Returns
        -------
        Float
            Flight speed.

        """
        return self.__flight_speed
    
    @flight_speed.setter
    def flight_speed(self, flight_speed):
        self.__flight_speed = flight_speed
        
    @property
    def data(self):
        """

        Returns
        -------
        List
            List of Loadcase parameters, also used as XRotor input.

        """
        return self.__data
    
    def set_data(self, prescribe_type, value, fix=None, value2=None):
        """
        
        Parameters
        ----------
        prescribe_type : String
            Type of Loadcase: 
                'adva' : Prescribe advance ratio [1]
                'rpm' : Prescribe rpm [1/min]
                'thru' : Prescribe thrust [N]
                'torq' : Prescribe torque [Nm]
                'powe' : Prescribe power [W]
        value : Float
            Value for given type.
        fix : String, optional
            Needed for 'thru', 'torq', 'powe'. The default is None.
                'p' : Fixed pitch
                'r' : Fixed rpm
        value2 : Float, optional
            RPM. Needed if 'fix' == r. The default is None.

        Returns
        -------
        None.

        """
        if prescribe_type.lower() == 'adva':
            self.__prescribe_type = 'adva'
            self.__value = value
        elif prescribe_type.lower() == 'rpm':
            self.__prescribe_type = 'rpm'
            self.__value = value
        elif prescribe_type.lower() == 'thru' \
        or prescribe_type.lower() == 'torq' \
        or prescribe_type.lower() == 'powe':
            self.__prescribe_type = prescribe_type.lower()
            self.__value = value
            if fix.lower() == 'p':
                self.__fix = fix
            elif fix.lower() == 'r':
                self.__fix = fix
                self.__value2 = value2
                if value2 == None:
                    raise ValueError('Invalid value2 %s' % value2)
            else:
                raise ValueError('Invalid fix %s' % fix)
                
        self.__data = [self.__prescribe_type, self.__value]
        if fix is not None:
            self.__data.append(self.__fix)
        if value2 is not None:
            self.__data.append(self.__value2)        