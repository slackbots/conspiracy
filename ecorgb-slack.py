import re
from datetime import datetime

#import requests
api = __import__('fake_api')
websocket = __import__('fake_websocket')

import ecorgb
import playerrgb

eco_key = api.make_keys()['ecorgb']
slack = api.API(eco_key)

players = {}
player_names = {}
game = ecorgb.EcoEnv(ecorgb.make_region(tree=20, bean=15))


def pb_send(channel, message):
    slack.post_as_bot(
        channel,
        message,
        'Pybot',
        ':godmode:'
    )


do_functions = {}


def do_commands(message):
    string = message['text']
    words = string.split()[1:]
    channel = message['channel']
    user = message['user']
    now = datetime.fromtimestamp(float(message['ts']))
    if user not in players:
        pb_send(channel, "You are not an active player; register with `ACC register`")
    elif players[user].stun > now:
        pb_send(channel, "You are still busy")
    else:
        todo = do_functions[words[0]]
        return todo[0](message['channel'], user, words[1:], now, todo[1:]);


def do_targeted(channel, user, words, time_when, args):
    action, target_type = args
    targets = players[user].find_all(game, type=target_type)
    target = targets[0] if targets else None
    players[user].do(game, time_when, action, target_location=(players[user].loc, 0, target))

do_functions = {
    'chop': (do_targeted, 'chop', 'tree'),
    'eat': (do_targeted, 'eat', 'bean'),
    'plant': (do_targeted, 'plant', 'bean'),
    'pick': (do_targeted, 'pick', 'bean stalk'),
}


def acc_commands(message):
    syntax = "ACC"
    string = message['text']
    words = string.split()[1:]
    channel = message['channel']
    user = message['user']
    now = datetime.fromtimestamp(float(message['ts']))
    if words == []:
        pass
    elif words[0] == 'register':
        syntax += " register <alias>"
        if len(words) > 2:
            pb_send(channel, "`{syntax}` alias must not contain spaces".format(syntax=syntax))
        elif len(words) < 2:
            pb_send(channel, "`{syntax}`".format(syntax=syntax))
        elif words[1] in player_names:
            pb_send(channel, "that name is taken")
        else:
            player_names[words[1]] = players[user] = playerrgb.Player(game, now)


event_output = {
    'transform': "[{location[0]} - {location[1]}] A {from_type} became a {to_type}! (@{location[2]})",
    'disappear': "[{location[0]} - {location[1]}] A {from_type} disappeared! (@{location[2]})",
    'appear': "[{location[0]} - {location[1]}] A {to_type} appeared! (@{location[2]})",
}


def set_output(message):
    global main_channel
    main_channel = message['channel']


responses = {}
functions = {
    #r'pb .+': pb_commands
    r'DO .+': do_commands,
    r'ACC .+': acc_commands,
    r'SET OUTPUT': set_output
}.items()

w = websocket.WebSocket()

wss_url = api.get_url(eco_key)
init_time = datetime.now()
w.connect(wss_url)

while True:
    n = w.next().replace('true', 'True').replace('false', 'False').replace('none', 'None')
    print(n)
    n = eval(n)
    if 'ts' in n:
        game.call_events(datetime.fromtimestamp(float(n['ts'])))
    if all([
        n['type'] == 'message',
        n['hidden'] if 'hidden' in n else True,  # why is this here
        'bot_id' not in n,
        datetime.fromtimestamp(float(n['ts'])) > init_time if 'ts' in n else False
    ]):
        for key, func in functions:
            if re.match(key, n['text']):
                func(n)
                continue
       # for response in responses:
       #     if re.match(response, n['text']):
       #         pb_send(n['channel'], responses[response])
       #         continue
    for rec in game.flush_records():
        if 'actor' in rec:
            actor = rec['actor']
            rec['actor'] = 'Nobody'  # This way {actor} is available to str.format()
            for player_name, player in player_names.items():
                if player is actor:
                    rec['actor'] = player_name  # I smell Python
                    break
        pb_send(main_channel, event_output[rec['nature']].format(**rec))

