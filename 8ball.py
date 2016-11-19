# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.8ball` 8-Ball plugin
=================================================

A simple fortune telling plugin,
because every irc bot needs an 8-ball

"""

import asyncio
import random
import re

import irc3
from irc3.plugins.command import command


@irc3.plugin
class RandomPlugin(object):
    """Plugin to provide:

    * 8 Ball
    * coin flip
    * roll dice
    """

    def __init__(self, bot):
        self.bot = bot

    @command(name='8ball')
    def eight_ball(self, mask, target, args):
        """
        8ball - Answers all you're questions, with 100%\ accuracy.
        %%8ball [<question>]...
        """
        answers = [
            'It is certain',
            'It is decidedly so',
            'Without a doubt',
            'Yes, definitely',
            'You may rely on it',
            'As I see it, yes',
            'Most likely',
            'Outlook good',
            'lol',
            'Signs point to yes',
            'Reply hazy try again',
            'Ask again later',
            'Better not tell you now',
            'Cannot predict now',
            'Concentrate and ask again',
            'Don\'t count on it',
            'My reply is no',
            'My sources say no',
            'Outlook not so good',
            'Very doubtful'
        ]

        response = random.choice(answers)
        self.bot.privmsg(target, response)

    #FIXME
    @command
    def choose(self, mask, target, args):
        """
        Choose - Makes a decision for you.
        %%choose <question>...
        """
        question = ' '.join(args['<question>'])

        if re.search('(?:\bor\b)', question):
            choices = re.findall('(?:\bor\b)', question)
        elif re.search('([^;,]+)', question):
            choices = re.findall('([^;,]+)', question)
        else:
            choices = re.findall('(\w+)', question)

        decision = random.choice(choices)
        self.bot.privmsg(target, decision)

    @command
    def roll(self, mask, target, args):
        """
        Roll - Rolls a dice, follows D&D dice notation (e.g. 1d20)
        %%roll [<dice>]
        """
        if target == self.bot.nick:
            target = mask.nick
        response = self._roll(args)
        self.bot.privmsg(target, response)

    def _roll(self, args):
        """returns proper roll to roll request"""
        roll = " ".join(args['<dice>'] or [])
        dice = re.findall('(^\d)d(\d+$)', roll)

        if not roll:
            # defaults to 1d6
            num = 1
            sides = 6
        elif not dice:
            response = "That's not a valid roll"
            return response
        else:
            num = int(dice[0][0])
            sides = int(dice[0][1])
            if (num or sides) > 101:
                response = "That's too much"
                return response
        total = 0
        for i in range(num):
            total += random.randrange(sides + 1)
        return str(total)

    @classmethod
    def reload(cls, old):
        return cls(old.bot)
