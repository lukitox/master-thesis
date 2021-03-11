# Third-party imports
import pyansys
import pandas as pd
import numpy as np
from pyOpt import Optimization
from pyOpt import ALPSO
import time
from mpi4py import MPI

# Local imports
from util_mapdl import Material
from util_mapdl.post_functions import fc_puck

class Femodel:
    
    def __init__(self, mapdl, mesh_factor=0.2):
        self.mapdl = mapdl
        self.__ansys_input_filename = '_ansys_input_file'
        self.mesh_density_factor = mesh_factor

    def cdread(self):
        """
        Read in the .cdb database file generated by the pre-processing 
        method.

        """
        
        self.mapdl.prep7()
        self.mapdl.cdread('all', self.__ansys_input_filename, 'cdb')        
        
    def clear(self):
        """Resets the MAPDL Session. """
        
        self.mapdl.finish()
        self.mapdl.clear('NOSTART')
        
    def pre_processing(self):

        self.mapdl.prep7() # Enter Preprocessing Routine
        
        # Space for basic parameters and settings
        self.mapdl.seltol(1e-4)
        self.mapdl.et('1','SHELL281')    
        self.mapdl.keyopt(1,8,1)

        # Material Parameters
        for key in self.materials:
            self.materials[key].assign_mp()

        # Abmaße des Balkens
        l = 1000 
        b = 10
        h = 30
    
        with self.mapdl.chain_commands:
            self.mapdl.et('1','SHELL281')
            self.mapdl.keyopt(1,8,1)
            
            # Modellgeometrie-Erstellung
            self.mapdl.k(1,0,0,h/2)
            self.mapdl.k(2,b,0,h/2)
            self.mapdl.k(3,b,l,h/2)
            self.mapdl.k(4,0,l,h/2)
            
            self.mapdl.k(5,0,0,-h/2)
            self.mapdl.k(6,b,0,-h/2)
            self.mapdl.k(7,b,l,-h/2)
            self.mapdl.k(8,0,l,-h/2)    
            
            self.mapdl.a(1,2,3,4)
            self.mapdl.a(5,6,7,8)    
            self.mapdl.a(6,7,3,2)
            
            # Mesh-Seeds
            self.mapdl.lsel('s','loc','x',b/2)
            self.mapdl.lesize('all','','',self.mesh_density_factor*b)
            
            self.mapdl.lsel('s','loc','y',l/2)
            self.mapdl.lesize('all','','',self.mesh_density_factor*l)
            
            self.mapdl.lsel('s','loc','z',0)
            self.mapdl.lesize('all','','',self.mesh_density_factor*h)
            
            # Vernetzung und Zuweisung Sections
            self.mapdl.mshkey(1)
            self.mapdl.mshape(0,'2d')
            self.mapdl.allsel('all')
            
            self.mapdl.sectype(100,'shell','','Dummy')
            self.mapdl.secdata(0.1,1,90.,3)
            self.mapdl.allsel('all')
            self.mapdl.amesh('all')
            
        self.mapdl.allsel('all')
        self.mapdl.cdwrite('all', self.__ansys_input_filename, 'cdb')
        self.mapdl.finish()
        self.mapdl.clear('nostart')
        
    def change_design_variables(self, divisions, topspar, bottomspar, web):

        # Abmaße des Balkens
        l = 1000 
        b = 10
        h = 30        
        
        # Überprüfen und sortieren der Trennstellen
        divisions = set(divisions)
        divisions = list(np.sort(list(divisions)))
        divisions.insert(0, 0)
        divisions.append(l)
        intervals = []
        for x in range(len(divisions)-1):
            intervals.append([divisions[x], divisions[x+1]])
    
            
        with self.mapdl.chain_commands:
            def secnum():
                secnum.counter+=1
                return secnum.counter
            secnum.counter = 0
    
            for i in intervals:       
                index = intervals.index(i)
                
                self.mapdl.sectype(secnum(),'shell','','Top_spar')
                self.mapdl.secdata(topspar[index],1,90.,3)
                self.mapdl.esel('s','cent','z',h/2)
                self.mapdl.esel('r','cent','y',i[0],i[1])
                self.mapdl.emodif('all','secnum',secnum.counter)
                
                self.mapdl.sectype(secnum(),'shell','','Bottom_spar')
                self.mapdl.secdata(bottomspar[index],1,90.,3)
                self.mapdl.esel('s','cent','z',-h/2)
                self.mapdl.esel('r','cent','y',i[0],i[1])
                self.mapdl.emodif('all','secnum',secnum.counter)
                
                self.mapdl.sectype(secnum(),'shell','','Shearweb')
                self.mapdl.secdata(web[index]/2,1,45.,3)                     #### achtung /2
                self.mapdl.secdata(web[index]/2,1,-45.,3)
                self.mapdl.esel('s','cent','x',b)
                self.mapdl.esel('r','cent','y',i[0],i[1])
                self.mapdl.emodif('all','secnum',secnum.counter)
                
            # Lastdefinition und Lösung
            # RBD
            self.mapdl.nsel('s','loc','x',0)
            self.mapdl.d('all','ux',0)
            self.mapdl.nsel('s','loc','y',0)
            self.mapdl.d('all','all',0)
            # Last
            self.mapdl.esel('s','cent','z',h/2)
            self.mapdl.sfe('all','','pres','0',-0.05/20)
            self.mapdl.esel('s','cent','z',-h/2)
            self.mapdl.sfe('all','','pres','0',-0.05/20)
            self.mapdl.allsel('all')
        
    def solve(self):
        """Solve the FE-Model. """
        
        self.mapdl.run('/SOLU')
        self.mapdl.antype('static')
        self.mapdl.outres('all','all')
        self.mapdl.solve()
        self.mapdl.finish()
        
    def post_processing(self, divisions):
        
        self.mapdl.post1() # Enter Post-processing Routine
        
        # Assign Failure Criteria Values
        for key in self.materials:
            self.materials[key].assign_fc()
        
        self.mapdl.fctyp('dele','all')
        self.mapdl.fctyp('add','pfib')
        self.mapdl.fctyp('add','pmat')        
        
        self.mapdl.allsel('all')
        
        # Abmaße des Balkens
        l = 1000 
        b = 10
        h = 30          
        
        # Überprüfen und sortieren der Trennstellen
        divisions = set(divisions)
        divisions = list(np.sort(list(divisions)))
        divisions.insert(0, 0)
        divisions.append(l)
        intervals = []
        for x in range(len(divisions)-1):
            intervals.append([divisions[x], divisions[x+1]])
        
        I_f_t, I_m_t, I_f_b, I_m_b, I_f_w, I_m_w = ([] for i in range(6))
        for i in intervals:
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','z',h/2)
            F, M = fc_puck(self.mapdl)
            I_f_t.append(F)
            I_m_t.append(M)
            
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','z',-h/2)
            F, M = fc_puck(self.mapdl)
            I_f_b.append(F)
            I_m_b.append(M)
            
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','x',b)
            F, M = fc_puck(self.mapdl)
            I_f_w.append(F)
            I_m_w.append(M)
        I = list(I_f_t + I_f_b + I_f_w + I_m_t + I_m_b + I_m_w)
        
        self.mapdl.allsel('all')
        self.mapdl.get('M','elem','0','mtot','z')
        mtot = self.mapdl.parameters['M']
        
        return mtot, I
    
    def evaluate(self, x):
    
        x = np.array(x)
        x[0] = int(x[0])
        x[1] = int(x[1])

        divisions = list(x[0:2]*5)
        if divisions[0] == divisions[1]:
            divisions[0] = divisions[0]-5
        topspar = list(x[2:5])
        bottomspar = list(x[5:8])
        web = list(x[8:11])
        
        self.cdread()
        self.change_design_variables(divisions, topspar, bottomspar, web)
        self.solve()
        mtot, I = self.post_processing(divisions)
        self.clear()
        
        return mtot, I
        
    @property
    def materials(self):
        """
        The Materials assigned to the Model.

        Returns
        -------
        materials : Dict

        """
        return self.__materials
    
    @materials.setter
    def materials(self, materials):
        self.__materials = materials
        
        for key in materials:
            self.__materials[key].load_from_db()
            
    @property
    def mesh_density_factor(self):
        """
        Integer factor to control the mesh density.

        Returns
        -------
        mesh_density_factor : int

        """
        return self.__mesh_density_factor
            
    @mesh_density_factor.setter
    def mesh_density_factor(self, mesh_density_factor):
        self.__mesh_density_factor = mesh_density_factor
        
