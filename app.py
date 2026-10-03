import warnings
warnings.filterwarnings('ignore')

import requests
import random
import string
import time
import json
import base64
import hmac
import hashlib
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
BOT_TOKEN     = "8965307683:AAGXwuIge4QKuYXtrkXhG4AahxDrynqi7SY"
OWNER_ID      = 8660700322
CHANNEL_PROMO = "@dindingijo"

# ============ KONFIGURASI API KEYS ============
API_KEYS = {
    "FREE_KEY_001":  {"limit": 50,     "used": 0, "info_limit": 50,     "info_used": 0, "last_reset_day": 0},
    "VIP_KEY_001":   {"limit": 500,    "used": 0, "info_limit": 500,    "info_used": 0, "last_reset_day": 0},
    "UNLIMITED_001": {"limit": 999999, "used": 0, "info_limit": 999999, "info_used": 0, "last_reset_day": 0},
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
    12:{"code": "KH",  "name": "CAMBODIA",    "lang": "km", "host": "loginbp.ppmainecoonghj.com"},
    13:{"code": "KR",  "name": "KOREA",       "lang": "ko", "host": "loginbp.ppmainecoonghj.com"},
    14:{"code": "CN",  "name": "CHINA",       "lang": "zh", "host": "loginbp.ppmainecoonghj.com"},
    15:{"code": "MM",  "name": "MYANMAR",     "lang": "my", "host": "loginbp.ppmainecoonghj.com"},
    16:{"code": "LA",  "name": "LAOS",        "lang": "lo", "host": "loginbp.ppmainecoonghj.com"},
    17:{"code": "JP",  "name": "JAPAN",       "lang": "ja", "host": "loginbp.ppmainecoonghj.com"},
}

SELECTED    = REGION_MAP.get(REGION_CHOICE, REGION_MAP[1])
REGION      = SELECTED["code"]
REGION_NAME = SELECTED["name"]
LANG        = SELECTED["lang"]
MAJOR_HOST  = SELECTED["host"]


# ============================================================
#  SUFFIX NAMA ASLI PER BAHASA
# ============================================================
NAME_SUFFIXES = {
    "id": ["Permata","Bintang","Melati","Cahaya","Pelangi","Kencana","Bunga","Anggrek","Mutiara","Langit","Petir","Garuda","Rajawali","Nusantara","Merdeka"],
    "vi": ["Hồng","Mai","Lan","Hương","Yến","Tùng","Dũng","Hùng","Anh","Linh","Ngọc","Bảo","Kim","Thanh","Phương"],
    "ko": ["지훈","민준","서준","도윤","예준","시우","하준","주원","지호","건우","서연","지우","하윤","민서","서윤"],
    "zh": ["小龙","天龙","大鱼","无双","雷霆","烈焰","风暴","冰霜","黑豹","紫电","玄武","朱雀","白虎","青龙","破晓"],
    "ja": ["さくら","ゆうき","はると","ひかり","たける","つばさ","みなと","りく","そら","ゆづき","レオン","カイト","リン","ハル","ソラ"],
    "th": ["น้ำฟ้า","สายลม","ตะวัน","เดือน","จันทร์","ดาว","นภา","ปลา","มังกร","ไทย","รัก","เพชร","ทอง","เงิน","ฟ้า"],
    "km": ["ស្រី","ព្រះ","ចន្ទ","ផ្កាយ","ទឹក","ភ្នំ","ព្រៃ","ខ្យល់","ភ្លើង","ដី","ស្នេហ៍","កូន","មាស","ពេជ្រ","ព្រះចន្ទ"],
    "lo": ["ດາວ","ຈັນ","ຟ້າ","ນ້ຳ","ໄຟ","ປ່າ","ພູ","ລົມ","ຄຳ","ເງິນ"],
    "my": ["ပန်း","နေ","လ","ကြယ်","တောင်","မြစ်","လေ","မီး","ရွှေ","ငွေ"],
    "ar": ["نجم","قمر","شمس","سماء","بحر","نار","ريح","ذهب","فضة","أسد"],
    "hi": ["तारा","चाँद","सूरज","आसमान","समुंदर","आग","हवा","सोना","चांदी","शेर"],
    "bn": ["তারা","চাঁদ","সূর্য","আকাশ","সমুদ্র","আগুন","বাতাস","সোনা","রূপা","সিংহ"],
    "ur": ["ستارہ","چاند","سورج","آسمان","سمندر","آگ","ہوا","سونا","چاندی","شیر"],
    "ru": ["Звезда","Луна","Солнце","Небо","Море","Огонь","Ветер","Золото","Серебро","Лев"],
    "es": ["Estrella","Luna","Sol","Cielo","Mar","Fuego","Viento","Oro","Plata","Leon"],
    "pt": ["Estrela","Lua","Sol","Ceu","Mar","Fogo","Vento","Ouro","Prata","Leao"],
    "en": ["Star","Moon","Sun","Sky","Sea","Fire","Wind","Gold","Silver","Lion"],
}
DEFAULT_SUFFIXES = ["Star", "Moon", "Sun", "Sky", "Fire"]

