'''
VisualOps agent protocol defines
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


## GENERAL
# Protocol
PROTOCOL_VERSION=1

## CODES
# Init Requests
HANDSHAKE="Handshake"
# Init Answers
APP_NOT_EXIST="AppNotReady"
# Agent Update
AGENT_UPDATE="AgentUpdate"
# States Server Push
RECIPE_DATA="RecipeMetadata"
# Wait Server Push
WAIT_DATA="State"
# Test message
TEST="Test"
# Test result message
TEST_ANS="TestAns"
# Agent Log Report
STATELOG="StateLog"

## ERROR MESSAGES
M_INVALID_JSON_SEND="Invalid JSON data to send"
M_INVALID_JSON_RECV="Invalid JSON data received"
M_INVALID_WRITE="Can't write on socket"
M_STOP="Shutting down"
M_CLONE="Can't clone states repo"

## ERROR CODES
C_INVALID_JSON_SEND=1000
C_INVALID_JSON_RECV=1000
C_INVALID_WRITE=1000
C_STOP=1000
C_CLONE=1000
