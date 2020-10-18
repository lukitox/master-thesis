def fc_puck(mapdl):
    ###
    # This Function is supposed to return the maximum "Puck fiber failure" and "Puck inter-fiber (matrix) failure" values of the laminate.
    # It still does not work in a reliable manner.
    ###

    mapdl.run('*SET,I_f,0,$*SET,I_m,0,')    # Initialize the return values with 0, this will avoid "IndexError: ... not a valid parameter_name" so the function returns 0, 0 instead
    mapdl.run('*SET,maxelementnumber')
    mapdl.get('maxelementnumber','ELEM',0,'NUM','MAX')
    # Get the number of layers
    mapdl.run('*get,nlow,elem,0,num,min')
    mapdl.run('*get,secid,elem,nlow,attr,secn')
    mapdl.run('*get,nlay,shel,secid,prop,nlay')
    
    # Get number of active elements
    mapdl.run('*get,numberofactiveelements,elem,0,count')
    
    # Initialize arrays that will be filled with maximum FC values of all layers
    mapdl.run('*dim,I_maxf,array,nlay')
    mapdl.run('*dim,I_maxm,array,nlay')

    with mapdl.non_interactive:
        mapdl.run('*DO,lay,1,nlay')
        mapdl.run('*set,failarray,,$*set,ekeep,,')              # Delete Arrays if existing 
        mapdl.run('layer,lay')                                  # Specify the element layer for which data are to be processed
        
        mapdl.run('*dim,failarray,,maxelementnumber,4')         # Initialize Array for all elements
        mapdl.run('*dim,ekeep,,numberofactiveelements,3')       # Initialize Array for active elements
        
        mapdl.run('*vget,failarray(1,1),elem,1,esel')           # Column 1: Status of elements (1= selected, 0 = unselected), this is the masking vector for following *vmask commands
        mapdl.run('*vfill,failarray(1,2),ramp,1,1')             # Column 2: Element Numbers
        
        mapdl.run('etable,fibfail,fail,pfib')                   
        mapdl.run('*vget,failarray(1,3),elem,1,etab,fibfail')   # Column 3: Puck fiber failure
        mapdl.run('etable,matfail,fail,pmat')
        mapdl.run('*vget,failarray(1,4),elem,1,etab,matfail')   # Column 4: Puck inter-fiber (matrix) failure
        
        mapdl.run('*vmask,failarray(1,1)')                      # Specify failarray(1,1) as masking vector
        mapdl.run('*vfun, ekeep(1,1), comp, failarray(1,2)')    # Compress data set to selected elements only
        mapdl.run('*vmask,failarray(1,1)')
        mapdl.run('*vfun, ekeep(1,2), comp, failarray(1,3)')    # Do the same for column 3 
        mapdl.run('*vmask,failarray(1,1)')
        mapdl.run('*vfun, ekeep(1,3), comp, failarray(1,4)')    # ...and 4
        
        mapdl.run('*vscfun,I_fib,max,ekeep(1,2)')               # Get maximum fiber failure value of current layer
        mapdl.run('*vscfun,I_mat,max,ekeep(1,3)')               # Get maximum inter-fiber failure value of current layer
        mapdl.run('I_maxf(lay)=I_fib')                          # Store those values
        mapdl.run('I_maxm(lay)=I_mat')      
                
        mapdl.run('*ENDDO')        
            
    mapdl.run('*vscfun,I_f,max,I_maxf')     # Get maximum fiber failure value of the whole laminate
    mapdl.run('*vscfun,I_m,max,I_maxm')     # Get maximum inter-fiber failure value of the whole laminate
        
    I_f = mapdl.parameters['I_f']           # Retrieve those values
    I_m = mapdl.parameters['I_m']
    
    return I_f, I_m