# -*- coding: utf-8 -*-

from irc3 import plugin
from irc3 import userlist
from irc3.plugins.command import command

@plugin
class AnnoucePlugin(object):
    """Annoucement Plugin"""

    requires = [
        'irc3.plugins.command',
        'irc3.plugins.userlist',
    ]

    def __init__(self, bot):
        self.bot = bot

    @command
    def psa(self, mask, target, args):
        """Broadcast a public service announcement to all users
            %%psa [<game>...]
        """
        game = ' '.join(args['<game>'])

        if not game:
            self.bot.privmsg(mask.nick, "I need a game to announce")
        else:
            userlist = ' '.join(self.bot.channels[target])
            msg = '{0}: {1} is inviting everyone to play, {3}.'.format(userlist, mask.nick, game)
            self.bot.privmsg(target, msg)
