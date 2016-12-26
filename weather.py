# -*- coding: utf-8 -*-
"""
=================================================
:mod:`onebot.plugins.weather` Weather plugin
=================================================

Basic plugin for displaying the weather

 “Powered by Dark Sky” - https://darksky.net/poweredby/.
"""
import asyncio

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
        """
        Weather - Reports the current weather for a given location.
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
        """
        Returns appropriate reponse to .w request
        example: <bot> New York, NY - Clear, 75.4°F
        """
        local = " ".join(args['<location>'])
        if not local:
            location = yield from self.get_local(mask.nick)
            if not location:
                response = "Sorry, I don't remember where you are"
                return response
        else:
            try:
                location = yield from self.get_geo(mask.nick, args)
            except ConnectionError:
                response = "Sorry, I could't find that place"
                return response
            # if args are provided remember them
            self.set_local(mask.nick, location)

        latlng, place = location
        try:
            self.ds = DarkSky(latlng, key=self.api_key)
        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException,
                requests.exceptions.HTTPError,
                ValueError, KeyError) as e:
            errmsg = str(e)
            return errmsg

        current = self.ds.forecast.currently
        time = _unixformat(current.time, self.ds.forecast.timezone)
        deg = "F" if self.ds.forecast.flags.units == "us" else "C"

        response = "\x02{0} \x0F({4}) - {1}, {2}\u00B0{3}".format(
            place, current.summary, current.temperature, deg, time)
        return response

# Set the api key using the system's environmental variables.
# $ export GOOGLE_API_KEY=<Secret API Key>
    @asyncio.coroutine
    def get_geo(self, nick, args):
        """Gets geocoding information from Google returns ['lat','lng']
            and "city", raises ConnectionError on bad results
        """
        location = " ".join(args['<location>'])
        geo = geocoder.google(location)
        if geo.status == "OK":
            if (geo.city, geo.state):
                place = "{0}, {1}".format(geo.city, geo.state)
            else:
                place = geo.country
            return (geo.latlng, place)
        else:
            self.log.info("Geocode error: {0} - {1}".format(nick, geo.status))
            raise ConnectionError

    @asyncio.coroutine
    def get_local(self, nick):
        """Gets the location, in the form of latitude and longitude,
        associated with a user from the database.
        """
        user = self.bot.get_user(nick)
        result = yield from user.get_setting('userloc', None)
        return result

    def set_local(self, nick, location):
        """
        Sets the location of the user ([longitude, latitude], "city")
        """
        self.log.info("Storing local {0} for {1}".format(location, nick))
        self.bot.get_user(nick).set_setting('userloc', location)

    @classmethod
    def reload(cls, old):
        return cls(old.bot)


def _unixformat(uxtime, tz):
    """
    Handles time zone conversions
    and converts unix time into readable format

    example: "9:34PM GMT"
    """
    tzlocal = timezone(tz)
    time = datetime.fromtimestamp(int(uxtime), tz=tzlocal)
    return "{:%I:%M%p %Z}".format(time)
