"""
Load calculation and FE-preprocessing script of HeLics propeller structural 
analysis Template.

Created on Jan 12 2021

Author: Lukas Hilbers
"""

# %% Import Libraries and Data

# Third-party imports
import numpy as np
import pyansys

# Local imports
from util_loads import Propeller, Airfoil, Loadcase
from util_mapdl import Material
from propellermodel import PropellerModel

# %% Instantiate Airfoils and assign radial sections

airfoil = Airfoil('mf3218.xfo', 500000, iter_limit=600)
airfoildick = Airfoil('mf3218-dick.xfo', 500000, iter_limit=600)
rectangle = Airfoil('rectangle2.txt',500000)

# %% Instantiate Propeller and assign geometry and airfoils

propeller = Propeller(number_of_blades=2,
                      tip_radius=0.412,
                      hub_radius=0.04,
                      )

propeller.geometry = np.array([[0.10,0.078,0],
                               [0.121, 0.078, 0.],
                               [0.155, 0.100, 5.99],
                               [0.223, 0.160, 17.97],
                               [0.345, 0.149, 14.44],
                               [0.417, 0.142, 12.68],
                               [0.490, 0.135, 11.18],
                               [0.563, 0.128, 9.94],
                               [0.636, 0.121, 8.97],
                               [0.709, 0.114, 8.26],
                               [0.782, 0.107, 7.81],
                               [0.854, 0.100, 7.63],
                               [0.947, 0.091, 7.5],
                               [1., 0.066, 7.5],                               
                               ])

propeller.sections = [[0.121, airfoil],
                      [0.223, airfoil],
                      [1., airfoil]]

propeller.geometric_sections = [[0.121, rectangle],
                                [0.223, airfoildick],
                                [1., airfoildick]]

for x in propeller.sections:
    x[1].set_polar(alpha_start=-7, alpha_stop=20, alpha_inc=0.25) 
    
airfoil.xrotor_characteristics['Cm'] = -0.14
airfoil.xrotor_characteristics['d(Cl)/d(alpha)'] = 6.28
airfoil.xrotor_characteristics['Minimum Cl'] = 0.

# %% Instantiate Loadcases

propeller.add_loadcase(loadcase=Loadcase(name='Max RPM', flight_speed=0.01))

propeller.loadcases[0][0].set_data('rpm',4000)

# %% Calculate loads

propeller.calc_loads()
propeller.set_load_envelope()

# %% Run ANSYS and instantiate FE-Model

ansys_path = '/home/y0065120/Dokumente/Leichtwerk/Projects/ANSYS'
mapdl = pyansys.launch_mapdl(run_location=ansys_path,
                             nproc=4,
                             override=True,
                             loglevel='error',
                             additional_switches='-smp -d X11C',
                             allow_ignore=True,
                             mode='console',
                             )

femodel = PropellerModel(mapdl,
                         mesh_density_factor=1,
                         propeller = propeller,
                         n_sec= 20,
                         )

femodel.materials = {'flaxpreg': Material(mapdl,
                                          'FLAXPREG-T-UD',
                                          1),
                     'balsa': Material(mapdl,
                                       'balsaholz',
                                       2),
                     }

femodel.pre_processing()

femodel.element_data.to_csv('element_data.csv')