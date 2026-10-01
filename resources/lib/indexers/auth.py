# -*- coding: utf-8 -*-
import requests
import json
import xbmcvfs
import xbmcaddon
import binascii
import xbmc
import os

addon = xbmcaddon.Addon('plugin.video.selekt')

def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"SELEKT AUTH DEBUG: {msg}", level)

PROFILE_DIR = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
if not xbmcvfs.exists(PROFILE_DIR):
    xbmcvfs.mkdir(PROFILE_DIR)
COOKIES_FILE = os.path.join(PROFILE_DIR, 'selekt_cookies.json')
h_r = binascii.unhexlify
h_f = lambda x: x.decode('utf-8')
_p_m = "65794a795a575270636d566a6446567961534936496d68306448427a4f69387661485575633256735a5774304c6e52324c324677615339765958563061434973496d4e736157567564456c6b496a6f69593278705a573530535752585a5749694c434a7a644746305a534936496b317956455a6e4f46644a56326447526b394e4e3152664d6a4a774f484e42596e70354e58704c53555a5053315a6d5531413662314a344e6a51694c434a6a644867694f6d353162477839"

def _logout():
    if not xbmcvfs.exists(COOKIES_FILE):
        return

    try:
        f = xbmcvfs.File(COOKIES_FILE, 'r')
        cookies_content = f.read()
        f.close()

        if cookies_content:
            cookies = json.loads(cookies_content)

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Origin": "https://hu.selekt.tv",
                "Referer": "https://hu.selekt.tv/"
            }

            logout_url = 'https://hu.selekt.tv/api/logout?_data=routes%2Fapi.logout'
            requests.post(logout_url, cookies=cookies, headers=headers, timeout=10)
    except Exception as e:
        log(f"Hiba a kijelentkezés során (valószínűleg már lejárt): {str(e)}", xbmc.LOGWARNING)

    try:
        xbmcvfs.delete(COOKIES_FILE)
    except Exception as e:
        log(f"Cookie fájl törlése sikertelen: {e}", xbmc.LOGWARNING)

def _login():
    _logout()

    EMAIL = addon.getSetting('username')
    PASSWORD = addon.getSetting('password')
    if not EMAIL or not PASSWORD:
        log("HIBA: Üres email vagy jelszó!", xbmc.LOGERROR)
        return None

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    })

    payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "encodedParams": h_f(h_r(_p_m)),
        "registrationToken": None,
        "selektProviderShortName": None
    }

    try:
        resp = session.post('https://amc.prod.greendev.hu/api/get-auth-url', json=payload, timeout=15)
        if resp.status_code == 200:
            resp_data = resp.json()
            if resp_data.get("success"):
                auth_url = resp_data.get("data")
                r2 = session.get(auth_url, allow_redirects=True, timeout=15)
                cookies_dict = session.cookies.get_dict()
                f = xbmcvfs.File(COOKIES_FILE, 'w')
                f.write(json.dumps(cookies_dict))
                f.close()
                return cookies_dict
            else:
                log(f"API hiba: {resp_data.get('errorMessage')}", xbmc.LOGERROR)
        else:
            log(f"Auth API nem 200: {resp.status_code}, body: {resp.text[:500]}", xbmc.LOGERROR)
    except Exception as e:
        log(f"KRITIKUS HIBA a login során: {str(e)}", xbmc.LOGERROR)
    return None

def _load_cookies():
    if not xbmcvfs.exists(COOKIES_FILE):
        return None
    try:
        f = xbmcvfs.File(COOKIES_FILE, 'r')
        content = f.read()
        f.close()
        if not content:
            return None
        cookies = json.loads(content)
        return cookies
    except Exception as e:
        log(f"Cookie olvasási hiba: {e}", xbmc.LOGWARNING)
        return None

def _is_login_page(html):
    has_remix = 'window.__remixContext' in html
    has_react_router = 'window.__reactRouterContext' in html
    has_root_div = '<div id="root">' in html
    has_main_js = '/static/js/main.' in html

    if has_remix or has_react_router:
        return False
    if has_root_div and has_main_js:
        return True
    if len(html) < 5000:
        return True
    return False

def get(url):
    cookies = _load_cookies()

    if cookies is None:
        cookies = _login()
        if not cookies:
            r = requests.Response()
            r.status_code = 401
            return r

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"}

    try:
        resp = requests.get(url, cookies=cookies, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code in [401, 403] or _is_login_page(resp.text):
            cookies = _login()
            if cookies:
                resp = requests.get(url, cookies=cookies, headers=headers, timeout=15, allow_redirects=True)
        return resp
    except Exception as e:
        r = requests.Response()
        r.status_code = 500
        return r