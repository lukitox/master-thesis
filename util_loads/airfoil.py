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
from .support import cleanup


# %%

class Airfoil:
    """
    The airfoil class.

    Parameters
    ----------
    airfoil_filename : string
        Name of airfoil. If coordinate file is stored in 'airfoil-database'
        folder, coordinates will be set.
    re : int or float
        Reynolds number
    ncrit : int or float, optional
        Ncrit value for XFOIL which affects Transition. The default is 9.
    iter_limit : int, optional
        Viscous-solution iteration limit. The default is 200.

    Returns
    -------
    None.

    """

    def __init__(self, airfoil_filename, re, ncrit=9, iter_limit=200):
        self.__parameters = {
            'airfoil_filename': airfoil_filename,
            'Re': re,
            'Ncrit': ncrit,
            'Iter': iter_limit,
        }
        self.__polar = None
        self.__xrotor_characteristics = None
        self.__database = './util_loads/airfoil-database/'

        airfoil_path = self.__database + self.__parameters['airfoil_filename']
        if os.path.exists(airfoil_path):
            self.coordinates = airfoil_path
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
            self.__coordinates = Xfoil.read_coordinates(coordinates)
        elif type(pd.DataFrame()) == type(coordinates):
            self.__coordinates = coordinates
        else:
            raise TypeError

    @property
    def xrotor_characteristics(self):
        """
        Returns airfoil characteristics dictionary for XROTOR.

            Zero-lift alpha (deg)
            d(Cl)/d(alpha)
            Maximum Cl
            Minimum Cl
            Minimum Cd
            Cl at minimum Cd
            d(Cd)/d(Cl**2)
            Cm

        Returns
        -------
        dict : int or float

        """
        return self.__xrotor_characteristics

    @xrotor_characteristics.setter
    def xrotor_characteristics(self, characteristics):
        self.__xrotor_characteristics = characteristics

    @property
    def parameters(self):
        """
        Return parameters dictionary.
            airfoil_filename : string
            Re : int or float
            Ncrit : int or float
            Iter : int

        Returns
        -------
        dict : string or int or float

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

    @cleanup
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
        np.savetxt(coordinates_file, self.coordinates, fmt='%9.8f')

        aseq = [[0, alpha_start, alpha_inc],
                [0, alpha_stop, alpha_inc]]

        for sequence in aseq:
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
                x.run('pacc')
                x.run(polar_file)
                x.run('')
                x.run('aseq ')
                x.run(sequence[0])
                x.run(sequence[1])
                x.run(sequence[2])
                x.run('')
                x.run('quit')

        self.__polar = Xfoil.read_polar(polar_file)

        # Set Xrotor_characteristics

        popt, pcov = curve_fit(self.__fit_cl_alpha__,
                               np.array(self.__polar['alpha']),
                               np.array(self.__polar['CL']))

        self.__polar['fitted CL'] = self.__fit_cl_alpha__(np.array(self.__polar['alpha']), *popt)
        self.__polar['d(Cl)/d(alpha)'] = np.gradient(self.__polar['fitted CL'], self.__polar['alpha']).round(5)
        self.__polar['filtered CD'] = savgol_filter(self.__polar['CD'], window_length=11, polyorder=2)
        self.__polar['d(Cd)/d(Cl**2)'] = np.gradient(np.gradient(self.__polar['filtered CD'], self.__polar['CL']),
                                                     self.__polar['CL'])

        self.__xrotor_characteristics = {
            'Zero-lift alpha (deg)': float(
                -self.__polar['fitted CL'][self.__polar[self.__polar['alpha'] == 0].index.values] / self.__polar[
                    'd(Cl)/d(alpha)'].max()),
            'd(Cl)/d(alpha)': self.__polar['d(Cl)/d(alpha)'].max() * 180 / 3.1416,
            'Maximum Cl': self.__polar['CL'].max(),
            'Minimum Cl': self.__polar[self.__polar['d(Cl)/d(alpha)'] == self.__polar['d(Cl)/d(alpha)'].max()][
                'fitted CL'].min(),
            'Minimum Cd': self.__polar['CD'].min(),
            'Cl at minimum Cd': self.__polar['CL'][self.__polar.idxmin()['CD']],
            'd(Cd)/d(Cl**2)': self.__polar['d(Cd)/d(Cl**2)'][self.__polar.idxmin()['CD']],
            'Cm': self.__polar['CM'].min(),
        }

    @staticmethod
    def __fit_cl_alpha__(x, x0, x1, a3, b1, b3, c2):
        b2 = 2 * a3 * x1 + b3
        c1 = b2 * x0 - b1 * x0 + c2
        c3 = b2 * x1 + c2 - a3 * x1 ** 2 - b3 * x1
        return np.piecewise(x, [x < x0, (x >= x0) & (x < x1), x > x1],
                            [lambda xx: b1 * xx + c1,
                             lambda xx: b2 * xx + c2,
                             lambda xx: a3 * xx ** 2 + b3 * xx + c3],
                            )

    @cleanup
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

        np.savetxt(coordinates_file, self.coordinates, fmt='%9.8f')

        cp_vs_x_file = '_xfoil_cpvsx.txt'

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

        return Xfoil.read_cp_vs_x(cp_vs_x_file, True)

    @staticmethod
    @cleanup
    def interpolate(airfoil1, airfoil2, fraction_of_2nd_airfoil):
        """
        Return interpolated airfoil of two input airfoils and fraction.
        This method uses XFOILs INTE and GDES routines in the background.

        .. code-block:: python

            airfoil, profiltropfen, camberline = Airfoil.interpolate(airfoil1,
                                                                     airfoil2,
                                                                     fraction_of_2nd_airfoil)

        Parameters
        ----------
        airfoil1 : Airfoil
        airfoil2 : Airfoil
        fraction_of_2nd_airfoil : Float 0..1
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
        options = [[1, 1], [1, 0], [0, 1]]

        for option in options:
            if os.path.exists(output_file):
                os.remove(output_file)
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

            result.append(Xfoil.read_coordinates(output_file))
        # thickness_line= df.loc[df['Y'] >= 0].drop_duplicates()
        # thickness_line['Y'] = thickness_line['Y']*2

        return result[0], result[1], result[2]
