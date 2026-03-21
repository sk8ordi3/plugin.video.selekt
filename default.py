# -*- coding: utf-8 -*-
'''
    SELEKT Add-on
    Copyright (C) 2026 heg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import sys
from resources.lib.indexers import navigator
from urllib.parse import parse_qsl, unquote_plus

params = dict(parse_qsl(sys.argv[2].replace('?', '')))
action = params.get('action')
url = params.get('url')
section = params.get('section')
page = params.get('page', '1')

nav = navigator.navigator()

if action is None:
    nav.root()
elif action == 'get_sections':
    nav.get_sections(unquote_plus(url))
elif action == 'get_section_items':
    nav.get_section_items(unquote_plus(url), unquote_plus(section), page)
elif action == 'get_items':
    url_decoded = unquote_plus(url)
    if '/series/' in url_decoded or '/magazin/' in url_decoded:
        nav.extraSeries(url_decoded)
    elif '/movies/' in url_decoded:
        nav.extraMovies(url_decoded)
elif action == 'player_link_handler':
    nav.player_link_handler(unquote_plus(url))
elif action == 'playmovie':
    nav.playMovie(unquote_plus(url))