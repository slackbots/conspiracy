import requests


def make_keys():
    file = open('api_keys.db')
    pairs = [line.split(': ') for line in file]
    return {k: v.strip() for k, v in pairs}


def get_url(key):
    rtm_start = 'https://slack.com/api/rtm.start'
    return requests.get(rtm_start, params={'token': key}).json()['url']


class RestrictedActionException(Exception):
    def __init__(self):
        super(Exception, self).__init__(self)


class Channel:
    def __init__(self, kwargs):
        self.__dict__.update(kwargs)


class User:
    def __init__(self, kwargs):
        self.__dict__.update(kwargs)


class API:
    def refresh():
        self.team_name, self.team_id, self.team_domain = self._get_team_info()
        self.channels = self._get_channels()
        self.users = self._get_users()

    def __init__(self, token):
        self.token = token
        refresh()
        self.keys = {}

    def _get_team_info(self):
        print("Fetching team info...")
        i = self._send('team.info')['team']
        return i['name'], i['id'], i['domain']

    def _get_channels(self):
        print("Fetching channel list...")
        c = {x['name']: Channel(x) for x in self._send('channels.list')['channels']}
        return c

    def _get_users(self):
        print("Fetching user list...")
        c = {x['name']: User(x) for x in self._send('users.list')['members']}
        return c

    def _send(self, method, **params):
        params['token'] = self.token
        r = requests.post(
            'https://slack.com/api/' + method,
            params=params
        )
        if not r.json()['ok']:
            if r.json()['error'] == 'restricted_action':
                raise RestrictedActionException
            else:
                raise Exception(r.json()['error'])
        return r.json()

    def get_channel_name(self, id):
        for channel in self.channels:
            if self.channels[channel].id == id:
                return self.channels[channel].name

    def get_user_name(self, id):
        for user in self.users:
            if self.users[user].id == id:
                return self.users[user].name

    def get_permalink(self, ts, channel):
        return 'https://' + \
               self.team_domain + \
               '.slack.com/archives/' + \
               self.get_channel_name(channel) + \
               '/p' + \
               ts.replace('.', '')

    def post_as_bot(self, channel, message, username='bot', emoji=''):
        return self._send(
            'chat.postMessage',
            channel=channel,
            text=message,
            icon_emoji=emoji,
            as_user=False,
            username=username,
        )

    def post_as_user(self, channel, message):
        return self._send(
            'chat.postMessage',
            channel=channel,
            text=message,
            as_user=True,
        )

    def pin_message(self, channel, ts):
        print("Pinning message...")
        return self._send(
            'pins.add',
            channel=self.channels[channel].id,
            timestamp=ts
        )

    def invite_to_channel(self, user, channel):
        return self._send(
            'channels.invite',
            channel=channel,
            user=user
        )

    def post_to_all(self, message):
        for channel in self.channels:
            print("Posting to #" + channel + "...")
            self.post_as_bot(channel, message)

    def post_loop(self):
        username = input('username: ')
        emoji = input('emoji: ')
        channel = input('channel: ')
        while True:
            self.post_as_bot(channel, input('> '), username, emoji)
