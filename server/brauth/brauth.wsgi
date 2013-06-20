import os, sys

os.chdir(os.path.dirname(__file__))
sys.path += [os.path.dirname(__file__)]

import brauth_api

application = brauth_api.app
