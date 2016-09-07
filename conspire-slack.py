import re
import os
import random
import sys
from datetime import datetime

api = __import__('api')
websocket = __import__('websocket')

logfile = "logfile.txt"

conspire_key = api.make_keys()['conspiracy']
slack = api.API(conspire_key)

if not os.path.exists(logfile):
    open(logfile, 'x').close()


def get_user_name(id):
    return slack.get_user_name(id)


def echo(message):
    print(message)
    with open(logfile, 'a') as logfileobj:
        logfileobj.write(message + '\n')


def send(channel, message):
    slack.post_as_bot(
        channel,
        message,
        'Game Master',
        ':tophat:'
    )


admins = ['spivee', 'lyneca']
signup = set()


def inform_players():
    for target_id, kappa_id in kappa.items():
        send(target_id, "{kappa_name} can cap you.".format(kappa_name=get_user_name(kappa_id)))


def sign_up(message):
    text = message['text'].replace('sign up', 'signup')
    if len(text.split()) > 2 and get_user_name(message['user']) in admins:
        if text.split()[2] in slack.users:
            user = slack.users[text.split()[2]].id
        else:
            send(message['channel'], "%s is not a valid user." % text.split()[2])
            return
    else:
        user = message['user']
    signup.add(user)
    send(message['channel'], "%s has signed up." % get_user_name(user))
    echo("User %s signed up." % get_user_name(user))


def sign_down(message):
    text = message['text'].replace('sign down', 'signdown')
    if len(text.split()) > 2 and get_user_name(message['user']) in admins:
        if text.split()[2] in slack.users:
            user = slack.users[text.split()[2]].id
        else:
            send(message['channel'], "%s is not a valid user." % text.split()[2])
            return
    else:
        user = message['user']
    signup.remove(user)
    send(message['channel'], "%s has signed down." % get_user_name(user))
    echo("User %s signed down." % get_user_name(user))


def admin(command):
    def decorated(message):
        if 'user' in message and get_user_name(message['user']) in admins:
            command(message)

    return decorated


def player(command):
    def decorated(message):
        if 'user' in message:
            if message['user'] in kappa:
                command(message)
            else:
                send(message['channel'], "You must be playing to use that command.")

    return decorated


@admin
def start_game(message):
    global signup, kappa, swapreq, functions, main_channel, eliminated
    if len(signup) < 2:
        send(message['channel'], "At least two players required to start the game.")
        return
    main_channel = message['channel']
    eliminated = []
    chain = list(signup)
    random.shuffle(chain)
    kappa = {chain[i - 1]: chain[i] for i in range(len(chain))}
    del signup
    swapreq = set()
    functions = game_functions
    send(main_channel, "The game has started! There are {} players.".format(len(kappa)))
    echo("Game started.")
    inform_players()


@admin
def promote(message):
    channel = message['channel']
    words = message['text'].split()[2:]
    user_name = '_'.join(words)
    if user_name not in slack.users:
        send(channel, "Player \"%s\" not found." % user_name)
        return
    admins.append(user_name)
    send(channel, "Promoted %s to admin." % user_name)
    echo("User %s promoted %s" % (get_user_name(message['user']), user_name))


@admin
def demote(message):
    channel = message['channel']
    words = message['text'].split()[2:]
    user_name = '_'.join(words)
    if user_name not in list(slack.users.keys()) + admins:
        send(channel, "Player \"%s\" not found." % user_name)
        return
    admins.remove(user_name)
    send(channel, "Demoted %s to user." % user_name)
    echo("User %s demoted %s" % (get_user_name(message['user']), user_name))


def end_routine():
    global kappa, swapreq, signup, functions, main_channel, eliminated
    del kappa
    del swapreq
    del main_channel
    del eliminated
    signup = set()
    functions = prep_functions


@admin
def end_game(message):
    end_routine()
    send(message['channel'], "Game ended.")
    echo("Game ended.")


def save_routine():
    out = open('kappa.dat', 'w')
    out.write('\n'.join("{}: {}".format(k, v) for k, v in kappa.items()))
    out.close()
    out = open('swapreq.dat', 'w')
    out.write('\n'.join("{}: {}".format(k, v) for k, v in swapreq))
    out.close()
    out = open('eliminated.dat', 'w')
    out.write('\n'.join(eliminated))
    out.close()


