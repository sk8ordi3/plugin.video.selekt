# -*- coding: utf-8 -*-
'''
    SELEKT Addon
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
import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, time, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, quote, unquote, quote_plus
from xbmcvfs import translatePath
from resources.lib.indexers import auth
import hashlib

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addon = xbmcaddon.Addon('plugin.video.selekt')
addonIcon = addon.getAddonInfo('icon')
addonFanart = addon.getAddonInfo('fanart')

PROFILE_DIR = translatePath(addon.getAddonInfo('profile'))
CACHE_DIR = os.path.join(PROFILE_DIR, 'cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

base_url = 'https://hu.selekt.tv'

custom_view_list = addon.getSetting('custom_view_list')
fixed_wide_view = 'series'
user_change_view = 'movies'

CACHE_TIME = 10800

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"SELEKT NAVIGATOR: {msg}", level)

class navigator:
    def __init__(self):
        pass

    def _check_credentials(self):
        username = addon.getSetting('username')
        password = addon.getSetting('password')
        if not username or not password:
            xbmcgui.Dialog().notification('SELEKT', 'Add meg a bejelentkezési adataidat!', xbmcgui.NOTIFICATION_WARNING)
            addon.openSettings()
            return False
        return True

    def root(self):
        if not self._check_credentials(): return
        self.addDirectoryItem("Főoldal", f"get_sections&url={quote_plus(base_url)}", '', addonIcon)
        
        self.addDirectoryItem("AMC", f"get_sections&url={quote_plus(base_url + '/amc')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/584698166088/AMC_Hub_Icon.png')
        self.addDirectoryItem("Sport", f"get_sections&url={quote_plus(base_url + '/sport')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/603597188885/STV_Hub_Icon.png')
        self.addDirectoryItem("Sport 3", f"get_sections&url={quote_plus(base_url + '/sport3')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/42861345143/SP3_Hub_Icon.png')
        self.addDirectoryItem("Spektrum", f"get_sections&url={quote_plus(base_url + '/spektrum')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/453311668916/SPK_Hub_Icon.png')
        self.addDirectoryItem("Spektrum Home", f"get_sections&url={quote_plus(base_url + '/spektrum-home')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/511042593119/SPH_Hub_Icon.png')
        self.addDirectoryItem("TV Paprika", f"get_sections&url={quote_plus(base_url + '/tv-paprika')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/186546665206/TVP_Hub_Icon.png')
        self.addDirectoryItem("Minimax", f"get_sections&url={quote_plus(base_url + '/minimax')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/301563844145/MMX_Hub_Icon.png')
        self.addDirectoryItem("Jimjam", f"get_sections&url={quote_plus(base_url + '/jimjam')}", '', 'https://assets-secure.applicaster.com/zapp/assets/app_family/5098/manual_feeds/600994942317/JJM_Hub_Icon.png')
        
        if custom_view_list == 'true':
            self.endDirectory(fixed_wide_view)
        else:
            self.endDirectory(user_change_view)

    def _get_cache_filename(self, url):
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        clean_name = re.sub(r'[^\w]', '_', url.split('/')[-1].split('?')[0])
        if not clean_name: clean_name = "index"
        return os.path.join(CACHE_DIR, f"{clean_name}_{url_hash}.json")

    def get_sections(self, url):
        if not self._check_credentials(): return
        cache_file = self._get_cache_filename(url)
        data_map = {}
        
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < CACHE_TIME:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data_map = json.load(f)
        else:
            resp = auth.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                containers = soup.find_all('div', class_=lambda c: c and 'component-' in c)
                processed_sections_count = 0
                current_title = "Ismeretlen"
                
                for container in containers:
                    header = container.find(class_=lambda c: c and 'label' in c)
                    cells = container.find_all('div', attrs={"data-testid": lambda x: x and x.startswith('power-cell-')})
                    
                    if cells:
                        if processed_sections_count == 0:
                            processed_sections_count += 1
                            continue
                        if header:
                            raw_title = header.get_text(strip=True)
                            current_title = re.sub(r'(.+?)\1+', r'\1', raw_title)
                        
                        if current_title not in data_map:
                            data_map[current_title] = []

                        seen_in_this_section = {item['link'] for item in data_map[current_title]}
                        
                        for cell in cells:
                            a_tag = cell.find('a', href=True)
                            if not a_tag: continue
                            
                            href = a_tag.get('href')
                            if '/badge/' in href: continue
                            
                            link = base_url + href

                            if link in seen_in_this_section:
                                continue
                            
                            title = a_tag.get('title', 'Cím nélkül')
                            content_type = "series" if "/series/" in href or "/magazin/" in href else "movies" if "/movies/" in href else "player"
                            
                            image_url = ''
                            payload_img = cell.find('div', attrs={"data-payload-image": "true"})
                            if payload_img:
                                img_el = payload_img.find('img')
                                if img_el:
                                    src = img_el.get('src', '')
                                    if src.startswith('data:image'):
                                        srcset = img_el.get('srcset', '') or img_el.get('srcSet', '')
                                        if srcset: src = srcset.split(',')[0].split(' ')[0]
                                    if src.startswith('http'):
                                        image_url = src if 'fastly_token' in src else re.sub(r'/\d+x\d+/match/', '/300x400/match/', src)
                            
                            data_map[current_title].append({"title": title, "link": link, "image": image_url, "type": content_type})
                            seen_in_this_section.add(link)
                            
                        processed_sections_count += 1
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data_map, f, ensure_ascii=False)

        for section_name, items in data_map.items():
            if section_name != "Ismeretlen" and len(items) > 0:
                query = f"get_section_items&url={quote_plus(url)}&section={quote_plus(section_name)}"
                self.addDirectoryItem(section_name, query, 'DefaultFolder.png', 'DefaultFolder.png')
        
        if custom_view_list == 'true':
            self.endDirectory(fixed_wide_view)
        else:
            self.endDirectory(user_change_view)

    def get_section_items(self, url, section_name, page=1):
        page = int(page)
        cache_file = self._get_cache_filename(url)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data_map = json.load(f)
            all_items = data_map.get(section_name, [])
            start = (page - 1) * 25
            end = start + 25
            for item in all_items[start:end]:
                is_folder = item['type'] in ['series', 'movies']
                action = "get_items" if is_folder else "player_link_handler"
                self.addDirectoryItem(item['title'], f"{action}&url={quote_plus(item['link'])}", item['image'], 'DefaultVideo.png', isFolder=is_folder, meta={'title': item['title']})
            if end < len(all_items):
                self.addDirectoryItem("Tovább >>", f"get_section_items&url={quote_plus(url)}&section={quote_plus(section_name)}&page={page+1}", 'DefaultFolder.png', 'DefaultFolder.png')
        
        if custom_view_list == 'true':
            self.endDirectory(fixed_wide_view)
        else:
            self.endDirectory(user_change_view)

    def extraSeries(self, url):
        cache_file = self._get_cache_filename(url)
        entries = []

        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < CACHE_TIME:
            with open(cache_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        else:
            resp = auth.get(url + "?_data=routes%2F%24")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    for feed in data.get('serverLoadedFeeds', []):
                        for entry in feed.get('feed', {}).get('entry', []):
                            if entry.get('extensions', {}).get('content_type') == 'FullEpisode':
                                ext = entry.get('extensions', {})

                                img = ""
                                media_group = entry.get('media_group', [{}])
                                if media_group:
                                    media_items = media_group[0].get('media_item', [{}])
                                    if media_items: img = media_items[0].get('src', '')

                                entries.append({
                                    "show": ext.get('show', ''),
                                    "season": int(ext.get('season', 0)) if str(ext.get('season')).isdigit() else 0,
                                    "episode": int(ext.get('episode', 0)) if str(ext.get('episode')).isdigit() else 0,
                                    "title": entry.get('title', ''),
                                    "web_link": base_url + entry.get('_webLink', ''),
                                    "image": img,
                                    "plot": ext.get('long_description', ''),
                                    "duration": int(ext.get('duration', 0)) // 1000 if ext.get('duration') else 0,
                                    "year": int(ext.get('production_year')) if str(ext.get('production_year', '')).isdigit() else 0,
                                    "mpaa": ext.get('rating_tv', ''),
                                    "cast": ext.get('actors_talent', '').split(', ') if ext.get('actors_talent') else []
                                })
                    
                    with open(cache_file, 'w', encoding='utf-8') as f: 
                        json.dump(entries, f, ensure_ascii=False)
                except Exception as e:
                    log(f"Hiba a sorozat JSON feldolgozásánál: {str(e)}")

        for e in entries:
            display_name = f"S{e['season']:02d}E{e['episode']:02d} - {e['title']}"
            
            metadata = {
                'title': e['title'], 'tvshowtitle': e['show'], 'season': e['season'], 'episode': e['episode'], 'plot': e['plot'], 'duration': e['duration'], 'year': e['year'], 'mpaa': e['mpaa'], 'cast': e['cast'], 'mediatype': 'episode'}

            self.addDirectoryItem(
                name=display_name, 
                query=f"player_link_handler&url={quote_plus(e['web_link'])}", 
                thumb=e['image'], 
                icon='DefaultVideo.png', 
                isFolder=False, 
                meta=metadata
            )
            
        if custom_view_list == 'true':
            self.endDirectory(fixed_wide_view)
        else:
            self.endDirectory(user_change_view)

    def extraMovies(self, url):
        data_url = url + "?_data=routes%2F%24"
        resp = auth.get(data_url)
        
        if resp.status_code != 200:
            if custom_view_list == 'true':
                self.endDirectory(fixed_wide_view)
            else:
                self.endDirectory(user_change_view)
            return

        try:
            data = resp.json()
            for feed_item in data.get('serverLoadedFeeds', []):
                entries = feed_item.get('feed', {}).get('entry', [])
                
                for entry in entries:
                    ext = entry.get('extensions', {})
                    if ext.get('content_type') == 'FullMovie':
                        title = entry.get('title', 'Ismeretlen film')
                        web_link = entry.get('_webLink')
                        if not web_link: continue

                        metadata = {
                            'title': title, 'plot': ext.get('long_description', ''), 'year': int(ext.get('production_year')) if ext.get('production_year') and ext.get('production_year').isdigit() else 0, 'director': ext.get('director', ''), 'mpaa': ext.get('rating_tv', ''), 'genre': ext.get('tags', '').replace(', ', ' / '), 'duration': int(ext.get('duration', 0)) // 1000 if ext.get('duration') else 0}

                        cast = ext.get('actors_talent', '').split(', ')
                        if cast: metadata['cast'] = cast

                        img = ""
                        media_group = entry.get('media_group', [{}])
                        if media_group:
                            media_items = media_group[0].get('media_item', [{}])
                            if media_items: img = media_items[0].get('src', '')

                        p_url = base_url + web_link
                        
                        self.addDirectoryItem(
                            name=f"[LEJÁTSZÁS] {title}", 
                            query=f"player_link_handler&url={quote_plus(p_url)}", 
                            thumb=img, 
                            icon='DefaultVideo.png', 
                            isFolder=False,
                            meta=metadata
                        )
            
        except Exception as e:
            log(f"HIBA az extraMovies-ban: {str(e)}")

        if custom_view_list == 'true':
            self.endDirectory(fixed_wide_view)
        else:
            self.endDirectory(user_change_view)

    def player_link_handler(self, player_url):
        self.playMovie(player_url)

    def playMovie(self, player_html_url):
        resp = auth.get(player_html_url)

        match = re.search(r'window\.__remixContext\s*=\s*(\{.*?\});', resp.text) or \
                re.search(r'<script>window.*Context = ({.*});</script>', resp.text) or \
                re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', resp.text)
        
        if not match:
            log("HIBA: Nem található JSON context a lejátszáshoz!", xbmc.LOGERROR)
            return

        data = json.loads(match.group(1))
        loader_data = data.get('state', {}).get('loaderData', {})
        item = loader_data.get('routes/player', {}).get('playableItem', {}) or \
               loader_data.get('routes/$', {}).get('playableItem', {})

        if not item:
            log("HIBA: Nincs playableItem.", xbmc.LOGWARNING)
            xbmcgui.Dialog().ok('SELEKT', 'Ez a tartalom a Te csomagodban nem elérhető.\nEllenőrizd az előfizetésed a selekt.tv oldalon!')
            xbmcplugin.setResolvedUrl(syshandle, False, xbmcgui.ListItem())
            return

        content_info = item.get('content', {})
        stream_url = content_info.get('src')
        mime_type = content_info.get('type', '')

        extensions = item.get('extensions', {})
        lic_url = extensions.get('drm', {}).get('widevine', {}).get('license_url')

        if not stream_url:
            log("HIBA: Nincs stream URL (src)!", xbmc.LOGERROR)
            xbmcgui.Dialog().notification('SELEKT', 'A videó nem található!', xbmcgui.NOTIFICATION_WARNING)
            xbmcplugin.setResolvedUrl(syshandle, False, xbmcgui.ListItem())
            return
        
        li = xbmcgui.ListItem(path=stream_url)
        li.setProperty('inputstream', 'inputstream.adaptive')

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/146.0.0.0"
        headers = f"User-Agent={quote(user_agent)}&Origin={quote('https://hu.selekt.tv')}&Referer={quote(player_html_url)}&verifypeer=false"
        
        li.setProperty('inputstream.adaptive.stream_headers', headers)
        li.setProperty('inputstream.adaptive.manifest_headers', headers)
        
        if 'hls' in mime_type or stream_url.endswith('.m3u8'):
            li.setProperty('inputstream.adaptive.manifest_type', 'hls')
        elif lic_url:
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')

            license_headers = {
                "User-Agent": user_agent,
                "Content-Type": "application/octet-stream",
                "Origin": "https://hu.selekt.tv",
                "Referer": player_html_url
            }
            encoded_license_headers = "&".join(f"{quote(k)}={quote(v)}" for k, v in license_headers.items())

            license_config = [lic_url, encoded_license_headers, 'R{SSM}', '']
            license_key_string = '|'.join(license_config)
            li.setProperty('inputstream.adaptive.license_key', license_key_string)
        else:
            log("HIBA: Ismeretlen stream típus vagy hiányzó licenc!", xbmc.LOGERROR)
            return

        xbmcplugin.setResolvedUrl(syshandle, True, li)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '': thumb = icon
        cm = []
        if queue: cm.append(('Queue Item', f'RunPlugin({sysaddon}?action=queueItem)'))
        if context: cm.append((context[0], f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': icon, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        item.setProperty('Fanart_Image', Fanart if Fanart else addonFanart)
        if not isFolder: item.setProperty('IsPlayable', 'true')
        if meta: item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)