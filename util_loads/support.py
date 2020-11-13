#%% Import Libraries and Data 

# Third-party imports
import os

## Local imports

# %%

def cleanup(func):
    def wrapper(*args, **kwargs):
        
        list_of_files = lambda : [f for f in os.listdir() \
                                  if os.path.isfile(os.path.join(f))]
        
        start_files = list_of_files()
        
        return_value = func(*args, **kwargs)
        
        end_files = list_of_files()
        
        for filename in end_files:
            if filename not in start_files:
                os.remove(filename)
            
        return return_value
    return wrapper