@admin
def save_game(message):
    save_routine()
    send(message['channel'], "Game successfully saved.")
    echo("Game saved.")


@admin
def load_game(message):
    global signup, kappa, swapreq, functions, main_channel, eliminated
    functions = game_functions
    main_channel = message['channel']
    del signup
    kappaf = open('kappa.dat')
    kappa = dict(line.rstrip().split(': ') for line in kappaf)
    kappaf.close()
    swapf = open('swapreq.dat')
    swapreq = set(line.rstrip().split(': ') for line in swapf)
    swapf.close()
    elimf = open('eliminated.dat')
    eliminated = [line.rstrip() for line in elimf]
    elimf.close()
    send(message['channel'], "Game successfully loaded.")
    echo("Game loaded.")
    inform_players()


def refresh(message):
    echo("User %s triggered a refresh" % get_user_name(message['user']))
    slack.refresh()


def show_kappa(sharer, target, format="{default_message}", back_format="{default_message}"):
    if sharer not in kappa:
        send(sharer, "You cannot share anything in response as you are eliminated.")
    sharer_kappa = kappa[sharer]
    sharer_name = get_user_name(sharer)
    sharer_kappa_name = get_user_name(sharer_kappa)
    target_name = get_user_name(target)
    fargs = {
        'sharer': sharer_name,
        'sharer_kappa': sharer_kappa_name,
        'target': target_name,
    }
    default_forward = "{sharer} has shared with you that {sharer_kappa} can cap them.".format(**fargs)
    default_backward = "{target} has been informed of your kappa.".format(**fargs)
    send(target, format.format(default_message=default_forward, **fargs))
    if back_format:
        send(sharer, format.format(default_message=default_backward, **fargs))


@player
def fakeinfo(message):
    string = message['text']
    sender = message['user']
    target = string.split()[3]
    kappa = string.split()[2]
    send(sender, "%s has shared with you that %s can cap them." % (target, kappa))
    send(sender, "In response, %s has been informed of your kappa." % target)


@player
def kswap(message):
    string = message['text']
    words = string.split()[2:]
    channel = message['channel']
    caller = message['user']
    flag = words.pop(-1)
    if flag not in ['direct', 'cancel', 'delay']:
        words.append(flag)
        flag = 'delay'
    target_name = '_'.join(words)
    if target_name not in slack.users:
        send(channel, "Player \"{}\" not found.".format(target_name))
        return
    target = slack.users[target_name].id
    if flag == 'cancel':
        send(channel, "Share request cancelled." if (caller, target) in swapreq else "Share request not found.")
        swapreq.discard((caller, target))
    else:
        if (target, caller) in swapreq:  # happens whether flag is 'direct' or 'delay'
            swapreq.remove((target, caller))
            show_kappa(sharer=caller, target=target)
            show_kappa(sharer=target, target=caller, format="In response, {default_message}",
                       back_format="In response, {default_message}")
        elif flag == 'delay':
            swapreq.add((caller, target))
        elif flag == 'direct':
            show_kappa(sharer=caller, target=target)


@player
def cap(message):
    target_name = '_'.join(message['text'].split()[2:])
    caller = message['user']
    caller_name = get_user_name(caller)
    if target_name in slack.users:
        target = slack.users[target_name].id
        if target not in kappa:
            send(message['channel'], target_name + (
                " has already been eliminated!" if target in eliminated else " is not playing this game."))
        elif kappa[target] == caller:
            eliminate(target, 'capped')
            echo("User %s capped %s." % (caller_name, get_user_name(target)))
        else:
            eliminate(caller, 'failed')
            echo("User %s capped the wrong target (%s)." % (caller_name, get_user_name(target)))
    else:
        send(message['channel'], "Player \"{}\" not found.".format(target_name))


@player
def resign(message):
    eliminate(message['user'], 'resigned')
    echo(get_user_name(message['user']) + " resigned.")


@admin
def broadcast(message):
    text = ' '.join(message['text'].split()[2:])
    echo(message['user'] + ' broadcasted "' + text + '"')
    send(slack.channels['events'].id, text)


