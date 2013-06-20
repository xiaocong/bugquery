import os, sys

os.chdir(os.path.dirname(__file__))
sys.path += [os.path.dirname(__file__)]

import brquery_api

application = brquery_api.app
