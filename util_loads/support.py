#%% Import Libraries and Data 

# Third-party imports
import os

## Local imports

# %% Cleanup Decorator function: Deletes files written by the wrapped function.

def cleanup(func):
    def wrapper(*args, **kwargs):
        
        list_of_files = lambda : [f for f in os.listdir() \
                                  if os.path.isfile(os.path.join(f))]
        
        start_files = list_of_files()
        
        return_value = func(*args, **kwargs)
        
        for filename in list_of_files():
            if filename not in start_files:
                os.remove(filename)
            
        return return_value
    
    return wrapper