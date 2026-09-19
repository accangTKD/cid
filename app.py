### Final API: Generate + Info + Token (1 file)
### Letakkan file pb2 berikut di folder yang SAMA:
###   - FreeFire_pb2.py
###   - AccountPersonalShow_pb2.py
###   - main_pb2.py

import warnings
warnings.filterwarnings('ignore')

import requests
import random
import string
import time
import json
import codecs
import base64
import hmac
import hashlib
import asyncio
from datetime import datetime, timedelta

import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3
from google.protobuf import json_format

import FreeFire_pb2
import AccountPersonalShow_pb2
import main_pb2

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ============ KONFIGURASI TELEGRAM ============
BOT_TOKEN = "8965307683:AAGXwuIge4QKuYXtrkXhG4AahxDrynqi7SY"
OWNER_ID = 8660700322
CHANNEL_PROMO = "@dindingijo"

# ============ KONFIGURASI API KEYS ============
# limit = generate, info_limit = /info  (sama kan saja)
API_KEYS = {
    "FREE_KEY_001":      {"limit": 50,     "used": 0, "info_limit": 50,     "info_used": 0, "last_reset_day": 0},
    "VIP_KEY_001":       {"limit": 500,    "used": 0, "info_limit": 500,    "info_used": 0, "last_reset_day": 0},
    "UNLIMITED_001":     {"limit": 999999, "used": 0, "info_limit": 999999, "info_used": 0, "last_reset_day": 0},
}

# ============ KONFIGURASI GENERATOR ============
REGION_CHOICE = 1

REGION_MAP = {
    1: {"code": "ID",  "name": "INDONESIA",   "lang": "id", "host": "loginbp.ppmainecoonghj.com"},
    2: {"code": "ME",  "name": "MIDDLE EAST", "lang": "ar", "host": "loginbp.ppmainecoonghj.com"},
    3: {"code": "IND", "name": "INDIA",       "lang": "hi", "host": "loginbp.ppmainecoonghj.com"},
    4: {"code": "TH",  "name": "THAILAND",    "lang": "th", "host": "loginbp.ppmainecoonghj.com"},
    5: {"code": "VN",  "name": "VIETNAM",     "lang": "vi", "host": "loginbp.ppmainecoonghj.com"},
    6: {"code": "BD",  "name": "BANGLADESH",  "lang": "bn", "host": "loginbp.ppmainecoonghj.com"},
    7: {"code": "PK",  "name": "PAKISTAN",    "lang": "ur", "host": "loginbp.ppmainecoonghj.com"},
    8: {"code": "TW",  "name": "TAIWAN",      "lang": "zh", "host": "loginbp.ppmainecoonghj.com"},
    9: {"code": "CIS", "name": "RUSSIA",      "lang": "ru", "host": "loginbp.ppmainecoonghj.com"},
    10:{"code": "SAC", "name": "SPAIN",       "lang": "es", "host": "loginbp.ppmainecoonghj.com"},
    11:{"code": "BR",  "name": "BRAZIL",      "lang": "pt", "host": "loginbp.ppmainecoonghj.com"},
}

SELECTED    = REGION_MAP.get(REGION_CHOICE, REGION_MAP[1])
REGION      = SELECTED["code"]
REGION_NAME = SELECTED["name"]
LANG        = SELECTED["lang"]
MAJOR_HOST  = SELECTED["host"]

NAME_PREFIX = "Ccang"
PASS_PREFIX = "NewApiGenByCcang"

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# AES key/iv untuk MajorLogin (info / jwt)
MAIN_KEY = b'Yg&tc%DEuh6%Zc^8'
MAIN_IV  = b'6oyZDr22E3ychjM%'

# Datadome cookies (untuk bypass registrasi)
DATADOME_COOKIE_REG = "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh"
DATADOME_COOKIE_TOK = "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv"
DEVICE_ID = "02-344afb0e-593c-40b7-92f2-171972f74807"

WAF_UAS = [
    "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
    "GarenaMSDK/4.0.44(25028RN03A;Android 15;id;ID;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.44(Xiaomi 14;Android 14;id;ID;)",
    "GarenaMSDK/4.0.44(Poco X5 Pro;Android 12;en;MY;)",
]

USERAGENT_INFO = "Dalvik/2.1.0 (Linux; U; Android 14; CPH2095 Build/RKQ1.211119.001)"
RELEASEVERSION = "OB55"

