'''
VisualOps agent CLOUD requests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


# System imports
import urllib2
import re
import json
import time

# Internal imports
from opsagent.exception import CLOUDNotFoundException
from opsagent import utils

# Defines
WAIT_RETRY=5
TIMEOUT=30

# Temporary openstack IP define
OPENSTACK_UID_URI="http://169.254.169.254/openstack/latest/meta_data.json"

# Get data
def get_cloud_data(url):
    req = urllib2.Request(url)
    f = urllib2.urlopen(req, timeout=TIMEOUT)
    res = f.read()
    if re.search('404 - Not Found', res):
        raise CLOUDNotFoundException
    return res

# Get OpenStack instance ID
def get_os_iid():
    res = urllib2.urlopen(OPENSTACK_UID_URI)
    meta = json.load(res)
    iid = meta['uuid']
    utils.log("INFO", "Instance ID from openstack meta: %s."%iid,('get_os_data','cloud'))
    return iid

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
            utils.log("WARNING", "Execution aborting, exiting ...",('userdata','cloud'))
            return None
        utils.log("DEBUG", "Getting userdata ...",('userdata','cloud'))
        try:
            ud = get_cloud_data(config['network']['userdata'])
        except CLOUDNotFoundException:
            utils.log("WARNING", "Userdata not found. Retrying in %s seconds"%(WAIT_RETRY),('userdata','cloud'))
            time.sleep(WAIT_RETRY)
        except Exception as e:
            utils.log("WARNING", "User data failure, error: '%s'. Retrying in %s seconds"%(e,WAIT_RETRY),('userdata','cloud'))
            time.sleep(WAIT_RETRY)
    return parse_ud(ud, ["APP_ID","WS_URI","VERSION","BASE_REMOTE","GPG_KEY_URI"])

# Get instance ID from CLOUD
def instance_id(config, manager):
    iid = None
    while not iid:
        if not manager.running():
            utils.log("WARNING", "Execution aborting, exiting ...",('instance_id','cloud'))
            return None
        utils.log("DEBUG", "Getting instance id ...",('instance_id','cloud'))

        error = False
        try:
            iid = get_os_iid()
        except Exception as e:
            error = True
            utils.log("DEBUG", "Couldn't get OpenStack ID (%s), trying regular AWS way..."%e,('instance_id','cloud'))
        if error or (not iid):
            try:
                iid = get_cloud_data(config['network']['instance_id'])
            except CLOUDNotFoundException:
                utils.log("ERROR", "Instance ID not found, retrying in '%s' seconds"%(WAIT_RETRY),('instance_id','cloud'))
                time.sleep(WAIT_RETRY)
            except Exception as e:
                utils.log("ERROR", "Instance ID failure, unknown error: '%s', retrying in '%s' seconds"%(e,WAIT_RETRY),('instance_id','cloud'))
                time.sleep(WAIT_RETRY)
    return iid

# Get token from disk
def token(config):
    f = config['global'].get('token')
    utils.log("DEBUG", "Getting token located in %s"%(f),('token','cloud'))
    t = ''
    try:
        with open(f, 'r') as f:
            t = f.read()
    except Exception as e:
        utils.log("WARNING", "Can't get token file (%s): %s, updating token"%(f,e),('token','cloud'))
        utils.reset_token(config)
        try:
            with open(f, 'r') as f:
                t = f.read()
        except Exception as e:
            utils.log("ERROR", "Can't get token file (%s): %s"%(f,e),('token','cloud'))
    return t
