# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.weather` Weather plugin
=================================================

Basic plugin for displaying the weather

 “Powered by Dark Sky” - https://darksky.net/poweredby/.
"""
import asyncio
import datetime
import re

from forcastiopy import *
#figure out why it doesn't work unless it's imported this way

import geocoder
from time import strftime

import irc3
from irc3.plugins.command import command


@irc3.plugin
class WeatherPlugin(object):
    """Plugin to provide:

    * Weather Plugin
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
        try:
            self.fio = ForecastIO.ForecastIO(self.config['api_key'])
        except ValueError:
            raise Exception(
            "You need to set a Dark Sky api_key "
            "in the config section [{}]".format(__name__))

    @command
    def sunrise(self, mask, target, args):
        """Gives the time the sun will rise

            %%sunrise [<location>]...
        """
        if target == self.bot.nick:
            target = mask.nick

        @asyncio.coroutine
        def wrap():
            response = yield from self.sunrise_response(mask, args)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

#TODO
#when args are provided needs to be parsed to get the lat and long values
#so far only works if latlong for a user exist
#also how useful is getting the sunrise time?

    @asyncio.coroutine
    def sunrise_response(self, mask, args):
        """Returns appropriate reponse to sunrise request"""
        local = args['<location>']
        if not local:
            try:
                location = yield from self.get_local(mask.nick)
            except KeyError:
                response = "I don't have a location set for you."
                return response
        try:
            self.fio.get_forecast(location[0], location[1])

        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException,
                KeyError, HTTPError)as e:
            errmsg = str(e)
            return errmsg

        daily = FIODaily.FIODaily(self.fio)
        sunrise daily.get_day(1)["sunriseTime"]
        time = datetime.datetime.fromtimestamp(int(sunrise)).strftime("%I:%M %p (%m/%d/%y)")
        response = 'The next sunrise for you is at: {0}'.format(time)
        return response

# Set the api key using the system's environmental variables.
# $ export GOOGLE_API_KEY=<Secret API Key>
    @command
    def setlocal(self, mask, target, args):
        """Sets the longitude and latitude of the user

            %%setlocal <location>...
        """
        location = ' '.join(args['<location>'])
        g = geocoder.google(location)
        self.log.info("Storing location %s for %s", location, mask.nick)
        self.bot.get_user(mask.nick).set_setting('latlong', g.latlng)
        self.bot.privmsg(target, "Got it.")

    @asyncio.coroutine
    def get_local(self, nick):
        """Gets the location associated with a user from the database"""
        user = self.bot.get_user(nick)
        if user:
            result = yield from user.get_setting('latlong', nick)
            return result
        else:
            raise KeyError