# ============ AKUN UNTUK JWT (SIAM_CODEX style) ============
# Dipakai untuk /info. Bisa diganti sendiri.
JWT_ACCOUNT = {
    "uid": "7742406516",
    "password": "507D3250C779A4E73A74B66998E99DD4ED95A6133A07151FC0411A225C405ADD"
}

# In-memory token cache
_token_cache = {}

# ============ HTTP CLIENT (pooling) ============
HTTP_LIMITS = httpx.Limits(max_keepalive_connections=20, max_connections=50)
HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_http_client = httpx.Client(limits=HTTP_LIMITS, timeout=HTTP_TIMEOUT)


# ============================================================
#  PROTOBUF ENCODER (untuk generator)
# ============================================================
def encode_varint(n):
    if n < 0: return b''
    result = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n: byte |= 0x80
        result.append(byte)
        if not n: break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, int):
        return encode_varint((field_num << 3) | 0) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        return encode_varint((field_num << 3) | 2) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())


# ============================================================
#  AES HELPERS
# ============================================================
def aes_encrypt_bytes(data_bytes):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data_bytes, AES.block_size))

def encrypt_api(plain_bytes):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain_bytes, AES.block_size))

def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext, AES.block_size))

def json_to_proto(json_data: str, proto_message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()


# ============================================================
#  TELEGRAM
# ============================================================
def send_to_owner(account_id, uid, password, region_name, api_key, caller_ip):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"""🔥 <b>NEW ACCOUNT GENERATED VIA API</b> 🔥

🆔 Account ID: <code>{account_id}</code>
📝 UID: <code>{uid}</code>
🔑 <b>PASSWORD: <code>{password}</code></b>
🌍 Region: {region_name}
🔑 API Key: <code>{api_key}</code>
📞 IP Caller: {caller_ip}
⏰ Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}

💡 Join: {CHANNEL_PROMO}"""
    try:
        requests.post(
            url,
            json={"chat_id": OWNER_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception:
        pass


# ============================================================
#  HELPERS GENERATOR
# ============================================================
def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def generate_password():
    return f"{PASS_PREFIX}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def generate_name():
    base = f"{NAME_PREFIX}{random.randint(10, 999)}"
    syms = ['~','!','@','#','$','%','^','&','*','-','_','+','=']
    p = random.randint(1, 3)
    if p == 1:
        s = random.choice(syms)
        return f"{s}{base}{s}"
    elif p == 2:
        s1, s2 = random.sample(syms, 2)
        return f"{s1}{s2}{base}"
    return base

def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split(".")
        if len(parts) < 2: return None
        pp = parts[1]
        pad_n = 4 - (len(pp) % 4)
        if pad_n != 4: pp += "=" * pad_n
        return json.loads(base64.urlsafe_b64decode(pp))
    except Exception:
        return None

def obfuscate_open_id(open_id):
    keystream = [
        0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,
        0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
        0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,
        0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30
    ]
    encoded = ''.join(
        chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
        for i in range(len(open_id))
    )
    return codecs.decode(
        encoded.encode('unicode_escape').decode('utf-8'),
        'unicode_escape'
    ).encode('latin1')


# ============================================================
#  JWT / TOKEN HELPERS (untuk /info & /token)
# ============================================================
def get_access_token(account: str):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = (
        account
        + "&response_type=token&client_type=2"
        + "&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
        + "&client_id=100067"
    )
    headers = {
        "User-Agent": USERAGENT_INFO,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    resp = _http_client.post(url, data=payload, headers=headers)
    data = resp.json()
    return data.get("access_token", "0"), data.get("open_id", "0")


def try_parse_login_res(data: bytes):
    try:
        msg = FreeFire_pb2.LoginRes()
        msg.ParseFromString(data)
        if msg.account_id and msg.account_id > 0:
            return json.loads(json_format.MessageToJson(msg))
    except Exception:
        pass
    return None


def extract_login_res(raw: bytes) -> dict:
    parsed = try_parse_login_res(raw)
    if parsed: return parsed

    idx = 0
    while True:
        idx = raw.find(b"\x08", idx)
        if idx == -1: break
        parsed = try_parse_login_res(raw[idx:])
        if parsed: return parsed
        idx += 1

    jwt_marker = raw.find(b"eyJhbGciOiJIUzI1NiIs")
    if jwt_marker != -1:
        for i in range(jwt_marker - 1, max(jwt_marker - 300, -1), -1):
            if raw[i] == 0x42:
                parsed = try_parse_login_res(raw[i:])
                if parsed: return parsed
                break

    raise Exception(f"Could not parse LoginRes. Raw: {raw[:200]}")


def generate_jwt_token(uid: str, password: str):
    start_time = time.time()

    token_val, open_id = get_access_token(f"uid={uid}&password={password}")
    if token_val == "0" or open_id == "0":
        raise Exception("Invalid UID or Password — access token not received")

    body = json.dumps({
        "open_id": open_id,
        "open_id_type": "4",
        "login_token": token_val,
        "orign_platform_type": "4",
    })
    proto_bytes = json_to_proto(body, FreeFire_pb2.LoginReq())
    payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)

    headers = {
        "User-Agent": USERAGENT_INFO,
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-Ga-Sv": "1789534056",
        "Authorization": "Bearer",
        "X-Ga": "v1 1",
        "Releaseversion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "PlAy_VeR": "1.132.1",
        "Ob_VeR": RELEASEVERSION,
    }

    resp = _http_client.post(f"https://{MAJOR_HOST}/MajorLogin", data=payload, headers=headers)
    msg = extract_login_res(resp.content)

    elapsed = time.time() - start_time

    return {
        "access_token": token_val,
        "open_id": open_id,
        "real_uid": str(msg.get("accountId", "")),
        "status": "success",
        "time": f"{elapsed:.2f}s",
        "token": f"Bearer {msg.get('token', '')}",
        "server_url": msg.get("serverUrl", ""),
        "region": msg.get("lockRegion", ""),
    }


def get_token_cached():
    """Ambil token dari cache, atau generate baru pakai JWT_ACCOUNT."""
    cached = _token_cache.get("main")
    if cached and cached.get("expires_at", 0) > time.time():
        return cached

    data = generate_jwt_token(JWT_ACCOUNT["uid"], JWT_ACCOUNT["password"])
    token_info = {
        "token": data["token"],
        "server_url": data.get("server_url") or f"https://clientbp.ppmainecoonghj.com",
        "region": data.get("region") or REGION,
        "expires_at": time.time() + 25200,  # 7 jam
    }
    _token_cache["main"] = token_info
    return token_info


# ============================================================
#  GENERATOR (dari Project 1)
# ============================================================
def generate_one_account(max_retry=5):
    for _ in range(max_retry):
        try:
            session = requests.Session()
            session.verify = False

            password = generate_password()

            # STEP 1 — GUEST REGISTER
            reg_payload = json.dumps({
                "app_id": 100067,
                "client_type": 2,
                "password": password,
                "source": 2
            }, separators=(',', ':'))

            signature = hmac.new(
                HEX_KEY.encode(), reg_payload.encode(), hashlib.sha256
            ).hexdigest()

            headers_reg = {
                "User-Agent": random.choice(WAF_UAS),
                "Connection": "Keep-Alive",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Authorization": f"Signature {signature}",
                "Content-Type": "application/json; charset=utf-8",
                "Cookie": DATADOME_COOKIE_REG,
                "Host": "100067.connect.garena.com",
                "X-Forwarded-For": get_random_ip(),
                "X-Real-IP": get_random_ip(),
            }

            resp_reg = session.post(
                "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                headers=headers_reg, data=reg_payload, timeout=15
            )

            if resp_reg.status_code != 200:
                time.sleep(0.5); continue
            try:
                reg_json = resp_reg.json()
            except Exception:
                time.sleep(0.5); continue
            if reg_json.get("code") != 0:
                time.sleep(0.5); continue

            uid = reg_json['data']['uid']
            time.sleep(0.05)

            # STEP 2 — TOKEN GRANT
            tok_payload = json.dumps({
                "client_id": 100067,
                "client_secret": HEX_KEY,
                "client_type": 2,
                "device_id": DEVICE_ID,
                "password": password,
                "response_type": "token",
                "uid": uid,
            }, separators=(',', ':'))

            headers_tok = headers_reg.copy()
            headers_tok["Cookie"] = DATADOME_COOKIE_TOK

            resp_tok = session.post(
                "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
                headers=headers_tok, data=tok_payload, timeout=15
            )
            if resp_tok.status_code != 200:
                time.sleep(0.5); continue
            try:
                tok_json = resp_tok.json()
            except Exception:
                time.sleep(0.5); continue
            if tok_json.get("code") != 0:
                time.sleep(0.5); continue

            access_token = tok_json['data']['access_token']
            open_id      = tok_json['data']['open_id']
            time.sleep(0.05)

            # STEP 3 — OBFUSCATE
            field = obfuscate_open_id(open_id)

            # STEP 4 — MAJOR REGISTER
            name = generate_name()
            proto = build_proto({
                1: name, 2: access_token, 3: open_id,
                5: 102000007, 6: 4, 7: 1, 13: 1,
                14: field, 15: LANG, 16: 1, 17: 1
            })
            enc_major = aes_encrypt_bytes(proto)

            headers_major = {
                "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                "Accept-Encoding": "deflate, gzip",
                "X-GA-SV": "1789535859",
                "Authorization": "Bearer",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB55",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Unity-Version": "2018.4.12f1",
                "Host": MAJOR_HOST,
            }

            session.post(
                f"https://{MAJOR_HOST}/MajorRegister",
                headers=headers_major, data=enc_major, timeout=15
            )
            time.sleep(0.05)

            # STEP 5 — MAJOR LOGIN
            payload_parts = [
                b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
                LANG.encode("ascii"),
                b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118693\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5',
            ]
            raw_payload = b"".join(payload_parts)
            raw_payload = raw_payload.replace(
                b"afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390",
                access_token.encode()
            )
            raw_payload = raw_payload.replace(
                b"1d8ec0240ede109973f3321b9354b44d",
                open_id.encode()
            )

            enc_bytes = encrypt_api(raw_payload)
            response = session.post(
                f"https://{MAJOR_HOST}/MajorLogin",
                headers=headers_major, data=enc_bytes, timeout=15
            )

            account_id = "N/A"
            jwt_token = ""

            if response.status_code == 200 and len(response.text) > 10:
                js = response.text.find("eyJ")
                if js != -1:
                    jwt_token = response.text[js:]
                    sd = jwt_token.find(".", jwt_token.find(".") + 1)
                    if sd != -1:
                        jwt_token = jwt_token[:sd + 44]
                    decoded = decode_jwt_payload(jwt_token)
                    if decoded:
                        account_id = (
                            decoded.get("account_id")
                            or decoded.get("external_id")
                            or "N/A"
                        )

            if account_id != "N/A":
                return {
                    "account_id": str(account_id),
                    "uid": uid,
                    "password": password,
                    "name": name,
                    "jwt_token": jwt_token,
                    "region": REGION_NAME,
                    "region_code": REGION,
                    "lang": LANG,
                }

        except Exception:
            pass

        time.sleep(0.5)

    return None


# ============================================================
#  INFO ACCOUNT (pakai protobuf)
# ============================================================
def get_item_name(item_id):
    if not item_id or item_id in ("0", 0):
        return "N/A"
    try:
        r = requests.get(f"https://api.danger.workers.dev/item/{item_id}", timeout=3)
        if r.status_code == 200:
            return r.json().get("name", str(item_id))
        return str(item_id)
    except Exception:
        return str(item_id)


def get_rank_name(rp):
    try:
        rp = int(rp)
    except Exception:
        return "N/A"
    if rp == 0: return "Bronze I"
    if rp < 100: return "Bronze II"
    if rp < 200: return "Bronze III"
    if rp < 300: return "Silver I"
    if rp < 400: return "Silver II"
    if rp < 500: return "Silver III"
    if rp < 600: return "Gold I"
    if rp < 700: return "Gold II"
    if rp < 800: return "Gold III"
    if rp < 900: return "Platinum I"
    if rp < 1000: return "Platinum II"
    if rp < 1100: return "Platinum III"
    if rp < 1200: return "Diamond I"
    if rp < 1300: return "Diamond II"
    if rp < 1400: return "Diamond III"
    if rp < 1500: return "Heroic"
    if rp < 2000: return "Master"
    return "Grandmaster"


def ts_to_bst(ts):
    try:
        dt = datetime.fromtimestamp(int(ts)) + timedelta(hours=6)
        return dt.strftime("%d %b %Y at %I:%M:%S %p") + " (BST)"
    except Exception:
        return "N/A"


def fetch_account_info(uid: int):
    """Query info akun pakai token dari cache."""
    token_info = get_token_cached()
    token = token_info["token"]
    server_url = token_info["server_url"]

    payload = json_to_proto(
        json.dumps({"a": uid, "b": 7}),
        main_pb2.GetPlayerPersonalShow()
    )
    data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)

    headers = {
        "User-Agent": USERAGENT_INFO,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/octet-stream",
        "Authorization": token,
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION,
    }

    resp = _http_client.post(
        server_url.rstrip("/") + "/GetPlayerPersonalShow",
        data=data_enc, headers=headers
    )
    if resp.status_code != 200:
        return None

    info = AccountPersonalShow_pb2.AccountPersonalShowInfo()
    info.ParseFromString(resp.content)
    result = json.loads(json_format.MessageToJson(info))
    result["region"] = token_info.get("region", REGION)
    return result


def build_info_response(uid: str, account_data: dict):
    basic   = account_data.get("basicInfo", {}) or {}
    clan    = account_data.get("clanBasicInfo", {}) or {}
    social  = account_data.get("socialInfo", {}) or {}
    pet     = account_data.get("petInfo", {}) or {}
    captain = account_data.get("captainBasicInfo", {}) or {}
    credit  = account_data.get("creditScoreInfo", {}) or {}

    prime_level = "N/A"
    pd = basic.get("primeLevel")
    if isinstance(pd, dict):
        prime_level = pd.get("level", "N/A")
    elif pd is not None:
        prime_level = str(pd)

    return {
        "status": "success",
        "server_used": account_data.get("region", REGION),
        "BasicInformation": {
            "PrimeLevel": prime_level,
            "Name": basic.get("nickname", "N/A"),
            "UID": uid,
            "Level": basic.get("level", "N/A"),
            "Exp": basic.get("exp", "N/A"),
            "Region": basic.get("region", "N/A"),
            "Likes": basic.get("liked", "N/A"),
            "HonorScore": credit.get("creditScore", "N/A"),
            "CelebrityStatus": "Yes" if basic.get("showBrRank") else "No",
            "Title": get_item_name(basic.get("title", "0")),
            "Signature": social.get("signature", "N/A"),
        },
        "ActivityInformation": {
            "MostRecentOB": basic.get("releaseVersion", "N/A"),
            "BooyahPass": "Yes" if basic.get("hasElitePass") else "No",
            "CurrentBpBadges": basic.get("badgeCnt", "N/A"),
            "BRRank": get_rank_name(basic.get("rankingPoints", 0)),
            "BRPoints": basic.get("rankingPoints", 0),
            "ShowBRRank": "True" if basic.get("showBrRank") else "False",
            "ShowCSRank": "True" if basic.get("showCsRank") else "False",
            "CreatedAt": ts_to_bst(basic.get("createAt", 0)),
            "LastLogin": ts_to_bst(basic.get("lastLoginAt", 0)),
        },
        "GuildInformation": {
            "GuildName": clan.get("clanName", "No Guild"),
            "GuildID": clan.get("clanId", "N/A"),
            "GuildLevel": clan.get("clanLevel", "N/A"),
            "LiveMembers": clan.get("memberNum", "N/A"),
            "MaxMembers": clan.get("capacity", "N/A"),
        },
        "PetDetails": {
            "Equipped": "Yes" if pet.get("isSelected") else "No",
            "PetNick": pet.get("name", "N/A"),
            "PetType": get_item_name(pet.get("id", "0")),
            "PetSkill": get_item_name(pet.get("selectedSkillId", "0")),
            "PetSkin": get_item_name(pet.get("skinId", "0")),
            "PetExp": pet.get("exp", "N/A"),
            "PetLevel": pet.get("level", "N/A"),
        },
        "LeaderInformation": {
            "Name": captain.get("nickname", "N/A"),
            "UID": captain.get("accountId", "N/A"),
            "Level": captain.get("level", "N/A"),
            "Region": captain.get("region", "N/A"),
            "BooyahPass": "Yes" if captain.get("hasElitePass") else "No",
            "BRRank": get_rank_name(captain.get("rankingPoints", 0)),
            "BRPoints": captain.get("rankingPoints", 0),
        },
    }


# ============================================================
#  API KEY MANAGEMENT
# ============================================================
def check_api_key(api_key, kind="generate"):
    current_day = datetime.now().day
    if api_key not in API_KEYS:
        return False, "Invalid API key", None

    kd = API_KEYS[api_key]

    if kd.get("last_reset_day", 0) != current_day:
        kd["used"] = 0
        kd["info_used"] = 0
        kd["last_reset_day"] = current_day

    if kind == "generate":
        if kd["used"] >= kd["limit"]:
            return False, f"Daily generate limit reached! Used {kd['used']}/{kd['limit']}", kd
    else:
        if kd["info_used"] >= kd["info_limit"]:
            return False, f"Daily info limit reached! Used {kd['info_used']}/{kd['info_limit']}", kd

    return True, "OK", kd


def update_api_key_usage(api_key, kind="generate"):
    if api_key in API_KEYS:
        if kind == "generate":
            API_KEYS[api_key]["used"] += 1
        else:
            API_KEYS[api_key]["info_used"] += 1


# ============================================================
#  FLASK ROUTES
# ============================================================
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({
        "success": True,
        "message": "FreeFire API - Generate + Info + Token",
        "version": "1.0",
        "endpoints": {
            "generate": "/generate?key=YOUR_KEY",
            "info":     "/info?key=YOUR_KEY&uid=UID",
            "token":    "/token?uid=UID&password=PASSWORD",
            "status":   "/status?key=YOUR_KEY",
        }
    })


# ---------- /generate ----------
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    api_key = None
    if request.method == 'GET':
        api_key = request.args.get('key') or request.args.get('api_key')
    else:
        if request.is_json:
            api_key = request.json.get('key')
        else:
            api_key = request.form.get('key')

    if not api_key:
        return jsonify({"success": False, "message": "API key required. Use ?key=YOUR_KEY"}), 401

    valid, msg, kd = check_api_key(api_key, "generate")
    if not valid:
        return jsonify({"success": False, "message": msg}), 429

    try:
        result = generate_one_account()
        if result:
            update_api_key_usage(api_key, "generate")
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            send_to_owner(
                result["account_id"], result["uid"], result["password"],
                result["region"], api_key, client_ip
            )
            return jsonify({
                "success": True,
                "message": "Account generated successfully",
                "data": {
                    "account_id": result["account_id"],
                    "uid": str(result["uid"]),
                    "password": result["password"],
                    "region": result["region"],
                    "region_code": result["region_code"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            })
        else:
            return jsonify({"success": False, "message": "Failed to generate account. Please try again."}), 500
    except Exception:
        return jsonify({"success": False, "message": "Internal server error"}), 500


# ---------- /info ----------
@app.route('/info', methods=['GET', 'POST'])
def info():
    if request.method == 'GET':
        api_key = request.args.get('key') or request.args.get('api_key')
        uid     = request.args.get('uid')
    else:
        if request.is_json:
            body    = request.json or {}
            api_key = body.get('key') or body.get('api_key')
            uid     = body.get('uid')
        else:
            api_key = request.form.get('key') or request.form.get('api_key')
            uid     = request.form.get('uid')

    if not api_key:
        return jsonify({"success": False, "message": "API key required. Use ?key=YOUR_KEY"}), 401
    if not uid:
        return jsonify({"success": False, "message": "UID required. Use &uid=UID"}), 400

    try:
        uid_int = int(uid)
    except Exception:
        return jsonify({"success": False, "message": "Invalid UID"}), 400

    valid, msg, kd = check_api_key(api_key, "info")
    if not valid:
        return jsonify({"success": False, "message": msg}), 429

    try:
        account_data = fetch_account_info(uid_int)
        if not account_data:
            return jsonify({"success": False, "message": "Player not found"}), 404

        update_api_key_usage(api_key, "info")
        return jsonify(build_info_response(str(uid_int), account_data))
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch info: {str(e)}"}), 500


# ---------- /token ----------
@app.route('/token', methods=['GET'])
def token_route():
    uid      = request.args.get('uid')
    password = request.args.get('password')
    if not uid or not password:
        return jsonify({
            "status": "error",
            "error": "Both uid and password parameters are required"
        }), 400
    try:
        data = generate_jwt_token(uid, password)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to generate token: {str(e)}"
        }), 500


# ---------- /status ----------
@app.route('/status', methods=['GET'])
def status():
    api_key = request.args.get('key') or request.args.get('api_key')
    if not api_key:
        return jsonify({"success": False, "message": "API key required"}), 401

    current_day = datetime.now().day
    if api_key not in API_KEYS:
        return jsonify({"success": False, "message": "Invalid API key"}), 404

    kd = API_KEYS[api_key]
    if kd.get("last_reset_day", 0) != current_day:
        kd["used"] = 0
        kd["info_used"] = 0
        kd["last_reset_day"] = current_day

    return jsonify({
        "success": True,
        "api_key": api_key,
        "generate": {
            "limit": kd["limit"],
            "used": kd["used"],
            "remaining": kd["limit"] - kd["used"],
        },
        "info": {
            "limit": kd["info_limit"],
            "used": kd["info_used"],
            "remaining": kd["info_limit"] - kd["info_used"],
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
