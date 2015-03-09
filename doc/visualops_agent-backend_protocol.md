# VisualOps: Agent-Backend Protocol

The Agent-Backend protocol is based on WebSocket

## What's new

* add Agent update message
* add `agent_version` in Handshake message 

## Events

- Start/stop software provision
- Recipe update 
- Agent connect/shutdown
- Backend failover

## Backend states

1. App not exist
2. App created (instances not configured)
3. instance waiting handshake (configured)
4. instance connected

The states transition are shown in the following figure
![Backend states transition](https://trello-attachments.s3.amazonaws.com/52a2c14514970df65f0005ef/52c189b6cb9876613e061c2d/9d919730edee1f4b9aad7432e02d62cd/visualops-backend-states-transition.001.png)

## Messages

In `APP_NOT_EXIST` and `APP_CREATED` states, **all WS requests** would not be accepted (return an error result frame), instead, a notification would be sent to `appservice`, for the case new APP or backend failover. The error frame from backend will like

    {
        "code": "AppNotReady"
    }

The agent should keep retry before the APP becoming ready. In `INST_WAIT_AGENT` state, backend is waiting for `Handshake` from agent, if it is verified as valid, transit to `INST_CONN` state. `Handshake` message will like:

    {
        "code"             :   "Handshake",
        "instance_id"      :   "id_of_instance",
        "app_id"           :   "id_of_app",
        "protocol_version" :   1,
        "agent_version"    :   "xxx.xx",
        "instance_token"   :   "token_of_instance"
    }

if the agent handshake with a wrong "`agent_version`", the opsBackend will ask agent to update itself.

In `INST_CONN` state:

### Recipe Push

For 

a. new connection after handshake
b. recipe update

Backend will push new recipe to agent. The message will like

    {
        "code":                "RecipeMetadata",
        "recipe_version":      1,
        "module": {
            "repo":            "",
            "tag":             ""
        },
        "state": [
            {
                "stateid":     "id_of_the_state",
                "module":      "module_of_the_state",
                "parameter": {
                    "param1":  "foo",
                    "param2":  "bar"
                }
            },
            {
                "stateid":     "id_of_the_second_state",
                "module":      "module_of_the_second_state",
                "parameter": {
                    "param1":  "foo",
                    "param2":  "bar"
                }
            },
        ]
    }

The `state` field includes the recipe, which is rendered by the `RequestWorker`. And if the update version has no different with the previous one (for the specific instance), then backend will send a message only contain the header part:

    {
        "code":                "RecipeMetadata",
        "recipe_version":      2,
    }

Agent should bumping its recipe version.

### Agent Report

Agent report the state running result, success or fail. It report for a state result, the message will like

    {
        "code":            "StateLog",
        "instance_id":     "id_of_instance",
        "app_id":          "id_of_app",
        "recipe_version":  1,
        "stateid":         "id_of_the_state",
        "state_result":    true,
        "state_comment":   "blahblah...",
        "state_stdout":    "blahblah..."
    }

### Reconnect

New `Handshake` message should be treated as reconnect if success, or it should be ignored

### Agent Update

The agent update is initiated by backend

    {
        "code":           "AgentUpdate",
        "version":        "xxx.xxx",
        "url":            "https://xxxxxx.xx.com/xxxx?xxxx",
    }

after agent update, it will restart itself and reconnect to the backend.

### Wait States Query

Agent can query for its waiting states with the following query

    {
        "code":            "WaitQuery",
        "instance_id":     "id_of_instance",
        "app_id":          "id_of_app",
        "recipe_version":  1,
    }

The response will like

    {
        "code":            "WaitList",
        "recipe_version":  1,
        "waited": [
            {
                "instance_id":   "foo",
                "state_id":      "bar"
            },
            {
                "instance_id":   "foo",
                "state_id":      "bar"
            }
        ]
    }



### Wait States Push

Whenever a waited state is finished, backend will push a message to Agent (if it is running). the message will like

    {
        "code":           "State",
        "recipe_version": 1,
        "stateid":        "the_id_of_the_wait_state"
    }

If an agent is (re)connected, it can also get the push for all the finished states it is waiting. 