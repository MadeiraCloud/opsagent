'''
Madeira OpsAgent AWS requests

@author: Thibault BRONCHAIN
'''


# System imports
import urllib2
import re

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
    try:
        id = get_aws_data(config['network']['instance_id'])
    except AWSNotFoundException:
        utils.log("ERROR", "Instance ID not found, retrying in '%s' seconds."%(WAIT_RETRY),('instance_id','aws'))
        return instance_id(config)
    except Exception as e:
        utils.log("ERROR", "Instance ID failure, unknown error: '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('instance_id','aws'))
        return instance_id(config)
    return id

# Get app ID and token from AWS passed by Madeira
def user_data_real(config):
    try:
        app_id = get_aws_data(config['network']['app_id'])
    except AWSNotFoundException:
        utils.log("ERROR", "App ID not found, retrying in '%s' seconds."%(WAIT_RETRY),('user_data','aws'))
        return user_data(config)
    except Exception as e:
        utils.log("ERROR", "App ID failure, unknown error: '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('user_data','aws'))
        return user_data(config)
    try:
        token = get_aws_data(config['network']['token'])
    except AWSNotFoundException:
        utils.log("ERROR", "Token not found, retrying in '%s' seconds."%(WAIT_RETRY),('user_data','aws'))
        return user_data(config)
    except Exception as e:
        utils.log("ERROR", "Token failure, unknown error: '%s', retrying in '%s' seconds."%(e,WAIT_RETRY),('user_data','aws'))
        return user_data(config)
    return (app_id,token)

# TODO: switch
def user_data(config):
    return ('ethylic','token')
