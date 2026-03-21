# -*- coding: utf-8 -*-
import requests
import json
import xbmcvfs
import xbmcaddon
import binascii
import xbmc
import os

addon = xbmcaddon.Addon('plugin.video.selekt')

def log(msg):
    xbmc.log(f"SELEKT AUTH DEBUG: {msg}", xbmc.LOGINFO)

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
            resp = requests.post(logout_url, cookies=cookies, headers=headers, timeout=10)
    except Exception as e:
        log(f"Hiba a kijelentkezés során (valószínűleg már lejárt): {str(e)}")

    try:
        xbmcvfs.delete(COOKIES_FILE)
    except:
        pass

def _login():
    _logout()
    
    EMAIL = addon.getSetting('username')
    PASSWORD = addon.getSetting('password')
    if not EMAIL or not PASSWORD:
        log("HIBA: Üres email vagy jelszó!")
        return None

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/146.0.0.0",
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
                session.get(auth_url, allow_redirects=True, timeout=15)
                cookies_dict = session.cookies.get_dict()
                f = xbmcvfs.File(COOKIES_FILE, 'w')
                f.write(json.dumps(cookies_dict))
                f.close()
                return cookies_dict
            else:
                log(f"API hiba: {resp_data.get('errorMessage')}")
    except Exception as e:
        log(f"KRITIKUS HIBA a login során: {str(e)}")
    return None

def get(url):
    cookies = {}
    
    if not xbmcvfs.exists(COOKIES_FILE):
        cookies = _login()
        if not cookies:
            resp = requests.Response()
            resp.status_code = 401
            return resp
    else:
        try:
            f = xbmcvfs.File(COOKIES_FILE, 'r')
            content = f.read()
            f.close()
            cookies = json.loads(content)
        except:
            cookies = _login()
            
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/146.0.0.0"}
    
    try:
        resp = requests.get(url, cookies=cookies, headers=headers, timeout=15)
        if resp.status_code in [401, 403]:
            cookies = _login()
            if cookies:
                resp = requests.get(url, cookies=cookies, headers=headers, timeout=15)
        return resp
    except Exception as e:
        r = requests.Response()
        r.status_code = 500
        return r