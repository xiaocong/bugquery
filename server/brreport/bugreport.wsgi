import os, sys

os.chdir(os.path.dirname(__file__))
sys.path += [os.path.dirname(__file__)]

import bugreport

application = bugreport.app