@admin
def terminate(message):
    global running
    running = False
    send(message['channel'], "Program terminated.")
    echo("User %s terminated the server." % get_user_name(message['user']))


def list_players(message):
    text = '*Players left alive:*\n```' + '\n'.join(sorted([get_user_name(x) for x in kappa])) + '```'
    if len(eliminated) > 0:
        text += '\n*Players eliminated:*\n```' + '\n'.join(sorted(eliminated)) + '```'
    send(message['channel'], text)


def list_signers(message):
    send(message['channel'],
         '*Players signed up:*\n```' + '\n'.join(sorted([get_user_name(x) for x in signup])) + '```')


def ping(message):
    send(message['channel'], "pong")


@admin
def log(message):
    echo("%s: %s" % (get_user_name(message['user']), ' '.join(message['text'].split()[2:])))


functions = prep_functions = {
    r'gm sign ?up.*': sign_up,
    r'gm sign ?down.*': sign_down,
    r'gm start': start_game,
    r'gm load': load_game,
    r'gm terminate': terminate,
    r'gm list': list_signers,
    r'gm ping': ping,
    r'gm log .+': log,
    r'gm promote .+': promote,
    r'gm demote .+': demote,
    r'gm refresh': refresh,
    r'gm broadcast': broadcast,
}.items()

game_functions = {
    r'gm kswap .+': kswap,
    r'gm fakeinfo .+': fakeinfo,
    r'gm cap .+': cap,
    r'gm resign .+': resign,
    r'gm end': end_game,
    r'gm save': save_game,
    r'gm list': list_players,
    r'gm ping': ping,
    r'gm log .+': log,
    r'gm promote .+': promote,
    r'gm demote .+': demote,
    r'gm broadcast': broadcast,
}.items()

elim_msg = {
    'capped': '{elim} has been capped by {capped_by} and has been eliminated!',
    'resigned': '{elim} has resigned from the game.',
    'failed': '{elim} capped the wrong player, ({wrong_target}) and has been eliminated!',
}


def eliminate(id, reason, wrong_target_name=''):
    has_new_target = kappa.pop(id)
    name = get_user_name(id)
    eliminated.append(name)
    has_new_target_name = get_user_name(has_new_target)
    has_new_kappa = [k for k in kappa if kappa[k] == id][0]
    send(main_channel,
         elim_msg[reason].format(elim=name, capped_by=has_new_target_name, wrong_target=wrong_target_name))
    if has_new_target == has_new_kappa:
        eliminated.append(has_new_target_name)
        eliminated.reverse()
        send(main_channel, "The game is over! The results are as follows: \n```" + '\n'.join(
            str(num + 1).rjust(2) + ': ' + place for num, place in enumerate(eliminated)) + '```')
        end_routine()
    else:
        kappa[has_new_kappa] = has_new_target
        send(has_new_kappa, "{new_kappa} can now cap you.".format(new_kappa=has_new_target_name))
        save_routine()


w = websocket.WebSocket()
print("Connecting to socket...")
wss_url = api.get_url(conspire_key)
init_time = datetime.now()
w.connect(wss_url)
print("Ready.")
send(slack.channels['events'].id, "Game server up.")
running = True
while running:
    n = w.next().replace('true', 'True').replace('false', 'False').replace('none', 'None').replace('null', 'None')
    # print(n)
    n = eval(n)
    if all([n['type'] == 'message' if 'type' in n else False, n['hidden'] if 'hidden' in n else True, 'bot_id' not in n,
            datetime.fromtimestamp(float(n['ts'])) > init_time if 'ts' in n else False
            ]):
        original_message = n['text']
        for line in original_message.lower().split('\n'):
            not_command = True
            for key, func in functions:
                n['text'] = line
                if re.match(key, line):
                    not_command = False
                    try:
                        func(n)
                    except Exception as e:
                        send(slack.channels['events'].id, "Program terminated due to exception: `" + str(e) + '`')
                        echo("Exception: " + str(e))
                        sys.exit()
                    continue

            if line.split()[0] == 'gm' and not_command:
                send(n['channel'], "Invalid `gm` command.")
# for response in responses:
#     if re.match(response, n['text']):
#         pb_send(n['channel'], responses[response])
#         continue
