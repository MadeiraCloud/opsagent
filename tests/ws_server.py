'''
VisualOps Manager Unit Tests WebServer
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

from __future__ import print_function

import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import EchoWebSocket,WebSocket

import base64
from hashlib import sha1
import inspect
import threading

import urllib2
import re
import json


def print(*args, **kwargs):
    """Custom print() function."""
    __builtins__.print('SERVER: ', end="")
    return __builtins__.print(*args, **kwargs)

# Temporary openstack IP define
OPENSTACK_UID_URI="http://169.254.169.254/openstack/latest/meta_data.json"
AWS_UID_URI="http://169.254.169.254/latest/meta-data/instance-id"
TIMEOUT=2

# Get data
def get_cloud_data(url):
    req = urllib2.Request(url)
    f = urllib2.urlopen(req, timeout=TIMEOUT)
    res = f.read()
    if re.search('404 - Not Found', res):
        raise Exception
    return res

# Get OpenStack instance ID
def get_os_iid():
    res = urllib2.urlopen(OPENSTACK_UID_URI, timeout=TIMEOUT)
    meta = json.load(res)
    iid = meta['uuid']
    print("Instance ID from openstack meta: %s."%iid)
    return iid

# Get instance ID from CLOUD
def instance_id():
    iid=""
    try:
        iid = get_os_iid()
    except Exception as e:
        print("Couldn't get OpenStack ID (%s), trying regular AWS way..."%(e))
        error = True
    if error or (not iid):
        try:
            iid = get_cloud_data(AWS_UID_URI)
            print("Instance ID from AWS:%s."%iid)
        except Exception as e:
            print("Instance ID failure, error: '%s'"%(e))
    return iid

valid = {
    "code"             :   "Test",
    "instance_id"      :   instance_id(),
    "app_id"           :   "app-id",
    "agent_version"    :   "1.0",
    "protocol_version" :   1,
    "instance_token"   :   "testtoken",
    "init_errors"      :   [None,"Can't create '/proc' directory: '[Errno 13] Permission denied: '/proc''. FATAL"]
}



class Root(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        print("Index")
        return "Index"

    @cherrypy.expose
    def agent(self):
        print("Agent")
        handler = cherrypy.request.ws_handler

class Actions(WebSocket):
    def received_message(self, message):
        print("got_message")
        d = json.loads(message.data)
        if d.get("code") == "Handshake":
            r = self.test(d)
        elif d.get("code") == "Test":
            r = self.test_ans(d)
        self.send(json.dumps(r))

    def test(self, d):
        print("Got request")
        return {
            "code": "Test"
        }

    def test_ans(self, d):
        print("Got TestAns")
        error = None
        for key in valid:
            if type(valid[key]) is not list:
                valid[key] = [valid[key]]
            if d.get(key) not in valid[key]:
                error = "Invalid value (%s), should be '%s'; got '%s'"%(key,"', or '".join(valid[key]),d.get(key))
                break
        return {
            "code":"TestAns",
            "result":(False if error else True),
            "error":error
        }

cherrypy.config.update({'server.socket_port': 9000})
WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()
cherrypy.quickstart(Root(), '/', config={'/agent': {'tools.websocket.on': True,
                                                    'tools.websocket.handler_cls': Actions}})
