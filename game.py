# -*- coding: utf-8 -*-

"""
=================================================
:mod:`onebot.plugins.videogames` Weather plugin
=================================================

Plugin for searching information on video games.

All information resourced from https://www.giantbomb.com/api/
"""
import asyncio
import requests
from attrdict import AttrDict
from time import strftime, strptime

import irc3
from irc3.plugins.command import command


@irc3.plugin
class VideoGamePlugin(object):
    """Plugin to provide:

        * Video Game Plugin

        Configuration settings:
                - ``api_key``: API key for GiantBomb.com
        """

    requires = [
        'irc3.plugins.command',
    ]

    def __init__(self, bot):
        """Initialize the plugin"""
        self.bot = bot
        self.log = bot.log.getChild(__name__)
        self.config = bot.config.get(__name__, {})
        if self.config['ignored_channels']:
            self.ignored_channels = self.config.get('ignored_channels', [])
        try:
            self.api_key = self.config['api_key']
        except KeyError:
            raise Exception(
                "You need to set an api_key for GiantBomb.com in the config"
                "section [{}]".format(__name__))

    @command
    def vg(self, mask, target, args):
        """
        Video Game Information - Seach for a video game by name.
        Returns relevant information

        %%vg <game>...

        """
        if (mask.nick == self.bot.nick or target in self.ignored_channels):
            return

        if target == self.bot.nick:
            target = mask.nick

        @asyncio.coroutine
        def wrap():
            response = yield from self.vg_response(mask, args)
            self.log.info(response)
            self.log.debug(response)
            self.bot.privmsg(target, response)
        asyncio.async(wrap())

    @asyncio.coroutine
    def vg_response(self, mask, args):
        """Forms the appropriate reponse to .vg request"""

        videogame = " ".join(args['<game>'])

        try:
            game = yield from self.giantbomb_api(videogame)
        except IndexError:
            message = "I didn't find anything on that game."
            return message
        except:
            message = "Something went wrong"
            return message

        # Build the response
        response = {}
        response['name'] = game.name
        response['url'] = game.site_detail_url

        # A game will either have an original_release_date or an expected one
        if (game.expected_release_day or game.expected_release_month or
                game.expected_release_year):
            # list should be [year, month, day], can be None
            expected_release_date = _datetime_parser(
                [game.expected_release_year, game.expected_release_month,
                 game.expected_release_day])

            response['release date'] = 'releases: ' + expected_release_date

        else:
            # Could be None?
            dt = strptime(game.original_release_date, "%Y-%m-%d %H:%M:%S")
            response['release date'] = 'released: ' + strftime('%b %d, %Y', dt)

        # Platforms

        if game.platforms:
            response['platforms'] = list(platform.abreviation for platform in game.platforms)
            del response['platforms'][4:]

            ignore = ['LIN', 'ANDR', 'FIRE', 'PSNV', '3DSE',
                      'BROW', 'IPHN', 'IPAD', 'XBGS', 'OUYA', 'WSHP']

            #removes any ignored platforms
            response['platforms'] = ",".join(
                [x for x in response['platforms'] if x not in ignore])

        # Developers
        response['developers'] = _response_parser(game['developers'], 'name')
        del response['developers'][2:]
        response['developers'] = ", ".join(response['developers'])

        # Publishers
        response['publishers'] = _response_parser(game['publishers'], 'name')
        del response['publishers'][2:]
        response['publishers'] = ", ".join(response['publishers'])

        # Format the message
        message = "\x02{name}\x0F".format(**response)
        if response['platforms']:
            message += " ({platforms})".format(**response)
        if response['developers'] and response['publishers']:
            message += " - {developers}/{publishers}".format(**response)
        elif response['developers']:
            message += " - {developers}".format(**response)
        elif response['publishers']:
            message += " - {publishers}".format(**response)
        if response['release date']:
            message += "\x1D {release date}\x0F".format(**response)
        if response['url']:
            message += " - {url}".format(**response)
        return message

    @asyncio.coroutine
    def giantbomb_api(self, game):
        """Deals with the giantbomb api
                note: The api can be really slow, >10sec
        """
        base_url = "https://www.giantbomb.com/api/"

        # First search for the game to find the game_id
        search_params = {"api_key": self.api_key,
                         "format": "json",
                         "field_list": "id",
                         "resources": "game",
                         "limit": "1",
                         "query": game
                         }

        search_url = base_url + "search/"
        try:
            sr = yield from self.giantbomb_get(search_url, search_params)
        except Exception as err:
            self.log.info(err)
            raise
        try:
            # Extract Game ID
            game_id = "3030-" + str(sr['results'][0]['id'])
        except IndexError:
            raise

        # Request information on that game
        field_list = ["id", "name", "platforms", "site_detail_url",
                      "publishers",
                      "developers", "original_release_date",
                      "expected_release_day", "expected_release_month",
                      "expected_release_year"
                      ]

        game_params = {"api_key": self.api_key,
                       "format": "json",
                       "field_list": ",".join(field_list)}

        game_url = base_url + "game/" + game_id
        gr = yield from self.giantbomb_get(game_url, game_params)
        game_result = AttrDict(gr)
        return game_result.results

    @asyncio.coroutine
    def giantbomb_get(self, url, params):
        # Requires unique user-agent
        headers = {'User-Agent': 'Onebot Python-requests/2.13.0'}
        r = requests.get(url, headers=headers, params=params)
        response = r.json()
        return response

    @classmethod
    def reload(cls, old):
        return cls(old.bot)


def _response_parser(atr, k):
    if atr: response = list((value[k] for value in atr))

    del response[k][2:]
     = ", ".join(response[k])


def _datetime_parser(in_date):
    """Makes the time useable"""
    _f = ["%Y", "%b", "%d"]  # [year, month, day]

    fmt = [_f[idx] for idx, val in enumerate(in_date) if val]
    fmt.reverse()

    # convert None to 0 so strftime will ignore it
    date = [0 if t is None else t for t in in_date]
    date.extend([0] * 6)
    response = strftime(' '.join(fmt), tuple(date))
    return response
