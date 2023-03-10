# %% Import Libraries and Data

# Third-party imports
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
        self.name = 'xfoil'
        self.input_file = '_xfoil_input.txt'
        self.mode = mode        

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

            def norm(dataframe): # Todo: isolieren
                norm_list = list(np.arange(0.01, 1.00, 0.01))
                empty_frame = pd.DataFrame(norm_list, columns=['x'])
                empty_frame['y'] = np.nan
                dataframe.columns = ['x', 'y']
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
    def read_cf_vs_x(filename):
        colspecs = [(12, 19), (59, 67)]
        
        df = pd.read_fwf(filename,
                         colspecs=colspecs)
        
        df = df[(df != 0).all(1)]
        
        suction_side = df.iloc[:df['x'].idxmin() + 1, :]
        pressure_side = df.iloc[df['x'].idxmin() + 1:, :]
        
        def norm(dataframe):
            norm_list = list(np.arange(0.01, 1.00, 0.01))
            empty_frame = pd.DataFrame(norm_list, columns=['x'])
            empty_frame['y'] = np.nan
            dataframe.columns = ['x', 'y']
            dataframe = dataframe.append(empty_frame)
            dataframe = dataframe.sort_values('x')
            dataframe = dataframe.interpolate()
            dataframe = dataframe.dropna()
            dataframe = dataframe.drop_duplicates(keep='first')
        
            dataframe = dataframe[dataframe['x'].isin(norm_list)]
            return dataframe

        norm_suction_side = norm(suction_side)
        norm_pressure_side = norm(pressure_side)
        
        norm_suction_side.columns = ['x', 'Cf']
        norm_pressure_side.columns = ['x', 'Cf']
        
        norm_suction_side['Cf'] = norm_suction_side['Cf'] + norm_pressure_side['Cf']
        
        return norm_suction_side
        
    @staticmethod
    def read_dump(filename):
        """
        Reads a DUMP file (that includes e.g. the skin friction coefficient
        'cf') and returns the content as a DataFrame.

        Parameters
        ----------
        filename : Str
            Filename/ Path.

        Returns
        -------
        tabular_data : DataFrame
            DESCRIPTION.

        """
        colspecs = [(3, 10), (12, 19), (20, 28), (29, 37), (39, 47),
                    (49, 57), (59, 67), (70, 77), (78, 87), (88, 96),
                    (97, 105), (106, 114)]
        
        tabular_data = pd.read_fwf(filename,
                                   colspecs=colspecs)
        
        return tabular_data
        
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
