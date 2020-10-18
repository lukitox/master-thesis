#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 18 15:42:30 2020

@author: Lukas Hilbers
"""
#%% Import Libraries and Data 

# Third-party imports
import time
import numpy as np

# Local imports
from util_mapdl import post_functions, prep_functions

#%%

class femodel:
    
    def __init__(self, mapdl):
        self.mapdl  = mapdl
        
        self.flaxpreg = prep_functions.material(self.mapdl,'FLAXPREG-T-UD',1)
        self.flaxpreg.load_from_db('FLAXPREG-T-UD')
        
    def evaluate(self, x):
        x = np.array(x)
        divisions = list(x[0:2]*5)
        if divisions[0] == divisions[1]:
            divisions[0] = divisions[0]-5
        topspar = list(x[2:5])
        bottomspar = list(x[5:8])
        web = list(x[8:11])
        
        mtot, I = self.calc(divisions, topspar, bottomspar, web)
        self.clear()
        
        return mtot, I

    def calc(self, divisions, topspar, bottomspar, web):
        self.mapdl.prep7()
        # Geometrieeinstellungen
        # Einheiten: tonne,mm,s,N
        
        # Abmaße des Balkens
        l = 1000 
        b = 10
        h = 30
        # Elementierung
        rho_elm = 0.2 # Elemente / mm Kantenlänge
        
        # Überprüfen und sortieren der Trennstellen
        divisions = set(divisions)
        divisions = list(np.sort(list(divisions)))
        divisions.insert(0, 0)
        divisions.append(l)
        intervals = []
        for x in range(len(divisions)-1):
            intervals.append([divisions[x], divisions[x+1]])
    
        with self.mapdl.chain_commands:
            self.mapdl.et('1','SHELL281')
            self.mapdl.keyopt(1,8,1)
            
            # Materialparameter
            self.flaxpreg.assign_mp()
            
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
            self.mapdl.lesize('all','','',rho_elm*b)
            
            self.mapdl.lsel('s','loc','y',l/2)
            self.mapdl.lesize('all','','',rho_elm*l)
            
            self.mapdl.lsel('s','loc','z',0)
            self.mapdl.lesize('all','','',rho_elm*h)
            
            # Vernetzung und Zuweisung Sections
            self.mapdl.mshkey(1)
            self.mapdl.mshape(0,'2d')
            self.mapdl.allsel('all')
            
            self.mapdl.sectype(100,'shell','','Dummy')
            self.mapdl.secdata(0.1,1,90.,3)
            self.mapdl.allsel('all')
            self.mapdl.amesh('all')
    
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
            
            # Lösung
            self.mapdl.run('/SOLU')
            self.mapdl.antype('static')
            self.mapdl.outres('all','all')
            self.mapdl.solve()
            self.mapdl.finish()
    
            # Auswertung
            self.mapdl.post1()
            
            # Versagenskriterium
            self.flaxpreg.assign_fc()
    
            self.mapdl.fctyp('dele','all')
            self.mapdl.fctyp('add','pfib')
            self.mapdl.fctyp('add','pmat')
        
            self.mapdl.allsel('all')
        
        I_f_t, I_m_t, I_f_b, I_m_b, I_f_w, I_m_w = ([] for i in range(6))
        for i in intervals:
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','z',h/2)
            F, M = post_functions.fc_puck(self.mapdl)
            I_f_t.append(F)
            I_m_t.append(M)
            
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','z',-h/2)
            F, M = post_functions.fc_puck(self.mapdl)
            I_f_b.append(F)
            I_m_b.append(M)
            
            self.mapdl.esel('s','cent','y',i[0],i[1])
            self.mapdl.esel('r','cent','x',b)
            F, M = post_functions.fc_puck(self.mapdl)
            I_f_w.append(F)
            I_m_w.append(M)
        I = list(np.round(I_f_t + I_f_b + I_f_w + I_m_t + I_m_b + I_m_w,3))
        
        self.mapdl.allsel('all')
        self.mapdl.get('M','elem','0','mtot','z')
        mtot = self.mapdl.parameters['M']
        return mtot, I
    
    def clear(self):
        self.mapdl.finish()
        self.mapdl.clear('NOSTART')