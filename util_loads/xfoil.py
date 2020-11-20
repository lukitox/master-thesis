# %% Import Libraries and Data

# Third-party imports
import os
from subprocess import DEVNULL, STDOUT, run
import pandas as pd
import numpy as np

# Local imports
from .xsoftware import Xsoftware


# %%


class Xfoil(Xsoftware):
    """
    The interface class to XFOIL.

    XFOIL access works with a context manager:

    .. code-block:: python

        from util_loads import Xfoil

        with Xfoil(mode='hide') as x:
            x.run('aero')
            #...
            x.run('quit')
            
    Parameters
    ----------
    mode : str, optional
        Mode to launch Xrotor.  Must be one of the following:
            
        - ``'hide'`` Hide popup windows and suppress output to console.
        - ``'show'`` Show popup windows and output to console.

    """

    def __init__(self, mode='hide'):
        super().__init__()
        self.input_file = '_xfoil_input.txt'
        self.__mode = mode

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super().__exit__(exc_type, exc_value, exc_traceback)

        if self.__mode == 'hide':
            run(['Xvfb :1 &'], shell=True, stdout=DEVNULL, stderr=STDOUT)
            run(['DISPLAY=:1 xfoil < ' + self.input_file], shell=True, stdout=DEVNULL, stderr=STDOUT)
            run(['kill -15 $!'], shell=True, stdout=DEVNULL, stderr=STDOUT)
        elif self.__mode == 'show':
            os.system('xfoil < ' + self.input_file)
        else:
            raise ValueError('Invalid mode %s' % self.__mode)
        
        os.remove(self.input_file)

    @staticmethod
    def read_coordinates(filename):
        """
        Reads an airfoil coordinates file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        coordinates : DataFrame

        """
        df = pd.read_fwf(filename,
                         header=0,
                         names=['X', 'Y'],
                         )

        return df.dropna()

    @staticmethod
    def read_cp_vs_x(filename, norm=False):
        """
        Reads a pressure distribution file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.
        norm : Bool
            - ``False`` Do not norm the output. X grid points are non-uniform
                and depend on the airfoils curvature.
            - ``True`` Norm X grid points are ``np.arange(0.01, 1.00, 0.01)``

        Returns
        -------
        cp_vs_x : DataFrame

        """
        df = pd.read_fwf(filename,
                         header=0,
                         skiprows=0,
                         names=['#', 'x', 'Cp'],
                         )
        df = df.drop(labels=['#'], axis=1)

        if norm is False:
            return df
        else:
            suction_side = df.iloc[:df['x'].idxmin() + 1, :]
            pressure_side = df.iloc[df['x'].idxmin() + 1:, :]

            def norm(dataframe):
                norm_list = list(np.arange(0.01, 1.00, 0.01))
                empty_frame = pd.DataFrame(norm_list, columns=['x'])
                empty_frame['Cp'] = np.nan
                dataframe = dataframe.append(empty_frame)
                dataframe = dataframe.sort_values('x')
                dataframe = dataframe.interpolate()
                dataframe = dataframe.dropna()
                dataframe = dataframe.drop_duplicates(keep='first')

                dataframe = dataframe[dataframe['x'].isin(norm_list)]
                return dataframe

            norm_suction_side = norm(suction_side)
            norm_pressure_side = norm(pressure_side)

            norm_suction_side.columns = ['x', 'Cp_suc']
            norm_pressure_side.columns = ['x', 'Cp_pres']

            norm_suction_side['Cp_pres'] = norm_pressure_side['Cp_pres']
            #norm_suction_side = norm_suction_side.fillna(0)

            return norm_suction_side[:99]

    @staticmethod
    def read_polar(filename):
        """
        Reads a polar output file and returns content as DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        polar : DataFrame
            Polar DataFrame.

        """
        colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46),
                    (49, 55), (58, 64), (66, 73), (74, 82)]
        tabular_data = pd.read_fwf(filename,
                                   colspecs=colspecs,
                                   header=[10],
                                   skiprows=[11])
        tabular_data.sort_values('alpha', inplace=True)
        tabular_data.drop_duplicates(keep='first', inplace=True)

        return tabular_data.reset_index()
