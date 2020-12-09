# %% Import Libraries and Data

# Third-party imports
import os


# Local imports

# %% Cleanup Decorator function: Deletes files written by the wrapped function.


def cleanup(func):
    def wrapper(*args, **kwargs):

        def list_of_files():
            return [f for f in os.listdir() if os.path.isfile(os.path.join(f))]

        start_files = list_of_files()

        return_value = func(*args, **kwargs)

        for filename in list_of_files():
            if filename not in start_files:
                os.remove(filename)

        return return_value

    return wrapper

# %% Decorator for printing function calls.

def print_call(func):
    def wrapper(*args, **kwargs):
        
        print('### Calling ' + func.__name__ + ' ###')
        print(f'- args: {args}')
        print(f'- kwargs: {kwargs}')
        
        return_value = func(*args, **kwargs)
        
        print(f'- return:\n {return_value}')
        print(f'### End of {func.__name__}  ###\n')
        
        return return_value
    
    return wrapper

# %% Timer

def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        
        return_value = func(*args, **kwargs)
        
        print('### Execution time: ' + str(time.time() - start))
        
        return return_value
    
    return wrapper