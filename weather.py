# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.weather` Weather plugin
=================================================

Basic plugin for displaying the weather

 “Powered by Dark Sky” - https://darksky.net/poweredby/.
"""
import asyncio
import re

import geocoder
import requests
from darksky import DarkSky
from datetime import datetime
from pytz import timezone

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
        """Gives some basic current weather information for the user
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

    @asyncio.coroutine
    def w_response(self, mask, args):
        """Returns appropriate reponse to w request"""
        local = args['<location>']
        location = yield from self.get_local(mask.nick)

        if not local and not location:
            response = "Sorry, I don't remember where you are"
            return response

        if local:
            try:
                geo = yield from self.get_geo(mask.nick, args)
            except ConnectionError as status:
                response = "Sorry, I could't find that place - " + str(status)
                return response
            # if args are provided remember them
            self.set_local(mask.nick, geo)
            location = yield from self.get_local(mask.nick)

        try:
            self.ds = DarkSky(location[:2], key=self.api_key)
        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
                ValueError, KeyError)as e:
            errmsg = str(e)
            return errmsg

        summary = self.ds.forecast.currently.summary
        temp = self.ds.forecast.currently.temperature
        if self.ds.forecast.flags.units == "us":
            deg = "F"
        else:
            deg = "C"
        response = "{0} - {1}, {2}\u00B0{3}".format(
            location[2], summary, temperature, deg)
        return response

# Set the api key using the system's environmental variables.
# $ export GOOGLE_API_KEY=<Secret API Key>
    @asyncio.coroutine
    def get_geo(self, mask, args):
    """Gets geocoding information from Google

        returns Geocoder class, raises ConnectionError on bad results
    """
        location = ' '.join(args['<location>'])
        geo = geocoder.google(location)

        if geo.status == "OK":
            return geo
        else:
            self.log.info(
                "Google Geocode error for {0} - {1}".format(mask.nick, geo.status))
            raise ConnectionError(geo.status)

    def set_local(self, mask, geo):
        """Sets the location of the user a list of [longitude, latitude,"city"]
        """
        location = geo.latlng

        if (geo.city, geo.state):
            location.append("{0}, {1}".format(p.city, p.state))
        else:
            location.append(geo.country)

        self.log.info("Storing local {0} for {1}".format(location, mask.nick))
        self.bot.get_user(mask.nick).set_setting('userloc', location)
        #self.bot.privmsg(target, "Got it.")

    @asyncio.coroutine
    def get_local(self, nick):
        """Gets the location, in the form of latitude and longitude,
        associated with a user from the database.
        If user is not in the database, returns None.
        """
        user = self.bot.get_user(nick)
        result = yield from user.get_setting('userloc', nick)
        return result

# NOTE not currently being used


def _unixformat(uxtime, tz, Date=False):
    """Handles time zone conversions
        and converts unix time into readable format

        example: "9:34 PM GMT (08/24/16)"
    """
    tzlocal = timezone(tz)

    fmt = "%I:%M %p %Z"
    if Date:
        fmt += " (%m/%d/%y)"

    time = datetime.fromtimestamp(int(uxtime), tz=tzlocal)
    return time.strftime(fmt)
