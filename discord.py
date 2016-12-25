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
        #Discord bot token
        try:
            self.token = self.config['token']
        except:
            raise

    @command
    def play(self, mask, target):
        """
        play - Response with the current game discord members are playing

        %%play
        """
        @asyncio.coroutine
        def wrap():
            response = yield from self.play_response(mask)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

    @asyncio.coroutine
    def play_response(self, mask):
        """
        Returns the appropriate response to .play request
        """
        gamer = yield from self.discord_socket()

        irc_users = {}
        for usr in self.bot.channels[target]:
            discord_id = self.set_ID(usr)
            irc_users[discord_id] = usr

        #result = [irc_users[key]: gamer[key] for key in gamer if key in irc_users]

        result = [(gamer[key], irc_users[key]) for key in gamer if key in irc_users]

        d = defaultdict(list)
        for key, value in result:
            d[key].append(value)
        results = sorted(d.items())

        response = ''
        for game, player in results:
            if len(player) > 1:
                response += '{0} are playing {1}. '.format(', '.join(player), game)
            else:
                response += '{0} is playing {1}. '.format(player[0], game)

    @asyncio.coroutine
    def discord_socket(self):

    r = requests.get('https://discordapp.com/api/gateway')
    baseurl = r.json()['url']
    url = baseurl + '/?encoding=json&v=5'

    identify = {
        "op": 2,
        "d": {
            "token": self.token,
            "properties": {
                "$os": "linux" ,
                "$browser": "solbot.py",
                "$device": "solbot.py",
                "$referrer": "",
                "$referring_domain": ""
            },
            "compress": False,
            "large_threshold": 50
        }
    }
    #FIXME Not the correct way
    ws = create_connection(url)
    hello = ws.recv()               # OP 10 Hello payload
    ws.send(json.dumps(identify))   # OP 2 Identify
    ready = ws.recv()               # Ready payload
    response = ws.recv()            # Dispatch payload
    ws.close()

    guild = AttrDict(json.loads(response))
    pres = guild.d.presences

    gamer = {}
    for usr in pres:
        if usr.game:
            gamer[usr.user.id] = usr.game.name

    return gamer

    @command
    def discord(self, mask, target, args):
        """
        set Discord ID for a user

        %%discord <discord ID>
        """
        if target == self.bot.nick:
            target = mask.nick
        did = args['<discord ID>']
        self.log.info("Storing Discord ID {0} for {1}".format(did, mask.nick))
        self.bot.get_user(mask.nick).set_setting('discord_id', did)

    @asyncio.coroutine
    def get_ID(self, nick):
        """Gets the discord id,associated with a user from the database.
        """
        # XXX if there's no database setting for the user,
        # it will return the nick?
        user = self.bot.get_user(nick)
        result = yield from user.get_setting('discord_id', nick)
        if result == nick:
            return None
        else:
            return result
