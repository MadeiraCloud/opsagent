'''
Madeira OpsAgent protocol defines

@author: Thibault BRONCHAIN
'''


## GENERAL
# Protocol
PROTOCOL_VERSION="1"

## CODES
# Init Requests
HANDSHAKE="Handshake"
# Init Answers
APP_NOT_EXIST="AppNotReady"
# States Server Push
RECIPE_DATA="RecipeMetadata"
# Wait Server Push
WAIT_DATA="State"
# Agent Log Report
STATELOG="state_log"

## ERROR MESSAGES
M_INVALID_JSON_SEND="Invalid JSON data to send"
M_INVALID_JSON_RECV="Invalid JSON data received"

## ERROR CODES
C_INVALID_JSON_SEND=1000
C_INVALID_JSON_RECV=1000
