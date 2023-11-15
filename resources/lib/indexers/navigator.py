# -*- coding: utf-8 -*-

'''
    Animedrive Addon
    Copyright (C) 2023 heg, vargalex

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

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, locale, base64
from bs4 import BeautifulSoup
import requests
import urllib.parse
from resources.lib.modules.utils import py2_decode, py2_encode
import html

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://animedrive.hu'

headers = {
    'authority': 'player.animedrive.hu',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'referer': 'https://animedrive.hu/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        self.addDirectoryItem("Filmek", "only_movies", '', 'DefaultFolder.png')
        self.addDirectoryItem("Sorozatok", "only_series", '', 'DefaultFolder.png')
        self.addDirectoryItem("Kategóriák", "categories", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", "search", '', 'DefaultFolder.png')
        self.endDirectory()
        
    def getCategories(self):
        page = requests.get(f"{base_url}/search/")
        soup = BeautifulSoup(page.text, 'html.parser')

        div_element = soup.find('div', class_='kereso-reszletes-mufaj-mufajok')
        genres = [span.text for span in div_element.find_all('span')]

        for category in genres:
            enc_value = urllib.parse.quote(category, safe=':/')
            enc_link = f'{base_url}/search/?tag={enc_value}'

            self.addDirectoryItem(f"{category}", f'items&url={enc_link}', '', 'DefaultFolder.png')

        self.endDirectory()        

    def getItems(self, url, title, img, descr):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        cards = soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-xl-2')
        
        for card in cards:
            if "TERVEZETT" not in card.text and "HAMAROSAN" not in card.text:
                title = card.find('h3', class_='card__title').text.strip()
                link = card.find('a', class_='nk-image-box-link')['href']
                img = card.find('img')['src']
                date = card.find('span', class_='card__category').find('a').text.strip()

                resp2 = requests.get(link, headers=headers).text
                soup_2 = BeautifulSoup(resp2, 'html.parser')
                
                parent_div = soup_2.find('div', class_='nk-image-box-1-a')
                megtekintes_link_tag = parent_div.find('a', {'aria-label': 'LINK'})
                if megtekintes_link_tag:
                    megtekintes_link = megtekintes_link_tag.get('href')
        
                    descr = soup_2.find('p', class_='col-12').text
                    left_table_rows = soup_2.select('.animeSpecs.left tr')
                    left_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in left_table_rows]}
                    megtekintes = left_table_data.get('megtekintés:')
                    
                    tipus = left_table_data.get('típus:')
                    
                    if tipus == 'Film':
                        tipus = f'{tipus:^10}'
                    
                    kiadas = left_table_data.get('kiadás:')
                    statusz = left_table_data.get('státusz:')

                    right_table_rows = soup_2.select('.animeSpecs.right tr')
                    right_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in right_table_rows]}
                    reszek = right_table_data.get('részek:')

                if tipus == 'Sorozat':
                    self.addDirectoryItem(f'{tipus} | [B]{title} - [COLOR red]({reszek})[/COLOR] - {date}[/B]', f'get_series_sources&url={megtekintes_link}&title={title}&img={img}&descr={descr}', img, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': descr})
                elif tipus:
                    self.addDirectoryItem(f'{tipus} | [B]{title} - {date}[/B]', f'get_movie_sources&url={megtekintes_link}&title={title}&img={img}&descr={descr}', img, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': descr})
            
        try:
            active_page = soup.find('a', class_='nk-pagination-current-white')
            next_page = active_page.find_next('a')['href']

            next_page_link = f'{base_url}/search/{next_page}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Animedrive | getItems | next_page_link | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def getOnlyMovies(self):
        page = requests.get(f"{base_url}/search/?q=&type=film&sort=ujak", headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        cards = soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-xl-2')
        
        for card in cards:
            if "TERVEZETT" not in card.text and "HAMAROSAN" not in card.text:
                title = card.find('h3', class_='card__title').text.strip()
                link = card.find('a', class_='nk-image-box-link')['href']
                img = card.find('img')['src']
                date = card.find('span', class_='card__category').find('a').text.strip()

                resp2 = requests.get(link, headers=headers).text
                soup_2 = BeautifulSoup(resp2, 'html.parser')
                
                parent_div = soup_2.find('div', class_='nk-image-box-1-a')
                megtekintes_link_tag = parent_div.find('a', {'aria-label': 'LINK'})
                if megtekintes_link_tag:
                    megtekintes_link = megtekintes_link_tag.get('href')
        
                    descr = soup_2.find('p', class_='col-12').text
        
                    left_table_rows = soup_2.select('.animeSpecs.left tr')
                    left_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in left_table_rows]}
                    megtekintes = left_table_data.get('megtekintés:')
                    tipus = left_table_data.get('típus:')
                    kiadas = left_table_data.get('kiadás:')
                    statusz = left_table_data.get('státusz:')

                    right_table_rows = soup_2.select('.animeSpecs.right tr')
                    right_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in right_table_rows]}
                    reszek = right_table_data.get('részek:')

                    self.addDirectoryItem(f'[B]{title} - {date}[/B]', f'get_movie_sources&url={quote_plus(megtekintes_link)}&title={title}&img={img}&descr={descr}', img, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': descr})
        
        try:
            next_page = soup.find('a', class_='nk-pagination-next')['href']
            next_page_link = f'{base_url}/search/{next_page}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Animedrive | getOnlyMovies | next_page | csak egy oldal található', xbmc.LOGINFO)
        
        
        self.endDirectory('movies')

    def getOnlySeries(self):
        page = requests.get(f"{base_url}/search/?q=&type=sorozat&sort=ujak", headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')

        cards = soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-xl-2')
        
        for card in cards:
            if "TERVEZETT" not in card.text and "HAMAROSAN" not in card.text:
                title = card.find('h3', class_='card__title').text.strip()
                link = card.find('a', class_='nk-image-box-link')['href']
                image_src = card.find('img')['src']
                date = card.find('span', class_='card__category').find('a').text.strip()

                resp2 = requests.get(link, headers=headers).text
                soup_2 = BeautifulSoup(resp2, 'html.parser')
                
                parent_div = soup_2.find('div', class_='nk-image-box-1-a')
                megtekintes_link_tag = parent_div.find('a', {'aria-label': 'LINK'})
                if megtekintes_link_tag:
                    megtekintes_link = megtekintes_link_tag.get('href')

                    description = soup_2.find('p', class_='col-12').text

                    left_table_rows = soup_2.select('.animeSpecs.left tr')
                    left_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in left_table_rows]}
                    megtekintes = left_table_data.get('megtekintés:')
                    tipus = left_table_data.get('típus:')
                    kiadas = left_table_data.get('kiadás:')
                    statusz = left_table_data.get('státusz:')

                    right_table_rows = soup_2.select('.animeSpecs.right tr')
                    right_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in right_table_rows]}
                    reszek = right_table_data.get('részek:')

                    self.addDirectoryItem(f'[B]{title} - [COLOR red]({reszek})[/COLOR] - {date}[/B]', f'get_series_sources&url={quote_plus(megtekintes_link)}&img={image_src}&descr={description}&title={title}', image_src, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': description})
        
        try:
            next_page = soup.find('a', class_='nk-pagination-next')['href']
            next_page_link = f'{base_url}/search/{next_page}'
            
            self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Animedrive | getOnlySeries | next_page | csak egy oldal található', xbmc.LOGINFO)
        
        
        self.endDirectory('series')       

    def getMovieItems(self, url, title, img, descr):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        cards = soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-xl-2')
        
        for card in cards:
            if "TERVEZETT" not in card.text and "HAMAROSAN" not in card.text:
                title = card.find('h3', class_='card__title').text.strip()
                link = card.find('a', class_='nk-image-box-link')['href']
                img = card.find('img')['src']
                date = card.find('span', class_='card__category').find('a').text.strip()
                
                #sec_requ
                resp2 = requests.get(link, headers=headers).text
                soup_2 = BeautifulSoup(resp2, 'html.parser')
                
                parent_div = soup_2.find('div', class_='nk-image-box-1-a')
                megtekintes_link_tag = parent_div.find('a', {'aria-label': 'LINK'})
                if megtekintes_link_tag:
                    megtekintes_link = megtekintes_link_tag.get('href')
        
                    descr = soup_2.find('p', class_='col-12').text
        
                    left_table_rows = soup_2.select('.animeSpecs.left tr')
                    left_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in left_table_rows]}
                    megtekintes = left_table_data.get('megtekintés:')
                    tipus = left_table_data.get('típus:')
                    kiadas = left_table_data.get('kiadás:')
                    statusz = left_table_data.get('státusz:')

                    right_table_rows = soup_2.select('.animeSpecs.right tr')
                    right_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in right_table_rows]}
                    reszek = right_table_data.get('részek:')     

                    self.addDirectoryItem(f'[B]{title} - {date}[/B]', f'get_movie_sources&url={quote_plus(megtekintes_link)}&title={title}&img={img}&descr={descr}', img, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': descr})

        try:
            next_page = soup.find('a', class_='nk-pagination-next')['href']
            next_page_link = f'{base_url}/search/{next_page}'

            self.addDirectoryItem('[I]Következő oldal[/I]', f'movie_items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Animedrive | getOnlyMovies | next_page | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def getSeriesItems(self, url, img, descr):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        cards = soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-xl-2')
        
        for card in cards:
            if "TERVEZETT" not in card.text and "HAMAROSAN" not in card.text:
                title = card.find('h3', class_='card__title').text.strip()
                link = card.find('a', class_='nk-image-box-link')['href']
                img = card.find('img')['src']
                date = card.find('span', class_='card__category').find('a').text.strip()
                
                #sec_requ
                resp2 = requests.get(link, headers=headers).text
                soup_2 = BeautifulSoup(resp2, 'html.parser')
                
                parent_div = soup_2.find('div', class_='nk-image-box-1-a')
                megtekintes_link_tag = parent_div.find('a', {'aria-label': 'LINK'})
                if megtekintes_link_tag:
                    megtekintes_link = megtekintes_link_tag.get('href')
        
                    descr = soup_2.find('p', class_='col-12').text
        
                    left_table_rows = soup_2.select('.animeSpecs.left tr')
                    left_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in left_table_rows]}
                    megtekintes = left_table_data.get('megtekintés:')
                    tipus = left_table_data.get('típus:')
                    kiadas = left_table_data.get('kiadás:')
                    statusz = left_table_data.get('státusz:')

                    right_table_rows = soup_2.select('.animeSpecs.right tr')
                    right_table_data = {td[0].text.strip().lower(): td[1].text.strip() for td in [row.find_all('td') for row in right_table_rows]}
                    reszek = right_table_data.get('részek:')

                    self.addDirectoryItem(f'[B]{title} - [COLOR red]({reszek})[/COLOR] - {date}[/B]', f'get_series_sources&url={quote_plus(megtekintes_link)}&img={img}&descr={descr}&title={title}', img, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': descr})
        
        try:
            next_page = soup.find('a', class_='nk-pagination-next')['href']
            next_page_link = f'{base_url}/search/{next_page}'

            self.addDirectoryItem('[I]Következő oldal[/I]', f'series_items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except AttributeError:
            xbmc.log(f'Animedrive | getSeriesItems | next_page | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('series')

    def getMovieSources(self, url, title, img, descr):
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        iframe_tag = soup.find('iframe')
        if iframe_tag:
            embed_src = iframe_tag.get('src')
        
            page_2 = requests.get(embed_src, headers=headers)
            soup_2 = BeautifulSoup(page_2.text, 'html.parser')
            
            import re
            
            pattern = re.compile(r"src: '(.*?)', type: 'video/mp4', size: (\d+),")
            matches = pattern.findall(str(soup_2))
            video_sources = [{'url': match[0], 'size': int(match[1])} for match in matches]

        try:
            max_size_source = max(video_sources, key=lambda x: x['size'])

            highest_link = max_size_source['url']
            highest_size = max_size_source['size']

            highest_link_string = f"Highest Link: {highest_link}"
            highest_size_string = f"Highest Size: {highest_size}p"
            
            self.addDirectoryItem(f'[B]{highest_size}p - {title}[/B]', f'playmovie&url={quote_plus(highest_link)}&title={title}&img={img}&descr={descr}', img, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': descr})            
        except (ValueError, UnboundLocalError):
            xbmc.log(f'Animedrive | getSeriesSources | name: No video sources found', xbmc.LOGINFO)
            notification = xbmcgui.Dialog()
            notification.notification("Animedrive", "Törölt tartalom", time=5000)
        
        self.endDirectory('movies')

    def getSeriesSources(self, url, episode_name, img, descr, title):
        import re
        
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        try:
            episode_links = soup.find('div', class_='episodes').find_all('a', class_='episode-item') 
            if episode_links:
            
                for link in episode_links:
                    episode_name = link.get_text(strip=True)
                    episode_href = link['href']
                    
                    resz_link = f'{base_url}/watch/{episode_href}'
                
                    try:
                        self.addDirectoryItem(f'[B]{episode_name} - {title}[/B]', f'episodes&url={resz_link}&episode_name={episode_name}&img={img}&descr={descr}&title={title}', img, 'DefaultMovies.png', isFolder=True, meta={'title': episode_name, 'plot': descr})
                    except UnboundLocalError:
                        notification = xbmcgui.Dialog()
                        notification.notification("Animedrive", "Törölt tartalom", time=5000)
                        xbmc.log(f'Animedrive | getSeriesSources | name: No video sources found', xbmc.LOGINFO)

        except AttributeError: #ha a sorozatban csak egy rész van 1/1
            try:
                episode_links = soup.find('iframe')['src']
                if episode_links:
                    resz = re.findall(r'(\?id=.*)', episode_links)[0].strip()
                    resz_link = f'{base_url}/watch/{resz}'
                    get_title_text = soup.title.text
                    title_parts = [part.strip() for part in get_title_text.split('|')]
                    episode_name = ' '.join(title_parts[2:]).strip()
                    
                    try:
                        title = ' '
                        
                        self.addDirectoryItem(f'[B]{episode_name}[/B]', f'episodes&url={resz_link}&episode_name={episode_name}&img={img}&descr={descr}&title={title}', img, 'DefaultMovies.png', isFolder=True, meta={'title': episode_name, 'plot': descr})
                    except UnboundLocalError:
                        notification = xbmcgui.Dialog()
                        notification.notification("Animedrive", "Törölt tartalom", time=5000)
                        xbmc.log(f'Animedrive | getSeriesSources | name: No video sources found', xbmc.LOGINFO)
            except TypeError:
                notification = xbmcgui.Dialog()
                notification.notification("Animedrive", "Törölt tartalom", time=5000)
                xbmc.log(f'Animedrive | getSeriesSources | name: No video sources found', xbmc.LOGINFO)            

        self.endDirectory('series')

    def getEpisodes(self, url, episode_name, img, descr, title):
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        iframe_tag = soup.find('iframe')
        if iframe_tag:
            embed_src = iframe_tag.get('src')
        
            page_2 = requests.get(embed_src, headers=headers)
            soup_2 = BeautifulSoup(page_2.text, 'html.parser')
            
            import re
            
            pattern = re.compile(r"src: '(.*?)', type: 'video/mp4', size: (\d+),")
            matches = pattern.findall(str(soup_2))
            video_sources = [{'url': match[0], 'size': int(match[1])} for match in matches]

        try:
            max_size_source = max(video_sources, key=lambda x: x['size'])

            highest_link = max_size_source['url']
            highest_size = max_size_source['size']

            highest_link_string = f"Highest Link: {highest_link}"
            highest_size_string = f"Highest Size: {highest_size}p"
            
            self.addDirectoryItem(f'[B]{highest_size}p - {episode_name} - {title}[/B]', f'playmovie&url={quote_plus(highest_link)}&episode_name={episode_name}&img={img}&descr={descr}&title={title}', img, 'DefaultMovies.png', isFolder=False, meta={'title': episode_name, 'plot': descr})            
        except (ValueError, UnboundLocalError):
            xbmc.log(f'Animedrive | getEpisodes | name: No video sources found', xbmc.LOGINFO)
            notification = xbmcgui.Dialog()
            notification.notification("Animedrive", "Törölt tartalom", time=5000)

        self.endDirectory('episodes')

    def playMovie(self, url):
        xbmc.log(f'Animedrive | playMovie | playing URL: {url}', xbmc.LOGINFO)

        play_item = xbmcgui.ListItem(path=url)
        play_item.setProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=play_item)

    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                url_p = f"{base_url}/search/?q={item}&sort=ujak"
                enc_url = quote_plus(url_p)                
                self.addDirectoryItem(item, f'items&url={url_p}', '', 'DefaultFolder.png')

            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory()

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write(f"{search_text}\n")
            file.close()
            url = f"{base_url}/search/?q={search_text}&sort=ujak"
            self.getItems(url, None, 1, None)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)