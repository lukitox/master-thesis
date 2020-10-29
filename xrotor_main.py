#%% Import Libraries and Data 

# Third-party imports
import numpy as np

# Local imports
from util_xrotor import util_xrotor as ux

#%% Instantiate Propeller

Prop_MF3218 = ux.propeller(number_of_blades= 2, tip_radius= 0.412, hub_radius= 0.04)

#                                r/R   c/R  beta
Prop_MF3218.geometry = np.array([[0.17, 0.10, 17],
                                 [0.22, 0.14, 20],
                                 [0.27, 0.16, 18],
                                 [0.32, 0.15, 16],
                                 [0.37, 0.15, 15],
                                 [0.42, 0.14, 14],
                                 [0.47, 0.14, 13],
                                 [0.52, 0.13, 13],
                                 [0.57, 0.13, 12],
                                 [0.62, 0.12, 12],
                                 [0.67, 0.12, 11],
                                 [0.72, 0.11, 11],
                                 [0.77, 0.11, 11],
                                 [0.82, 0.10, 11],
                                 [0.87, 0.10, 10],
                                 [0.92, 0.09, 10],
                                 [0.97, 0.08,  7],
                                 [1.00, 0.01,  7],])

MH113 = ux.airfoil('mh113.txt', 250000)
MH113.calculate_polar()

MH121 = ux.airfoil('mh121.txt', 500000)
MH121.calculate_polar()

Prop_MF3218.add_section(0.5, MH113)
Prop_MF3218.add_section(1.0, MH121)

#%% Instantiate Loadcase

Prop_MF3218.add_loadcase(name= 'Max. RPM', loadcase= ux.loadcase(flight_speed= 0.01, rpm= 4000))

#%% Run Xrotor

with ux.xrotor(propeller= Prop_MF3218, loadcase= 'Max. RPM') as x:
    x.run('atmo 0')             # Set fluid properties from ISA 0km
    x.arbi()                    # Input arbitrary rotor geometry
    x.parse_airfoils()
    x.run('oper')               # Calculate off-design operating points
    x.run('rpm 4000')           # Prescribe rpm                                     ### automatisieren
    x.write_oper()              # Write current operating point to disk file
    x.run('')                   # return
    x.run('bend')               # Write current operating point to disk file
    x.run('eval')               # Evaluate structural loads and deflections
    x.write_bend()              # Write structural solution to disk file
    x.run('')                   # return
    x.run('quit')               # Exit program
    
#%% Play around
    
oper_single_values = Prop_MF3218.loadcases['Max. RPM'].results['oper'][0]
oper_tabular_data  = Prop_MF3218.loadcases['Max. RPM'].results['oper'][1]
bend_tabular_data  = Prop_MF3218.loadcases['Max. RPM'].results['bend']

#print(Prop_MF3218.loadcases)
#print(Prop_MF3218)

bend_tabular_data.plot(x='r/R',y=['Mz','Mx'])
oper_tabular_data.plot(x='r/R',y=['CL','Cd'])

#%%

with ux.xrotor(propeller= Prop_MF3218, loadcase= 'Max. RPM') as x:
    x.run('atmo 0')             # Set fluid properties from ISA 0km
    x.arbi()                    # Input arbitrary rotor geometry
    for i in range(10):
        x.run('aero')
        x.run('')
    x.run('quit')
