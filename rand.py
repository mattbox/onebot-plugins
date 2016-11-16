# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.rand` event plugin
=================================================
"""
import irc3
from irc3 import plugin, event


@plugin
class RandPlugin(object):

    def __init__(self, bot):
        self.bot = bot

    @event('^:(?P<mask>\S+!\S+@\S+) PRIVMSG (?P<target>\S+) :\s*(Hi|hi)$')
    def hi(self, mask, target):

        if target == self.bot.nick:
            target = mask.nick
        
        response = 'hi, {}'.format(mask.nick)
        self.bot.privmsg(target, reponse)
