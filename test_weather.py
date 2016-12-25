# -*- coding; utf-8 -*-
from __future__ import unicode_literals, print_function

import asyncio
import json
import os.path
import unitest

from irc3.testing import BotTestCase, patch, MagicMock
from irc3.utils import Irc3String


def _get_fixture(fixture_name):
    """Reads a fixture from a file"""
    with open(os.path.join(os.path.dirname(__file__),
        'fixtures/{}'.format(fixture_name)), 'r') as f:
        return json.load(f)

class WeatherPluginTest(BotTestCase):
    """Test for Weather Plugin."""

    config = {
        'includes': ['weather'],
        'weather': {'api_key': ''},
        'cmd': '!'
    }

    def test_get_local_from_database(self):
    mock = MagicMock()
    # mock get_setting
    @asyncio.coroutine
    def mock_get_setting(setting, default):
        assert setting == 'weatheruser'
        assert default == 'nick'
        return 'lastfmuser'
    mock.get_setting = mock_get_setting
    # we need to have a mock return the mocked user with get_setting
    mock_user = MagicMock(name='MockGetUser', return_value=mock)
    self.callFTU()
    self.bot.get_user = mock_user
    weather = self.bot.get_plugin('onebot.plugins.weather.WeatherPlugin')

    def wrap():
        lastfmnick = yield from weather.get_local('nick')
        assert lastfmnick == 'lastfmuser'
    self.bot.loop.run_until_complete(wrap())
