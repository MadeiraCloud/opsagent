'''
Madeira OpsAgent AWS requests

@author: Thibault BRONCHAIN
'''


# System imports
import urllib2
import re
import time

# Internal imports
from opsagent.exception import *
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

# Get instance ID from AWS
def instance_id(config):
    utils.log("DEBUG", "Getting instance id ...",('instance_id','aws'))
    try:
        id = get_aws_data(config['network']['instance_id'])
    except AWSNotFoundException:
        utils.log("ERROR", "Instance ID not found, retrying in '%s' seconds."%(WAIT_RETRY),('instance_id','aws'))
        time.sleep(WAIT_RETRY)
        return instance_id(config)
    except Exception as e:
        utils.log("ERROR", "Instance ID failure, unknown error: '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('instance_id','aws'))
        time.sleep(WAIT_RETRY)
        return instance_id(config)
    return id

# Get app ID from AWS passed by Madeira
def app_id(config):
    utils.log("DEBUG", "Getting app id ...",('instance_id','aws'))
    try:
        user_data = get_aws_data(config['network']['user_data'])
    except AWSNotFoundException:
        utils.log("ERROR", "User data not found, retrying in '%s' seconds."%(WAIT_RETRY),('user_data','aws'))
        time.sleep(WAIT_RETRY)
        return app_id(config)
    except Exception as e:
        utils.log("ERROR", "User data failure, unknown error: '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('user_data','aws'))
        time.sleep(WAIT_RETRY)
        return app_id(config)
    try:
        r = re.search("#app_id=(.+)\n",user_data)
        app_id = r.group(1)
    except Exception as e:
        utils.log("ERROR", "Can't get appid '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('user_data','aws'))
        time.sleep(WAIT_RETRY)
        return app_id(config)
    return app_id

# TODO: token
def token(config):
    return ('token')

# TODO: delete
def app_id_t(config):
    return ('ethylic')
def isntance_id_t(config):
    return ('slurry')
def token_t(config):
    return ('token')