CORE_PREFIX = "Ccang"
MIN_TOTAL   = 7
MAX_TOTAL   = 11


def generate_name(lang: str = None, min_len: int = MIN_TOTAL, max_len: int = MAX_TOTAL) -> str:
    lang = lang or LANG
    suffixes = NAME_SUFFIXES.get(lang) or DEFAULT_SUFFIXES
    core = CORE_PREFIX
    core_len = len(core)

    if core_len >= max_len:
        return core[:max_len]

    for _ in range(80):
        sfx = random.choice(suffixes)
        max_num_len = min(4, max_len - core_len - 1)

        if max_num_len < 1:
            num_len = random.randint(1, max_len - core_len)
            lo = 10 ** (num_len - 1) if num_len > 1 else 1
            hi = 10 ** num_len - 1
            num = random.randint(lo, hi)
            name = f"{core}{num}"
            if min_len <= len(name) <= max_len:
                return name
            continue

        num_len = random.randint(1, max_num_len)
        slot_sfx = max_len - core_len - num_len
        if slot_sfx < 1:
            continue

        sfx_use = sfx[:slot_sfx]
        if not sfx_use:
            continue

        lo = 10 ** (num_len - 1) if num_len > 1 else 1
        hi = 10 ** num_len - 1
        num = random.randint(lo, hi)

        name = f"{core}{sfx_use}{num}"
        if min_len <= len(name) <= max_len:
            return name

    return f"{core}{random.randint(1000, 9999)}"


PASS_PREFIX = "NewApiGenByCcang"

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

MAIN_KEY = b'Yg&tc%DEuh6%Zc^8'
MAIN_IV  = b'6oyZDr22E3ychjM%'

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

USER_AGENTS_REG = [
    "Dalvik/2.1.0 (Linux; U; Android 11)",
    "Dalvik/2.1.0 (Linux; U; Android 12)",
    "Dalvik/2.1.0 (Linux; U; Android 13)",
    "Dalvik/2.1.0 (Linux; U; Android 14; CPH2095 Build/RKQ1.211119.001)",
    "Dalvik/2.1.0 (Linux; U; Android 13; SM-A536E Build/TP1A.220624.014)",
    "Dalvik/2.1.0 (Linux; U; Android 12; V2111 Build/SP1A.210812.003)",
    "GarenaMSDK/4.0.44(25028RN03A;Android 15;id;ID;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.44(Xiaomi 14;Android 14;id;ID;)",
    "BestHTTP/2 v2.4.0",
]

USERAGENT_INFO = "Dalvik/2.1.0 (Linux; U; Android 14; CPH2095 Build/RKQ1.211119.001)"
RELEASEVERSION = "OB55"

