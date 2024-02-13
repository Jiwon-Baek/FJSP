

# from Source import Source
# from Sink import Sink
# from Part import Job, Operation
# from Process import Process
# from Resource import Machine
# from Monitor import *

"""
Note: when you make use of 'from-import' statement, its context is distinguished by 
whether it is absolute-import or relative-import.

1. from .Monitor 
-> This is relative import. This assumes that the module (Monitor) is in the same package (directory) 
as the module where this import statement is written.

2. from Monitor 
-> This is absolute import. This assumes that there is a top-level module or package named Monitor
in your Python path. It's not relative to the current package. The 'config.py' file and the 'quay.py' file is
at the outer scope of this 'environment' directory, so the absolute import method was used. 

Note 2: You need to add import statement repeatedly inside the each python file respectively.
The import statements in the __init__.py file are primarily for making the contents 
of the environment package available when someone imports the package itself.
"""

