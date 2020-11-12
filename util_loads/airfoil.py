"""Airfoil class."""

# %% Import Libraries and Data

# Third-party imports
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter

# Local imports
from .xfoil import Xfoil

# %%

def clean_up(filename):
    if os.path.exists(filename):
        os.remove(filename)

class Airfoil:
    """
    The airfoil class.

    Parameters
    ----------
    airfoil_filename : string
        Name of airfoil. If coordinate file is stored in 'airfoil-database' folder, coordinates will be set.
    Re : int or float
        Reynolds number
    Ncrit : int or float, optional
        Ncrit value for XFOIL which affects Transition. The default is 9.
    Iter : int, optional
        Viscous-solution iteration limit. The default is 200.

    Returns
    -------
    None.

    """

    def __init__(self, airfoil_filename, Re, Ncrit=9, Iter=200):
        self.__parameters = {
            'airfoil_filename': airfoil_filename,
            'Re': Re,
            'Ncrit': Ncrit,
            'Iter': Iter,
            }
        self.__polar = None
        self.__xrotor_characteristics = None
        
        if os.path.exists('./util_loads/airfoil-database/' + self.__parameters['airfoil_filename']):
            self.coordinates = './util_loads/airfoil-database/' + self.__parameters['airfoil_filename']
        else:
            self.__coordinates = None
            
    def __repr__(self):
        return str(self.parameters)
            
    @property
    def coordinates(self):
        """
        Return Dataframe of airfoil coordinates
        
        Returns
        -------
        DataFrame
        
        """
        return self.__coordinates
    
    @coordinates.setter
    def coordinates(self, coordinates):
        if type(coordinates) == str:
            df = pd.read_fwf(coordinates,
                             header = 0,
                             names=['X','Y'],
                             )
            self.__coordinates = df.dropna()
        elif type(coordinates) == type(pd.DataFrame()):
            self.__coordinates = coordinates
        else:
            raise TypeError
            
    @property
    def xrotor_characteristics(self):
        """
        Returns airfoil characteristics dictionary for XROTOR.

        Returns
        -------
        dict : int or float

        Parameters
        ----------
        Zero-lift alpha (deg)
        d(Cl)/d(alpha)
        Maximum Cl
        Minimum Cl
        Minimum Cd
        Cl at minimum Cd
        d(Cd)/d(Cl**2)
        Cm

        """
        return self.__xrotor_characteristics
    
    @property
    def parameters(self):
        """
        Return parameters dictionary.

        Returns
        -------
        dict : string or int or float

        Parameters
        ----------
        airfoil_filename : string,\n
        Re : int or float,\n
        Ncrit : int or float,\n
        Iter : int

        """
        return self.__parameters
        
    @property
    def polar(self):
        """
        Return Polar Dataframe.

        Returns
        -------
        DataFrame
        
        """
        return self.__polar
    
    def set_polar(self, alpha_start=-20, alpha_stop=20, alpha_inc=0.25):
        """
        Calculate airfoil polar and store as pandas dataframe.
        Calculate Xrotor Characteristics.

        Parameters
        ----------
        alpha_start : int or float, optional
            first alpha value (deg). The default is -20.
        alpha_stop : int or float, optional
            last  alpha value (deg). The default is 20.
        alpha_inc : int or float, optional
            alpha increment. The default is 0.25.

        Returns
        -------
        None.

        """
        polar_file = '_xfoil_polar.txt'
    
        coordinates_file = '_xfoil_input_coords.txt'
        clean_up(coordinates_file)
        np.savetxt(coordinates_file, np.array(self.coordinates), fmt='%9.8f')

        clean_up(polar_file)
        clean_up(':00.bl')
        
        aseq = [[0, alpha_start, alpha_inc],
                [0, alpha_stop, alpha_inc]]

        for sequence in aseq:
            with Xfoil() as x:
                x.run('load ')
                x.run(coordinates_file)
                x.run('')
                # x.run('load ./util_loads/airfoil-database/' +
                #      self.__parameters['airfoil_filename'])  # Todo: Relativer Pfad
                x.run('pane')
                x.run('oper')
                x.run('vpar')
                x.run('n ' + str(self.__parameters['Ncrit']))
                x.run('')
                x.run('visc ' + str(self.__parameters['Re']))
                x.run('iter')
                x.run(str(self.__parameters['Iter']))
                x.run('pacc')
                x.run(polar_file)
                x.run('')
                x.run('aseq ')
                x.run(sequence[0])
                x.run(sequence[1])
                x.run(sequence[2])
                x.run('')
                x.run('quit')
                
        colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46),
                    (49, 55), (58, 64), (66, 73), (74, 82)]
        tabular_data = pd.read_fwf(polar_file,
                                   colspecs=colspecs,
                                   header=[10],
                                   skiprows=[11])
        tabular_data.sort_values('alpha', inplace=True)
        tabular_data.drop_duplicates(keep='first', inplace=True)
        tabular_data = tabular_data.reset_index()

        clean_up(coordinates_file)
        clean_up(polar_file)
        clean_up(':00.bl')

        self.__polar = tabular_data

        # Set Xrotor_characteristics
        
        popt, pcov = curve_fit(self.__fit_cl_alpha__,
                               np.array(self.__polar['alpha']),
                               np.array(self.__polar['CL']))

        self.__polar['fitted CL'] = self.__fit_cl_alpha__(np.array(self.__polar['alpha']), *popt)
        self.__polar['d(Cl)/d(alpha)'] = np.gradient(self.__polar['fitted CL'], self.__polar['alpha']).round(5)
        self.__polar['filtered CD'] = savgol_filter(self.__polar['CD'],  window_length=11, polyorder=2)
        self.__polar['d(Cd)/d(Cl**2)'] = np.gradient(np.gradient(self.__polar['filtered CD'], self.__polar['CL']), self.__polar['CL'])

        self.__xrotor_characteristics = {
            'Zero-lift alpha (deg)': float(-self.__polar['fitted CL'][self.__polar[self.__polar['alpha'] == 0].index.values] / self.__polar['d(Cl)/d(alpha)'].max()),
            'd(Cl)/d(alpha)': self.__polar['d(Cl)/d(alpha)'].max() * 180/3.1416,
            'Maximum Cl': self.__polar['CL'].max(),
            'Minimum Cl': self.__polar[self.__polar['d(Cl)/d(alpha)'] == self.__polar['d(Cl)/d(alpha)'].max()]['fitted CL'].min(), 
            'Minimum Cd': self.__polar['CD'].min(),
            'Cl at minimum Cd': self.__polar['CL'][self.__polar.idxmin()['CD']],
            'd(Cd)/d(Cl**2)': self.__polar['d(Cd)/d(Cl**2)'][self.__polar.idxmin()['CD']],
            'Cm': self.__polar['CM'].min(),
            }

    def __fit_cl_alpha__(self, x, x0, x1, a3, b1, b3, c2):
        b2 = 2*a3*x1 + b3
        c1 = b2*x0 - b1*x0 + c2
        c3 = b2*x1 + c2 - a3*x1**2 - b3*x1
        return np.piecewise(x, [x < x0, (x >= x0) & (x < x1), x > x1], [lambda x: b1*x + c1,
                                                                        lambda x: b2*x + c2,
                                                                        lambda x: a3*x**2 + b3*x + c3])
    
    def cp_vs_x(self, mode, value):
        """
        Returns the pressure distribution. Available modes:

        Parameters
        ----------
        mode : string.
            'alfa' for Angle of attack.
            'cl' for Coefficient of lift.
            'cli' for Coefficient of lift, inviscid.
        value : int or float

        Returns
        -------
        DataFrame
            Pressure distribution.

        """
        coordinates_file = '_xfoil_input_coords.txt'
        clean_up(coordinates_file)
        
        np.savetxt(coordinates_file, np.array(self.coordinates), fmt='%9.8f')
        
        cp_vs_x_file = '_xfoil_cpvsx.txt'
        clean_up(cp_vs_x_file)
        
        with Xfoil() as x:
            x.run('load ')
            x.run(coordinates_file)
            x.run('')
            x.run('pane')
            x.run('oper')
            x.run('vpar')
            x.run('n ' + str(self.__parameters['Ncrit']))
            x.run('')
            x.run('visc ' + str(self.__parameters['Re']))
            x.run('iter')
            x.run(str(self.__parameters['Iter']))
            x.run(mode)
            x.run(value)
            x.run('cpwr')
            x.run(cp_vs_x_file)
            x.run('')
            x.run('quit')
    
        df = pd.read_fwf(cp_vs_x_file,
                 header=0,
                 skiprows=0,
                 names=['#','x','Cp'],
                 )
        df = df.drop(labels=['#'],axis=1)
        clean_up(coordinates_file)
        clean_up(cp_vs_x_file)
        
        return df
    
    @staticmethod
    def interpolate(airfoil1, airfoil2, fraction_of_2nd_airfoil):
        """
        Return interpolated airfoil of two input airfoils and fraction. 
        This method uses XFOIL's INTE and GDES routines in the background.
        
        .. code-block:: python
            
            airfoil, profiltropfen, camberline = Airfoil.interpolate(airfoil1,
                                                                     airfoil2,
                                                                     fraction_of_2nd_airfoil)

        Parameters
        ----------
        airfoil1 : Instance of Airfoil class
        airfoil2 : Instance of Airfoil class
        fraction_of_2nd_airfoil : float 0..1
            Fraction of second airfoil to keep.

        Returns
        -------
        DataFrame
            The interpolated airfoil.
        DataFrame
            The symmetrical airfoil (Profiltropfen).
        DataFrame
            The camber line.

        """
        output_file = '_xfoil_output.txt'
        
        result = []
        options = [[1,1], [1, 0], [0, 1]]
        
        def read_coordinates(filename):
            df = pd.read_fwf(filename,
                             header = 0,
                             names=['X','Y'],
                             )
            df = df.dropna()
            return df
        
        for option in options:
            clean_up(output_file)
            with Xfoil() as x:
                x.run('inte')
                x.run('f')
                x.run('./util_loads/airfoil-database/' +
                          airfoil1.parameters['airfoil_filename'])
                x.run('f')
                x.run('./util_loads/airfoil-database/' +
                          airfoil2.parameters['airfoil_filename'])
                x.run(fraction_of_2nd_airfoil)
                x.run('')
                x.run('pcop')
                x.run('pane')
                x.run('gdes')
                x.run('tfac')
                x.run(option[0])
                x.run(option[1])
                x.run('')
                x.run('pcop')
                x.run('pane')                
                x.run('save')
                x.run(output_file)
                x.run('quit')
            
            result.append(read_coordinates(output_file))
        clean_up(output_file)    
        # thickness_line= df.loc[df['Y'] >= 0].drop_duplicates()
        # thickness_line['Y'] = thickness_line['Y']*2
        
        return result[0], result[1], result[2]