# ── FIELD_22 (dari CLI kamu) ──────────────────────────────────────────
FIELD_22_HEX = (
    "474752450101010062000000a78910bd098e3ff2e4345d59a31db114ea088f37e32e65"
    "212ff96621793d9eb78720d0bf2ac95176569765247ada5eb01376b3b9931794a4946"
    "d76ef8890779f3f2129317e6e1cb2fdcf7b06247cea343b8d4f167eff85a2e1dfe99"
    "b4583a7e1a155dbe7f7f85cff3b223eb77222ec1228f3ee1ef6ce7f8ca24b00a554"
    "e497328812f8df74c82d519ae3e3ceab436eb145e8a517089a7cef6a4efb22214b2"
    "a4b19989b74807584afe5e52825e7ac60e19a596a9bf02d961de6a0ed2515ec6023"
    "fdb7684d9464b97b21c527ce61b6bee4ef30d20a1fa33a996952d44d44e44f2f86c"
    "768aaf2a7808ad60f91048dca0207961ba7c2555c48341b30190debc775edb2cee24"
    "4cf51fca3760ce4388be2db45e80b813b5beb9c784007b7762d7a1e428affc8a3a4"
    "cd76cbaef648a274297fde33233dccd3f272cb77f39a1affe0365a24954111f768f72"
    "0e77535af024bea2b2726c3bac992374755c3deacf09235e6865d456e651680d115a"
    "751a797225eaacdf9a513cf104526e1a32e5296e111a33ae581a63850837921df848"
    "9adfd41ea895b7cf3f5b2e45d538a6e4f032f590ccbb7daf5fa9c50adadee0799661"
    "4c3f957bda349e6c484fdf55970d1943ad7955a76671298b6d98b636b69ebde6bc94"
    "dbd93ac3393a6ae230130445b2d744189167854a5617be2393e7d8fbb5719a1b4754"
    "1ba466167e3e05a6c244f1301ee2035acf94dffc8adbde747d5cd85e35ead3acc372"
    "a59c4220e54bf63f9d80485f3de2518495c1d0f78c911d2da595911fd2a1989cf17"
    "cf3ded5f6c92dea64d675c555c11df92d6c517ca5d0d61a8962f43f76ec7e87596c"
    "8325ebf9ab0f8e6d2eca33c511ceac6980906ebd68c478665591dcecf788ec6ef34c"
    "fbe3fcc279c6147c5bf91cd43cdc9704236"
)

FIELD_94_STR = (
    "KqsHT+UrR1HKqb6+1db+Ofei+NtZr2+hbiBo3yKDL8w+8E3S5qF2IgEEe1fFQFyHRzl4"
    "iyHjHp+QsfeLbjJ6+DidTiKxm0ak2uYYa6QR4nAUdlZR"
)

JWT_ACCOUNT = {
    "uid": "7742406516",
    "password": "507D3250C779A4E73A74B66998E99DD4ED95A6133A07151FC0411A225C405ADD"
}

_token_cache = {}

HTTP_LIMITS  = httpx.Limits(max_keepalive_connections=20, max_connections=50)
HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_http_client = httpx.Client(limits=HTTP_LIMITS, timeout=HTTP_TIMEOUT)


# ============================================================
#  PROTOBUF ENCODER
# ============================================================
def encode_varint(n):
    if n < 0:
        return b''
    result = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)


def create_proto_field(field_num, value):
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        return encode_varint((field_num << 3) | 0) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode("utf-8") if isinstance(value, str) else value
        return encode_varint((field_num << 3) | 2) + encode_varint(len(encoded_val)) + encoded_val
    return b''


def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())


def parse_proto(data: bytes) -> dict:
    out = {}
    i, n = 0, len(data)
    while i < n:
        tag = 0
        shift = 0
        while i < n:
            b = data[i]
            i += 1
            tag |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        field_num = tag >> 3
        wire_type = tag & 7

        if wire_type == 0:
            val = 0
            shift = 0
            while i < n:
                b = data[i]
                i += 1
                val |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            out[field_num] = val
        elif wire_type == 2:
            length = 0
            shift = 0
            while i < n:
                b = data[i]
                i += 1
                length |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            payload = data[i:i + length]
            i += length
            try:
                text = payload.decode("utf-8")
                out[field_num] = text if text.isprintable() else payload
            except Exception:
                out[field_num] = payload
        elif wire_type == 1:
            i += 8
            out[field_num] = "<64>"
        elif wire_type == 5:
            i += 4
            out[field_num] = "<32>"
        else:
            break
    return out


# ============================================================
#  AES HELPERS
# ============================================================
def aes_encrypt_bytes(data_bytes):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data_bytes, AES.block_size))


def encrypt_api(plain_bytes):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(plain_bytes, AES.block_size))


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


def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split(".")
        if len(parts) < 2:
            return None
        pp = parts[1]
        pad_n = 4 - (len(pp) % 4)
        if pad_n != 4:
            pp += "=" * pad_n
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
    return bytes(
        ord(open_id[i]) ^ keystream[i % len(keystream)]
        for i in range(len(open_id))
    )