# %% Run ANSYS and instantiate FE-Model

rank = MPI.COMM_WORLD.Get_rank()
size = MPI.COMM_WORLD.Get_size()

ansys_path = ['/home/y0065120/Dokumente/Leichtwerk/Projects/ansys-'
              + str(i) for i in range(size)]

jobname = ['job-' + str(i) for i in range(size)]

mapdl = [[] for i in range(size)]

mapdl[rank] = pyansys.launch_mapdl(run_location=ansys_path[rank],
                                   nproc=1,
                                   override=True,
                                   loglevel='error',
                                   additional_switches='-smp -d X11C',
                                   jobname=jobname[rank],
                                   allow_ignore=True,
                                   mode='console',
                                   )

femodel = [[] for i in range(size)]

femodel[rank] = Femodel(mapdl[rank])

femodel[rank].materials = {'flaxpreg': Material(mapdl[rank], 'FLAXPREG-T-UD', 1)}
femodel[rank].pre_processing()

def objfunc(x):
    comm = MPI.COMM_WORLD
    
    size = comm.Get_size()
    rank = comm.Get_rank()       
    
    mtot, I = femodel[rank].evaluate(x)
    
    # Get objective and constraint vector
    f = np.round(mtot*10**6,3)
    g = list(np.round(np.array(I)-1,3))
    
    # Print current Function Evaluation for monitoring purpuses
    objfunc.counter+= 1
    print(objfunc.counter,str(np.round(f,2)).zfill(5),str(int(x[0])).zfill(3),str(int(x[1])).zfill(3),list(np.round(x[2:],3)))
    
    time.sleep(0.01)
    fail = 0
    return f, g, fail
