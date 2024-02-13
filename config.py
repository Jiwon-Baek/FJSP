import os
from datetime import datetime

# Time Variables
# IAT = 'exponential(25)'
IAT = float("inf")
SIMUL_TIME = 1000

# Process Variables
DISPATCH_MODE = 'FIFO'  # FIFO, Manual

# Monitor Variables
OBJECT = 'Entire Process'
CONSOLE_MODE = True

# Visualization Variables
TITLE = "Quay Simulation"


current_working_directory = os.getcwd()
# Directory Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
folder_name = 'result'  # Define the folder name
save_path = os.path.join(script_dir, folder_name)  # Construct the full path to the folder
if not os.path.exists(save_path):
    os.makedirs(save_path)
now = datetime.now()
filename = now.strftime('%Y-%m-%d-%H-%M-%S')
filepath = os.path.join(save_path, filename+'.csv')

n_op = 100
n_show = n_op + 1
show_interval_time = 100
finished_pause_time = 1000