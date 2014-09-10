'''
VisualOps agent AWS requests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


# System imports
import urllib2
import re
import time

# Internal imports
from opsagent.exception import AWSNotFoundException
from opsagent import utils

# Defines
WAIT_RETRY=5
TIMEOUT=30


# Get data
def get_aws_data(url):
    req = urllib2.Request(url)
    f = urllib2.urlopen(req, timeout=TIMEOUT)
    res = f.read()
    if re.search('404 - Not Found', res):
        raise AWSNotFoundException
    return res

# parse user data script
def parse_ud(ud, keys):
    v = {}
    for key in keys:
        m = re.search("%s=(.*)\n"%(key),ud)
        if m:
            v[key.lower()] = m.group(1)
    return v

# Get userdata
def userdata(config, manager):
    ud = None
    while not ud:
        if not manager.running():
            utils.log("WARNING", "Execution aborting, exiting ...",('userdata','aws'))
            return None
        utils.log("DEBUG", "Getting userdata ...",('userdata','aws'))
        try:
            ud = get_aws_data(config['network']['userdata'])
        except AWSNotFoundException:
            utils.log("WARNING", "Userdata not found. Retrying in %s seconds"%(WAIT_RETRY),('userdata','aws'))
            time.sleep(WAIT_RETRY)
        except Exception as e:
            utils.log("WARNING", "User data failure, error: '%s'. Retrying in %s seconds"%(e,WAIT_RETRY),('userdata','aws'))
            time.sleep(WAIT_RETRY)
    return parse_ud(ud, ["APP_ID","WS_URI","VERSION","BASE_REMOTE","GPG_KEY_URI"])

# Get instance ID from AWS
def instance_id(config, manager):
    iid = None
    while not iid:
        if not manager.running():
            utils.log("WARNING", "Execution aborting, exiting ...",('instance_id','aws'))
            return None
        utils.log("DEBUG", "Getting instance id ...",('instance_id','aws'))
        try:
            iid = get_aws_data(config['network']['instance_id'])
        except AWSNotFoundException:
            utils.log("ERROR", "Instance ID not found, retrying in '%s' seconds"%(WAIT_RETRY),('instance_id','aws'))
            time.sleep(WAIT_RETRY)
        except Exception as e:
            utils.log("ERROR", "Instance ID failure, unknown error: '%s', retrying in '%s' seconds"%(e,WAIT_RETRY),('instance_id','aws'))
            time.sleep(WAIT_RETRY)
    return iid

# Get token from disk
def token(config):
    f = config['global'].get('token')
    utils.log("DEBUG", "Getting token located in %s"%(f),('token','aws'))
    t = ''
    try:
        with open(f, 'r') as f:
            t = f.read()
    except Exception as e:
        utils.log("WARNING", "Can't get token file (%s): %s, updating token"%(f,e),('token','aws'))
        utils.reset_token(config)
        try:
            with open(f, 'r') as f:
                t = f.read()
        except Exception as e:
            utils.log("ERROR", "Can't get token file (%s): %s"%(f,e),('token','aws'))
    return t
