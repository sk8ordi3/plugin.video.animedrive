# -*- coding: utf-8 -*-

'''
    Animedrive Add-on
    Copyright (C) 2020 heg, vargalex

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

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?', '')))

action = params.get('action')
url = params.get('url')
episode_name = params.get('episode_name')
img = params.get('img')
descr = params.get('descr')
title = params.get('title')

if action is None:
    navigator.navigator().root()
    
elif action == 'categories':
    navigator.navigator().getCategories()    

elif action == 'only_movies':
    navigator.navigator().getOnlyMovies()

elif action == 'only_series':
    navigator.navigator().getOnlySeries()

elif action == 'items':
    navigator.navigator().getItems(url, title, img, descr)

elif action == 'search':
    navigator.navigator().getSearches()

elif action == 'movie_items':
    navigator.navigator().getMovieItems(url, title, img, descr)

elif action == 'series_items':
    navigator.navigator().getSeriesItems(url, img, descr)

elif action == 'get_movie_sources':
    navigator.navigator().getMovieSources(url, title, img, descr)

elif action == 'get_series_sources':
    navigator.navigator().getSeriesSources(url, episode_name, img, descr, title)
    
elif action == 'episodes':
    navigator.navigator().getEpisodes(url, episode_name, img, descr, title)

elif action == 'playmovie':
    navigator.navigator().playMovie(url)

elif action == 'newsearch':
    navigator.navigator().doSearch()

elif action == 'deletesearchhistory':
    navigator.navigator().deleteSearchHistory() 