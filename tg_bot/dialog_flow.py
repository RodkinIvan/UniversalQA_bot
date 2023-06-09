
from dff.script import labels as lbl
from dff.script import conditions as cnd
from dff.script import GLOBAL, TRANSITIONS, RESPONSE, Context, Message
from dff.messengers.telegram import (
    TelegramUI,
    TelegramMessage,
    RemoveKeyboard,
)
from dff.script.core.message import Button
import requests

def generated_response(ctx: Context, actor, *args, **kwargs) -> Message:
    if ctx.validation:
        return Message(text='gen')
    url = 'http://odqa:8141/'
    text = ctx.last_request.text
    request = {
        'questions': [text]
    }
    response, _ = requests.get(url, json=request).json()

    cur_response = response[0]
    response = requests.post(url='http://response_refinement:8030/refine', json={'question': text, 'response': cur_response, })
    model_response = response.json()['refined_resp']
    return Message(text=model_response)

def graph_response(ctx: Context, actor, *args, **kwargs) -> Message:
    if ctx.validation:
        return Message(text='graph')
    url = 'http://graph:5000/'
    text = ctx.last_request.text
    request = {
        'msg': text
    }
    response = requests.get(url=url, params=request).json()
    text = response['response'][0]
    is_terminated = response['is_terminated']
    slots = response['slots']
    if len(slots) != 0:
        text += '\n\nDetected slots:\n'
        text += str(slots)
    if is_terminated:
        text += '\n\nEnd of session. Type /start to begin a new one'
    return Message(text=text)


script = {
    GLOBAL: {
        TRANSITIONS: {
            ('greeting_flow',"greeting_node", 1.1): cnd.exact_match(Message(text="/start")),
        }
    },
    "greeting_flow": {
        "start_node": {
            TRANSITIONS: {
                'greeting_node': cnd.true()
            }
        },
        "greeting_node": {
            RESPONSE: TelegramMessage(
                text="Hello, choose your option",
                ui=TelegramUI(
                    buttons=[
                        Button(text='odqa'),
                        Button(text='graph')
                    ],
                    is_inline=False,
                    row_width=4,
                )
            ),
            TRANSITIONS: {
                ("generating_flow", "start_gen_node"): cnd.exact_match(TelegramMessage(text="odqa")),
                ("graph_flow", "start_graph_node"): cnd.exact_match(TelegramMessage(text="graph")),
            },

        },
        "fallback_node": {
            RESPONSE: Message(text="Please, start another session with /start"),
            TRANSITIONS: {
                'greeting_node': cnd.true()
            }
        },
    },
    'generating_flow': {
        'start_gen_node':{
            RESPONSE: TelegramMessage(text='Ask questions', ui=RemoveKeyboard()),
            TRANSITIONS: {
                'gen_node': cnd.true()
            }
        },  
        'gen_node': {
            RESPONSE: generated_response,
            TRANSITIONS: {
                lbl.repeat(): cnd.true()
            }
        }
    },
    'graph_flow': {
        'start_graph_node':{
            RESPONSE: TelegramMessage(text='Send requests', ui=RemoveKeyboard()),
            TRANSITIONS: {
                'graph_node': cnd.true()
            }
        },  
        'graph_node': {
            RESPONSE: graph_response,
            TRANSITIONS: {
                lbl.repeat(): cnd.true()
            }
        }
    }
}