# ============================================================
#  TOKEN HELPERS (untuk /token & /info)
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
    if parsed:
        return parsed

    idx = 0
    while True:
        idx = raw.find(b"\x08", idx)
        if idx == -1:
            break
        parsed = try_parse_login_res(raw[idx:])
        if parsed:
            return parsed
        idx += 1

    jwt_marker = raw.find(b"eyJhbGciOiJIUzI1NiIs")
    if jwt_marker != -1:
        for i in range(jwt_marker - 1, max(jwt_marker - 300, -1), -1):
            if raw[i] == 0x42:
                parsed = try_parse_login_res(raw[i:])
                if parsed:
                    return parsed
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
    cached = _token_cache.get("main")
    if cached and cached.get("expires_at", 0) > time.time():
        return cached

    data = generate_jwt_token(JWT_ACCOUNT["uid"], JWT_ACCOUNT["password"])
    token_info = {
        "token": data["token"],
        "server_url": data.get("server_url") or "https://clientbp.ppmainecoonghj.com",
        "region": data.get("region") or REGION,
        "expires_at": time.time() + 25200,
    }
    _token_cache["main"] = token_info
    return token_info


# ============================================================
#  GUEST REGISTER — endpoint oauth guest:register
# ============================================================
def guest_register(session, password: str):
    reg_payload = json.dumps({
        "app_id": 100067,
        "client_type": 2,
        "password": password,
        "source": 2,
    }, separators=(',', ':'))

    signature = hmac.new(
        HEX_KEY.encode(), reg_payload.encode(), hashlib.sha256
    ).hexdigest()

    headers = {
        "User-Agent": random.choice(USER_AGENTS_REG),
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

    r = session.post(
        "https://100067.connect.garena.com/api/v2/oauth/guest:register",
        headers=headers, data=reg_payload, timeout=15
    )
    if r.status_code != 200:
        return None
    try:
        j = r.json()
    except Exception:
        return None
    if j.get("code") != 0:
        return None
    return j["data"]["uid"]


# ============================================================
#  TOKEN GRANT — endpoint oauth guest/token:grant
# ============================================================
def token_grant(session, uid, password: str):
    tok_payload = json.dumps({
        "client_id": 100067,
        "client_secret": HEX_KEY,
        "client_type": 2,
        "device_id": DEVICE_ID,
        "password": password,
        "response_type": "token",
        "uid": uid,
    }, separators=(',', ':'))

    headers = {
        "User-Agent": random.choice(USER_AGENTS_REG),
        "Connection": "Keep-Alive",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer",
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": DATADOME_COOKIE_TOK,
        "Host": "100067.connect.garena.com",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
    }

    r = session.post(
        "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
        headers=headers, data=tok_payload, timeout=15
    )
    if r.status_code != 200:
        return None, None
    try:
        j = r.json()
    except Exception:
        return None, None
    if j.get("code") != 0:
        return None, None
    return j["data"]["access_token"], j["data"]["open_id"]


# ============================================================
#  MAJOR REGISTER
# ============================================================
def major_register(session, name, access_token, open_id):
    fields = {
        1:  name,
        2:  access_token,
        3:  open_id,
        5:  102000007,
        6:  4,
        7:  1,
        13: 1,
        14: obfuscate_open_id(open_id),
        15: "en",
        16: 2,
        20: "2.133.8",
        21: 1,
        22: bytes.fromhex(FIELD_22_HEX),
    }
    encrypted = aes_encrypt_bytes(build_proto(fields))

    headers = {
        "Host": MAJOR_HOST,
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": str(int(time.time())),
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB55",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "Content-Length": str(len(encrypted)),
    }

    r = session.post(
        f"https://{MAJOR_HOST}/MajorRegister",
        data=encrypted, headers=headers, timeout=30, verify=False
    )
    if r.status_code != 200:
        return None
    return parse_proto(r.content)


# ============================================================
#  MAJOR LOGIN — build proto lengkap
# ============================================================
def build_major_login_fields(access_token, open_id):
    return {
        3:  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        4:  "free fire",
        5:  1,
        7:  "2.133.9",
        8:  "Android OS 10 / API-29 (QP1A.190711.020/1617006012)",
        9:  "Handheld",
        10: "Vi India",
        11: "WIFI",
        12: 1600,
        13: 720,
        14: "320",
        15: "ARM64 FP ASIMD AES | 2301 | 8",
        16: 2799,
        17: "PowerVR Rogue GE8320",
        18: "OpenGL ES 3.2 build 1.11@5425693",
        19: "Google|9f7d6b8b-b10c-454a-852d-06332cd498eb",
        20: "151.158.158.220",
        21: "en",
        22: access_token,
        23: "4",
        24: "Handheld",
        25: "realme RMX2189",
        26: "SG",
        29: "9892ee38a1d1e2fdbc069b357a754a8c885145af7d32eac25ef81b072595d123",
        30: 1,
        41: "Vi India",
        42: "WIFI",
        57: "1ac4b80ecf0478a44203bf8fac6120f5",
        60: 19799,
        61: 2536,
        62: 5056,
        64: 2768,
        65: 19999,
        66: 2536,
        67: 19799,
        73: 1,
        74: "/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/lib/arm64",
        76: 2,
        77: "38f4751a330688ab124c2c804cec90a5|"
            "/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/base.apk",
        78: 2,
        79: 2,
        81: "64",
        83: "2019118527",
        86: "OpenGLES3",
        87: 3071,
        88: 4,
        92: 67920,
        93: "android_max",
        94: FIELD_94_STR,
        95: 111107,
        96: '{"cur_rate":null,"support_etc2":true}',
        97: 1,
        98: 1,
        99: "4",
        100: "4",
        102: "",
        104: 83812,
        105: 1,
        106: "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|"
             "https://core-bs.ggpolarbear.com/live/ABHotUpdates/|"
             "a4332cb1c1a84e51dd77441e4856ed5a",
        107: "1.9393e7b8e3e8aeb",
    }


def major_login(session, access_token, open_id):
    plain = build_proto(build_major_login_fields(access_token, open_id))
    encrypted = aes_encrypt_bytes(plain)

    headers = {
        "Host": MAJOR_HOST,
        "User-Agent": random.choice(USER_AGENTS_REG),
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": "1789535859",
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB55",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
    }

    r = session.post(
        f"https://{MAJOR_HOST}/MajorLogin",
        headers=headers, data=encrypted, verify=False, timeout=15
    )

    if r.status_code == 200:
        idx = r.text.find("eyJ")
        if idx != -1:
            token = r.text[idx:]
            dot = token.find(".", token.find(".") + 1)
            if dot != -1:
                token = token[: dot + 44]
                payload = token.split(".")[1]
                payload += "=" * (4 - len(payload) % 4)
                try:
                    j = json.loads(base64.urlsafe_b64decode(payload))
                    acct = j.get("account_id") or j.get("external_id")
                    if acct:
                        return str(acct), token
                except Exception:
                    pass
    return None, None


# ============================================================
#  GENERATOR (flow utama) — register → grant → major register → major login
# ============================================================
def generate_one_account(max_retry=5):
    for attempt in range(max_retry):
        try:
            session = requests.Session()
            session.verify = False

            password = generate_password()

            # STEP 1 — GUEST REGISTER
            uid = guest_register(session, password)
            if not uid:
                time.sleep(0.3)
                continue

            time.sleep(0.05)

            # STEP 2 — TOKEN GRANT
            access_token, open_id = token_grant(session, uid, password)
            if not access_token or not open_id:
                time.sleep(0.3)
                continue

            time.sleep(0.05)

            # STEP 3 — MAJOR REGISTER
            name = generate_name(LANG)
            reg_result = major_register(session, name, access_token, open_id)

            if not reg_result:
                time.sleep(0.3)
                continue

            # cek hasil register: field 3 = real uid
            real_uid_from_reg = None
            if 3 in reg_result and isinstance(reg_result[3], int) and reg_result[3] > 0:
                real_uid_from_reg = str(reg_result[3])
            elif 9 in reg_result and isinstance(reg_result[9], str):
                # ditolak, coba ulang
                time.sleep(0.3)
                continue

            time.sleep(0.2)

            # STEP 4 — MAJOR LOGIN (ambil account_id dari JWT)
            real_uid, jwt_token = major_login(session, access_token, open_id)
            final_uid = real_uid or real_uid_from_reg

            if not final_uid or final_uid == "0":
                time.sleep(0.3)
                continue

            return {
                "account_id": str(final_uid),
                "uid": str(uid),
                "password": password,
                "name": name,
                "jwt_token": jwt_token or "",
                "region": REGION_NAME,
                "region_code": REGION,
                "lang": LANG,
            }

        except Exception:
            time.sleep(0.3)

    return None


# ============================================================
#  INFO ACCOUNT
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
                    "name": result["name"],
                    "region": result["region"],
                    "region_code": result["region_code"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            })
        else:
            return jsonify({"success": False, "message": "Failed to generate account. Please try again."}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500


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