objfunc.counter = 0

opt_prob = Optimization('Faserverbundbalken',objfunc)

# Add variables
t_layer = 0.185
opt_prob.addVar('y1', 'c', lower=4, upper=149, value=30)
opt_prob.addVar('y2', 'c', lower=4, upper=150, value=90)
opt_prob.addVar('n_top1' ,'c', lower=1*0.1, upper=1.5, value=3*t_layer)
opt_prob.addVar('n_top2' ,'c', lower=1*0.1, upper=1.5, value=3*t_layer)
opt_prob.addVar('n_top3' ,'c', lower=1*t_layer, upper=0.75, value=2*t_layer)
opt_prob.addVar('n_bot1' ,'c', lower=1*0.1, upper=1.5, value=5*t_layer)
opt_prob.addVar('n_bot2' ,'c', lower=1*0.1, upper=1.5, value=4*t_layer)
opt_prob.addVar('n_bot3' ,'c', lower=1*t_layer, upper=0.75, value=2*t_layer)
opt_prob.addVar('n_web1' ,'c', lower=1*t_layer, upper=1.5, value=2*t_layer)
opt_prob.addVar('n_web2' ,'c', lower=1*t_layer, upper=1.5, value=1*t_layer)
opt_prob.addVar('n_web3' ,'c', lower=1*t_layer, upper=0.75, value=1*t_layer)

# Add objective
opt_prob.addObj('f')

# Add constraints
opt_prob.addConGroup('g_fib_top', 3, 'i')
opt_prob.addConGroup('g_fib_bot', 3, 'i')
opt_prob.addConGroup('g_fib_web', 3, 'i')
opt_prob.addConGroup('g_mat_top', 3, 'i')
opt_prob.addConGroup('g_mat_bot', 3, 'i')
opt_prob.addConGroup('g_mat_web', 3, 'i')

# Instantiate Optimizer
alpso = ALPSO(pll_type='SPM')
alpso.setOption('fileout',1)

alpso_path = "/home/y0065120/Dokumente/Leichtwerk/Projects/ALPSO/"
filename = 'Balken_Output_ALPSO'

alpso.setOption('filename', alpso_path+filename)
alpso.setOption('SwarmSize', 40)
alpso.setOption('stopIters', 2)      
alpso.setOption('rinit', 1.)
alpso.setOption('itol', 0.01)
alpso.setOption('c1',3.5)
alpso.setOption('c2',0.3)
alpso.setOption('w2',0.7)

def coldstart():    
    alpso(opt_prob, store_hst=True)
    print(opt_prob.solution(0))
    
for i in range(10):
    alpso.setOption('filename', alpso_path+filename+str(i))
    alpso(opt_prob, store_hst=True)
    print(opt_prob.solution(i))
    with open('solution'+str(i)+'.txt', "w") as f:
        f.write(str(opt_prob.solution(i)))