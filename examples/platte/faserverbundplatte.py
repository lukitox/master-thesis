import pyansys
import numpy as np

path = 'C:/Users/y0065120/Documents/Leichtwerk/1_Masterarbeit/ValidierungSoftware/Faserverbundplatte'
mapdl = pyansys.launch_mapdl(run_location=path,override=True,additional_switches='-smp')

#
# Einstellbare Parameter
#
mapdl.output('output','out')
#mapdl.run('/FILENAME,Balken')
mapdl.eshape('1')
mapdl.plopts('title','off')
mapdl.number('1')
mapdl.pnum('kp','0')
mapdl.pnum('sec','1')
mapdl.psymb('esys','0')
mapdl.pbc('all','','0')
mapdl.vscale('1','6','0')
mapdl.shade()
mapdl.facet('fine')
mapdl.nerr('','100000')

def fe_calc(alpha,beta):
    mapdl.prep7()
    # 
    # Geometrieeinstellungen
    #
    # Einheiten: tonne,mm,s,N
    #
    b = 1     # Breite 
    h = 1     # Länge
    F = 30     # Kraft
    n_elm = 10  # Anzahl Elemente pro Kante
    
    mapdl.et('1','SHELL281')
    
    # 
    # Materialparameter
    #
    mapdl.mp('EX',1,28200)
    mapdl.mp('EY',1,3310)
    mapdl.mp('EZ',1,3310)
    mapdl.mp('PRXY','1',0.34)
    mapdl.mp('PRXZ','1',0.34)
    mapdl.mp('PRYZ','1',0.34)
    mapdl.mp('GXY','1',5200)
    mapdl.mp('GXZ','1',5200)
    mapdl.mp('GYZ','1',3615)
    mapdl.mp('DENS','1','1.33E-9')
    d_flaxpreg = 0.185
    
    #
    # Modellgeometrie-Erstellung
    #
    mapdl.k(1,0,0,0)
    mapdl.k(2,b,0,0)
    mapdl.k(3,b,h,0)
    mapdl.k(4,0,h,0)
    
    mapdl.a(1,2,3,4)    
    
    # 
    # Mesh-Seeds
    #
    mapdl.lsel('all')
    mapdl.lesize('all','','',n_elm)
    
    #
    # Vernetzung und Zuweisung Sections
    #
    mapdl.mshkey(1)
    mapdl.mshape(0,'2d')
    mapdl.allsel('all')
    mapdl.nummrg('kp')
    mapdl.allsel('all')
    mapdl.type(1)
    
    mapdl.sectype(1,'shell','','Secname')
    mapdl.secdata(d_flaxpreg,1,alpha,3)
    mapdl.secdata(d_flaxpreg,1,beta,3)
    mapdl.secdata(d_flaxpreg,1,beta,3)
    mapdl.secdata(d_flaxpreg,1,alpha,3)

    mapdl.allsel('all')
    mapdl.amesh('all')
    
    # 
    # Lastdefinition und Lösung
    #
    # RBD
    mapdl.nsel('s','loc','x',0)
    mapdl.nsel('r','loc','y',0)
    mapdl.d('all','all',0)
    
    mapdl.nsel('all')
    mapdl.d('all','uz',0)
    
    # Last
    mapdl.nsel('s','loc','x',b)
    mapdl.f('all','fy',F/mapdl.n_node)
    
    mapdl.nsel('s','loc','x',0)
    mapdl.f('all','fy',-F/mapdl.n_node)    
    
    mapdl.nsel('s','loc','y',h)
    mapdl.f('all','fx',F/mapdl.n_node)
    
    mapdl.nsel('s','loc','y',0)
    mapdl.f('all','fx',-F/mapdl.n_node)    
    
    mapdl.allsel('all')
    #mapdl.save()
    
    # Lösung
    mapdl.run('/SOLU')
    mapdl.antype('static')
    mapdl.outres('all','all')
    mapdl.solve()
    mapdl.finish()
    #mapdl.save()
    
    #
    # Auswertung
    #
   
    mapdl.post1()
    mapdl.seltol(0.05) 
    
    mapdl.nsle('s','corner')
    mapdl.nsel('r','loc','x',b/2)
    mapdl.nsel('r','loc','y',h/2)
    mapdl.get('E_xy','node',np.int(mapdl.nnum[0]),'epto','xy')
    E_xy = mapdl.read_float_parameter('E_xy')
    
    mapdl.finish()
    mapdl.clear('NOSTART')
    
    return np.array([E_xy,0])

#
# Optimierung mit PSO und PyOpt
#

from pyOpt import Optimization
from pyOpt import ALPSO
import time

def objfunc(x):
    a = fe_calc(x[0],x[1])
    
    f = a[0]
    
    g = [0.0]*1
    g[0] = -1
    
    time.sleep(0.01)
    
    fail = 0
    return f, g, fail

# Instantiate Optimization Problem 
opt_prob = Optimization('Test',objfunc)
opt_prob.addVar('alpha','i',lower=-90,upper=90,value=0)
#opt_prob.addVar('alpha','i',lower=38,upper=48,value=43)

opt_prob.addVar('beta','i',lower=-90,upper=90,value=0)
#opt_prob.addVar('beta','i',lower=-48,upper=-38,value=-43)

opt_prob.addObj('f')
#opt_prob.addCon('g','i')

# Solve Problem (No-Parallelization)
alpso_none = ALPSO()
alpso_none.setOption('fileout',1)
alpso_none.setOption('filename','Out-ALPSO')

alpso_none.setOption('SwarmSize',25)
alpso_none.setOption('stopIters',3)

alpso_none(opt_prob, store_hst=True)
print(opt_prob.solution(0))


#0.02682103

#alpso_none(opt_prob._solutions[0])
#print(opt_prob._solutions[0]._solutions[0])
#opt_prob.write2file(outfile='', disp_sols=True, solutions=[])





    #mapdl.nsel('s','loc','x',b)
    #mapdl.nsel('r','loc','y',h)
    
    #mapdl.get('U_sum','node',np.int(mapdl.nnum),'u','sum')
    #    U_sum = mapdl.read_float_parameter('U_sum')   
    
    #mapdl.allsel('all')
    #mapdl.run('/POST1')
    #mapdl.run('PLNSOL,U,SUM')#  plnsol('u','sum')
    #mapdl.open_gui()
    #mapdl.get('U_sum','PLNSOL',0,'max')
    #U_sum = mapdl.read_float_parameter('U_sum')
    
# =============================================================================
#     mapdl.allsel('all')
#     mapdl.run('/POST1')
#     mapdl.etable('uxetab','U','X')
#     mapdl.run('*vget,uxvget,elem,1,etab,uxetab')
#     mapdl.vscfun('uxmax','max','uxvget')
#     UX_max = mapdl.read_float_parameter('uxmax')  
#     
#     mapdl.etable('uyetab','U','Y')
#     mapdl.run('*vget,uyvget,elem,1,etab,uyetab')
#     mapdl.vscfun('uymax','max','uyvget')
#     UY_max = mapdl.read_float_parameter('uymax')  
#     
#     U_sum = np.sqrt(UX_max**2 + UY_max**2)
# =============================================================================