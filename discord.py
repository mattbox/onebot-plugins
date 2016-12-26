# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.discord` Discord plugin
=================================================

Basic plugin for discord
Very quick and dirty

"""
import asyncio

import requests
import json
import websocket
from websocket import create_connection
from attrdict import AttrDict

from collections import defaultdict
import irc3
from irc3.plugins.command import command


@irc3.plugin
class DiscordPlugin(object):
    """Plugin to provide:

        * Discord Plugin
    """

    requires = [
        'irc3.plugins.command',
        'irc3.plugins.userlist',
        'onebot.plugins.users'
    ]

    def __init__(self, bot):
        """Initialize the plugin"""
        self.bot = bot
        self.log = bot.log.getChild(__name__)
        self.config = bot.config.get(__name__, {})
        # Discord bot token
        try:
            self.token = self.config['token']
        except:
            raise

    @command
    def play(self, mask, target, args):
        """
        play - Response with the current game discord members are playing

        %%play
        """
        @asyncio.coroutine
        def wrap():
            response = yield from self.play_response(mask, target)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

    @asyncio.coroutine
    def play_response(self, mask, target):
        """
        Returns the appropriate response to .play request
        """
        wsr = self.discord_socket()
        gamer = _parse_response(wsr)

        irc = {}
        for nick in self.bot.channels[target]:
            if not nick:
                continue
            discord_id = yield from self.get_ID(nick)
            if discord_id:
                irc[discord_id] = nick

        result = [(gamer[key], irc[key]) for key in gamer if key in irc]

        d = defaultdict(list)
        for key, value in result:
            d[key].append(value)

        results = sorted(d.items())  # [('game',[usr1, usr2]),('game2',[usr3)]

        response = ''
        for game, player in results:
            if len(player) > 1:
                response += '{0} are playing {1}. '.format(
                    ', '.join(player), game)
            else:
                response += '{0} is playing {1}. '.format(player[0], game)

        return response

    def discord_socket(self):
        """
        Handles the websocket with discord's gateway server, returns appropriate response as dictonary
        """
        r = requests.get('https://discordapp.com/api/gateway')
        baseurl = r.json()['url']
        url = baseurl + '/?encoding=json&v=5'

        self.log.info('requested url: ' + url)
        identify = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "linux",
                    "$browser": "solbot.py",
                    "$device": "solbot.py",
                    "$referrer": "",
                    "$referring_domain": ""
                },
                "compress": False,
                "large_threshold": 50
            }
        }
        # FIXME Not the correct way
        self.log.info('connecting to websocket')
        ws = create_connection(url)
        hello = ws.recv()               # OP 10 Hello payload
        ws.send(json.dumps(identify))   # OP 2 Identify
        ready = ws.recv()               # Ready payload
        response = ws.recv()            # Dispatch payload
        ws.close()

        result = json.loads(response)
        self.log.info(result)
        return result

    @command
    def discord(self, mask, target, args):
        """set Discord ID for a user

        %%discord <id>
        """
        self.log.info("Storing Discord ID: {0} for {1}".format(
            args['<id>'], mask.nick))
        self.bot.get_user(mask.nick).set_setting('discord', args['<id>'])

    @asyncio.coroutine
    def get_ID(self, nick):
        """Gets the discord id, associated with a user from the database.
        """
        user = self.bot.get_user(nick)
        if user:
            result = yield from user.get_setting('discord', None)
            return result

    @classmethod
    def reload(cls, old):
        return cls(old.bot)


def _parse_response(response):
    """Parses the websocket response in a dict  "discord_id": "game"
    """
    guild = AttrDict(response)
    prsn = guild.d.presences

    gamer = {}
    for usr in prsn:
        if usr.game:
            gamer[usr.user.id] = usr.game.name

    return gamer
