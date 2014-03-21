'''
Madeira OpsAgent protocol defines

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
# Agent Log Report
STATELOG="StateLog"

## ERROR MESSAGES
M_INVALID_JSON_SEND="Invalid JSON data to send"
M_INVALID_JSON_RECV="Invalid JSON data received"
M_INVALID_WRITE="Can't write on socket"
M_STOP="Shutting down"

## ERROR CODES
C_INVALID_JSON_SEND=1000
C_INVALID_JSON_RECV=1000
C_INVALID_WRITE=1000
C_STOP=1000
