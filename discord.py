# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.discord` Discord plugin
=================================================

Basic plugin for discord

"""
import asyncio

import requests
import json
import websocket
from websocket import create_connection
import irc3
from irc3.plugins.command import command

@irc3.plugin
class DiscordPlugin(object):
    """Plugin to provide:

        * Discord Plugin
    """

    requires = [
        'irc3.plugins.command',
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


    @command
    def play(self, mask, target, args):
        """
        play - Response with the current game discord members are playing

        %%play
        """
        @asyncio.coroutine
        def wrap():
            response = yield from self.p_respn(mask)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

    @asyncio.coroutine
    def p_respn(self, mask):
        """
        Returns the appropriate response to .play request
        """

    @asyncio.coroutine
    def discord_socket(self):
    r = requests.get('https://discordapp.com/api/gateway')
    baseurl = r.json()['url']
    url = baseurl + '/?encoding=json&v=5'

    ws = create_connection(url)
identify = {
        "op": 2,
        "d": {
            "token": "MjI4OTI5MTcxNjk3NTY1Njk2.Cz-_pw.47nwJ54RGyHZo1dHzR1nKgv99LI",
            "properties": {
                "$os": "linux" ,
                "$browser": "solbot.py",
                "$device": "solbot.py",
                "$referrer": "",
                "$referring_domain": ""
            },
            "compress": false,
            "large_threshold": 50
        }
    }
