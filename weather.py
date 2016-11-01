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

import geocoder
import requests
from darksky import DarkSky
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
            self.api_key = self.config['api_key']
        except KeyError:
            raise Exception(
                "You need to set the DarkSky.net api_key"
                "in the config section [{}]".format(__name__))

    @command
    def w(self, mask, target, args):
        """Gives the time the sun will rise

            %%w [<location>]...
        """
        if target == self.bot.nick:
            target = mask.nick

        @asyncio.coroutine
        def wrap():
            response = yield from self.w_response(mask, args)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

# TODO
# Still not correctly working when no args are given.
    @asyncio.coroutine
    def w_response(self, mask, args):
        """Returns appropriate reponse to w request"""
        local = args['<location>']
        location = yield from self.get_local(mask.nick)

        if not local and location is None:
            response = "I don't remember where you are"
            return response
        elif local:  # if both values exist, args take priority
            self.set_local(mask.nick, args)
            g = geocoder.google(' '.join(local))
            location = g.latlng
            if not location:
                response = "Sorry, I can't seem to find that place."
                return response
        try:
            self.ds = DarkSky(location)
        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
                ValueError, KeyError)as e:
            errmsg = str(e)
            return errmsg

        summary = self.ds.forecast.currently.summary
        temp = self.ds.forecast.currently.temperature

# maybe it would be nice if the city name was stored too?
        p = geocoder.google(str(location), method="reverse")
        if (p.city, p.state):
            place = "{0}, {1}".format(p.city, p.state)
        else:
            place = p.country

        if self.ds.forecast.flags.units == "us":
            deg = "F"
        else:
            deg = "C"
        response = "{0} - {1}, {2}\u00B0{3}".format(
            place, summary, temperature, deg)
        return response

# Set the api key using the system's environmental variables.
# $ export GOOGLE_API_KEY=<Secret API Key>
    def set_local(self, mask, args):
        """Sets the longitude and latitude of the user
        """
        location = ' '.join(args['<location>'])
        g = geocoder.google(location)

        self.log.info("Storing location %s for %s", location, mask.nick)
        self.bot.get_user(mask.nick).set_setting('latlong', g.latlng)
        self.bot.privmsg(target, "Got it.")

    @asyncio.coroutine
    def get_local(self, nick):
        """Gets the location associated with a user from the database.
        If user is not in the database, returns None.
        """
        user = self.bot.get_user(nick)
        result = yield from user.get_setting('latlong', nick)
        return result


def _unixformat(unixtime,d=False):
    """Turns Unix Time into something readable

    "9:34 PM (08/24/16)"
    """
    time = datetime.datetime.fromtimestamp(
        int(unixtime)).strftime("%I:%M %p")

    date = datetime.datetime.fromtimestamp(
        int(unixtime)).strftime(" (%m/%d/%y)")
    if d:
        return time + date
    else:
        return time
