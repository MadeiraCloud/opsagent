'''
@author: Thibault BRONCHAIN
'''

# internal import
import globals
from OpsAgent import OpsAgent

if __name__ == "__main__":
    globals.init()
    a = OpsAgent()
    a.run()
