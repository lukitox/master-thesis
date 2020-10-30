#%% Import Libraries and Data 

# Third-party imports
import os
import numpy as np
import pandas as pd

# Local imports
from .xfoil import xfoil

#%%

class airfoil:
    '''
    The airfoil class.

    Parameters
    ----------
    airfoil_filename : string
        Name of airfoil coordinate file stored in 'airfoil-database' folder.
    Re : int or float
        Reynolds number
    Ncrit : int or float, optional
        Ncrit value for XFOIL which affects Transition. The default is 9.
    Iter : int, optional
        Viscous-solution iteration limit. The default is 200.

    Returns
    -------
    None.

    '''    
    def __init__(self, airfoil_filename, Re, Ncrit = 9, Iter = 200):
        self.parameters = {
            'airfoil_filename': airfoil_filename,
            'Re': Re,
            'Ncrit': Ncrit,
            'Iter': Iter,
            }
        ''' 
        Returns parameters dictionary
        
        Returns
        -------
        dict : string or int or float
        
        Parameters
        ----------
        airfoil_filename : string,\n
        Re : int or float,\n
        Ncrit : int or float,\n
        Iter : int
    
            
        '''
        
        self.polar = {}
        ''' 
        Returns Polar Dataframe.
        
        Returns
        -------
        DataFrame
        '''
        
        self.xrotor_characteristics = {}
        
        '''
        Returns airfoil characteristics dictionary for XROTOR
        
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
        
        '''
        
    def calculate_polar(self, alpha_start = -20, alpha_stop = 20, alpha_inc = 0.25):
        '''
        Calculate airfoil polar and store as pandas dataframe.

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

        '''
        polar_file = '_xfoil_polar.txt'
        
        def clean_up():
            if os.path.exists(polar_file):
                os.remove(polar_file)
                
            if os.path.exists(':00.bl'):
                os.remove(':00.bl')
                
        clean_up()
        
        aseq = [[0, alpha_start, alpha_inc],
                [0, alpha_stop , alpha_inc]]
        
        for sequence in aseq:        
            with xfoil() as x:
                x.run('load ./util_loads/airfoil-database/' + self.parameters['airfoil_filename'])      ##### Todo: Relativer Pfad 
                x.run('pane')
                x.run('oper')
                x.run('vpar')
                x.run('n ' + str(self.parameters['Ncrit']))
                x.run('')
                x.run('visc ' + str(self.parameters['Re']))
                x.run('iter')
                x.run(str(self.parameters['Iter']))
                x.run('pacc')
                x.run(polar_file)
                x.run('')
                x.run('aseq ')
                x.run(sequence[0])
                x.run(sequence[1])
                x.run(sequence[2])
                x.run('')
                x.run('quit')
                
        colspecs = [(1, 8), (10, 17), (20, 27), (30, 37), (39, 46), (49, 55), (58, 64), (66, 73), (74, 82)]
        tabular_data = pd.read_fwf(polar_file, colspecs=colspecs, header= [10], skiprows=[11])
        tabular_data.sort_values('alpha', inplace=True)
        tabular_data.drop_duplicates(keep='first',inplace=True)
        tabular_data = tabular_data.reset_index()
        
        clean_up()
        
        self.polar = tabular_data        
        self.__calculate_xrotor_parameters__()
        
    def __calculate_xrotor_parameters__(self):
        from scipy.optimize import curve_fit
        from scipy.signal import savgol_filter
                
        popt, pcov = curve_fit(self.__fit_cl_alpha__, np.array(self.polar['alpha']), np.array(self.polar['CL']))
        
        self.polar['fitted CL']         = self.__fit_cl_alpha__(np.array(self.polar['alpha']), *popt)
        self.polar['d(Cl)/d(alpha)']    = np.gradient(self.polar['fitted CL'], self.polar['alpha']).round(5)
        self.polar['filtered CD']       = savgol_filter(self.polar['CD'],  window_length=11, polyorder=2)
        self.polar['d(Cd)/d(Cl**2)']    = np.gradient(np.gradient(self.polar['filtered CD'], self.polar['CL']), self.polar['CL'])
        
        self.xrotor_characteristics = {
            'Zero-lift alpha (deg)' : float(-self.polar['fitted CL'][self.polar[self.polar['alpha'] == 0].index.values] / self.polar['d(Cl)/d(alpha)'].max()),
            'd(Cl)/d(alpha)'        : self.polar['d(Cl)/d(alpha)'].max() * 180/3.1416,           
            'Maximum Cl'            : self.polar['CL'].max(),
            'Minimum Cl'            : self.polar[self.polar['d(Cl)/d(alpha)'] == self.polar['d(Cl)/d(alpha)'].max()]['fitted CL'].min(), 
            'Minimum Cd'            : self.polar['CD'].min(),
            'Cl at minimum Cd'      : self.polar['CL'][self.polar.idxmin()['CD']],
            'd(Cd)/d(Cl**2)'        : self.polar['d(Cd)/d(Cl**2)'][self.polar.idxmin()['CD']],
            'Cm'                    : self.polar['CM'].min(),
            }                     
                             
    def __fit_cl_alpha__(self, x, x0, x1, a3, b1, b3, c2):
        b2 = 2*a3*x1 + b3
        c1 = b2*x0 - b1*x0 + c2
        c3 = b2*x1 + c2 - a3*x1**2 - b3*x1
        return np.piecewise(x, [x < x0, (x >= x0) & (x < x1), x > x1], [lambda x: b1*x + c1,
                                                                        lambda x: b2*x + c2,
                                                                        lambda x: a3*x**2 + b3*x + c3])