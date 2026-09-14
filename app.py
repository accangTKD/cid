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
from datetime import datetime
from flask import Flask, request, jsonify
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ============ KONFIGURASI TELEGRAM ============
BOT_TOKEN = "8965307683:AAGXwuIge4QKuYXtrkXhG4AahxDrynqi7SY"
OWNER_ID = 8660700322
CHANNEL_PROMO = "@dindingijo"
CONTACT = "@ricaricahamstee"
WATERMARK = f"CH TELE {CHANNEL_PROMO} Join pls"

# ============ KONFIGURASI API KEYS ============
API_KEYS = {
    "FREE_KEY_001": {"limit": 50, "used": 0, "last_reset_day": 0},
    "VIP_KEY_001": {"limit": 500, "used": 0, "last_reset_day": 0},
    "UNLIMITED_001": {"limit": 999999, "used": 0, "last_reset_day": 0}
}

# ============ KONFIGURASI GENERATOR ============
REGION_CHOICE = 1

REGION_MAP = {
    1: {"code": "ID", "name": "INDONESIA", "lang": "id"},
    2: {"code": "ME", "name": "MIDDLE EAST", "lang": "ar"},
    3: {"code": "IND", "name": "INDIA", "lang": "hi"},
    4: {"code": "TH", "name": "THAILAND", "lang": "th"},
    5: {"code": "VN", "name": "VIETNAM", "lang": "vi"},
    6: {"code": "BD", "name": "BANGLADESH", "lang": "bn"},
    7: {"code": "PK", "name": "PAKISTAN", "lang": "ur"},
    8: {"code": "TW", "name": "TAIWAN", "lang": "zh"},
    9: {"code": "CIS", "name": "RUSSIA", "lang": "ru"},
    10: {"code": "SAC", "name": "SPAIN", "lang": "es"},
    11: {"code": "BR", "name": "BRAZIL", "lang": "pt"}
}

SELECTED = REGION_MAP.get(REGION_CHOICE, REGION_MAP[1])
REGION = SELECTED["code"]
REGION_NAME = SELECTED["name"]
LANG = SELECTED["lang"]

NAME_PREFIX = "shuoi-"
PASS_PREFIX = "shu"

HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

WAF_UAS = [
    "GarenaMSDK/4.0.42(SM-A525F ;Android)",
    "GarenaMSDK/4.0.39(SM-A325M;Android 13;en;HK;)",
    "GarenaMSDK/4.0.38(Redmi Note 10;Android 12;en;ID;)",
    "GarenaMSDK/4.0.40(Poco X3;Android 11;en;SG;)",
    "GarenaMSDK/4.0.41(SM-S918B;Android 14;en;IN;)",
    "GarenaMSDK/4.0.42(OnePlus 11;Android 13;en;US;)",
    "GarenaMSDK/4.0.42(Xiaomi 14;Android 14;id;ID;)",
    "GarenaMSDK/4.0.40(Poco X5 Pro;Android 12;en;MY;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.41(OPPO Reno 10;Android 13;id;ID;)",
    "GarenaMSDK/4.0.42(Realme 11 Pro;Android 13;hi;IN;)",
    "GarenaMSDK/4.0.39(Vivo V27;Android 13;en;PH;)",
    "GarenaMSDK/4.0.40(Redmi Note 9;Android 10;ru;RU;)",
    "GarenaMSDK/4.0.41(Redmi 9;Android 10;id;ID;)",
]

# ============ DEVICE POOL ============
DEVICE_POOL = []
samsung = [f"SM-{c}{random.randint(100,999)}" for _ in range(100) for c in "AGNFMSJE"]
xiaomi = [f"{p} {random.randint(7,14)}" for _ in range(80) for p in ["Redmi Note", "Redmi", "Poco F", "Poco X", "Mi", "Xiaomi"]]
oppo = [f"OPPO {m}{random.randint(2,9999)}" for _ in range(60) for m in ["CPH", "Find X", "Reno", "A", "F"]]
vivo = [f"vivo {m}{random.randint(1,9999)}" for _ in range(60) for m in ["V", "X", "Y", "T", "S"]]
realme = [f"Realme {m}{random.randint(7,70)}" for _ in range(50) for m in ["", " Pro", " GT ", " C", " Narzo "]]
oneplus = [f"OnePlus {random.randint(8,14)}" for _ in range(40)]
moto = [f"Moto {m}{random.randint(10,100)}" for _ in range(40) for m in ["G", "E", "Edge "]]
other = ["ASUS_I005DA","ASUS Zenfone 8","Google Pixel 6","Sony Xperia 1 III"] * 20
all_models = samsung + xiaomi + oppo + vivo + realme + oneplus + moto + other
brands = ["samsung","xiaomi","oppo","vivo","realme","oneplus","motorola","asus","google","sony"]
android_versions = ["9","10","11","12","13","14","15"]

for _ in range(2000):
    DEVICE_POOL.append({
        "model": random.choice(all_models),
        "brand": random.choice(brands),
        "android": random.choice(android_versions)
    })

# ============ TELEGRAM FUNCTION ============
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
    
    payload = {
        "chat_id": OWNER_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ============ GENERATOR FUNCTIONS ============
def get_ua():
    return random.choice(WAF_UAS)

def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def get_headers():
    device = random.choice(DEVICE_POOL)
    return {
        "User-Agent": f"GarenaMSDK/4.0.39({device['model']};Android {device['android']};en;ID;)",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": f"v1 {random.randint(100000, 999999)}",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
    }

def get_headers_form():
    h = get_headers()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

def encode_varint(n):
    if n < 0: return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n: byte |= 0x80
        result.append(byte)
        if not n: break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, dict):
        nested = b''
        for k, v in value.items():
            nested += create_proto_field(k, v)
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(nested)) + nested
    elif isinstance(value, int):
        header = (field_num << 3) | 0
        return encode_varint(header) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def aes_encrypt_bytes(data_bytes):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data_bytes, AES.block_size))

def aes_encrypt(hex_data):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    data = bytes.fromhex(hex_data)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    plain = bytes.fromhex(plain_hex)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

def generate_cool_name():
    base = f"{NAME_PREFIX}{random.randint(10, 999)}"
    syms = ['~','!','@','#','$','%','^','&','*','-','_','+','=']
    p = random.randint(1, 3)
    if p == 1:
        s = random.choice(syms)
        return f"{s}{base}{s}"
    elif p == 2:
        s1, s2 = random.sample(syms, 2)
        return f"{s1}{s2}{base}"
    else:
        return base

def get_major_headers(region):
    host = "loginbp.common.ggbluefox.com" if region in ["ME", "TH"] else "loginbp.ggblueshark.com"
    return {
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
        "Host": host,
        "ReleaseVersion": "OB54",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
        "X-GA": "v1 1",
        "X-Unity-Version": "2018.4.11f1",
    }

def get_major_urls(region):
    base = "https://loginbp.common.ggbluefox.com" if region in ["ME", "TH"] else "https://loginbp.ggblueshark.com"
    return f"{base}/MajorRegister", f"{base}/MajorLogin"

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

def generate_one_account():
    session = requests.Session()
    session.verify = False

    for retry in range(3):
        try:
            password = f"{PASS_PREFIX}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
            name     = generate_cool_name()

            # ── STEP 1: GUEST REGISTER (HMAC Signature) ──
            url = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
            payload = {
                "app_id": 100067,
                "client_type": 2,
                "password": password,
                "source": 2,
            }
            body_json = json.dumps(payload, separators=(",", ":"))
            signature = hmac.new(HEX_KEY, body_json.encode("utf-8"), hashlib.sha256).hexdigest()

            headers = {
                "User-Agent": get_ua(),
                "Connection": "Keep-Alive",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Authorization": f"Signature {signature}",
                "Content-Type": "application/json; charset=utf-8",
                "Host": "100067.connect.garena.com",
                "X-Forwarded-For": get_random_ip(),
                "X-Real-IP": get_random_ip(),
            }

            resp = session.post(url, headers=headers, data=body_json, timeout=15)
            if resp.status_code != 200:
                time.sleep(0.5)
                continue
            try:
                res = resp.json()
            except Exception:
                time.sleep(0.5)
                continue
            if "data" not in res or "uid" not in res["data"]:
                time.sleep(0.5)
                continue
            uid = res["data"]["uid"]

            time.sleep(0.05)

            # ── STEP 2: GRANT TOKEN ──
            url = "https://100067.connect.garena.com/oauth/guest/token/grant"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": get_ua(),
                "X-Forwarded-For": get_random_ip(),
                "X-Real-IP": get_random_ip(),
            }
            resp2 = session.post(
                url, headers=headers,
                data={
                    "uid": uid,
                    "password": password,
                    "response_type": "token",
                    "client_type": "2",
                    "client_secret": HEX_KEY,
                    "client_id": "100067",
                },
                timeout=15,
            )
            if resp2.status_code != 200:
                time.sleep(0.5)
                continue
            try:
                j = resp2.json()
            except Exception:
                time.sleep(0.5)
                continue
            if "open_id" not in j:
                time.sleep(0.5)
                continue
            open_id      = j["open_id"]
            access_token = j["access_token"]

            time.sleep(0.05)

            # ── STEP 3: XOR OBFUSCATE open_id ──
            keystream = [
                48, 48, 48, 50, 48, 49, 55, 48,
                48, 48, 48, 48, 50, 48, 49, 55,
                48, 48, 48, 48, 48, 50, 48, 49,
                55, 48, 48, 48, 48, 48, 50, 48,
            ]
            encoded = "".join(chr(ord(open_id[i]) ^ keystream[i % len(keystream)]) for i in range(len(open_id)))
            hex_str = "".join(c if 32 <= ord(c) <= 126 else "\\u{:04x}".format(ord(c)) for c in encoded)
            field   = codecs.decode(hex_str, "unicode_escape").encode("latin1")

            # ── STEP 4: MAJOR REGISTER ──
            url_major, url_login = get_major_urls(REGION)

            proto_payload = {
                1:  name,
                2:  access_token,
                3:  open_id,
                5:  102000007,
                6:  4,
                7:  1,
                13: 1,
                14: field,
                15: LANG,
                16: 1,
                17: 1,
            }
            payload_bytes = build_proto(proto_payload)
            encrypted_payload = aes_encrypt_bytes(payload_bytes)

            session.post(
                url_major,
                headers=get_major_headers(REGION),
                data=encrypted_payload,
                timeout=15,
            )

            time.sleep(0.05)

            # ── STEP 5: MAJOR LOGIN ──
            payload_parts = [
                b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
                LANG.encode("ascii"),
                b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5',
            ]
            data = b"".join(payload_parts)

            ph_at  = b"afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390"
            ph_oid = b"1d8ec0240ede109973f3321b9354b44d"

            data = data.replace(ph_at, access_token.encode())
            data = data.replace(ph_oid, open_id.encode())

            d = encrypt_api(data.hex())
            enc_bytes = bytes.fromhex(d)

            response = session.post(
                url_login,
                headers=get_major_headers(REGION),
                data=enc_bytes,
                timeout=15,
            )

            account_id = "N/A"
            jwt_token  = ""

            if response.status_code == 200 and len(response.text) > 10:
                js = response.text.find("eyJ")
                if js != -1:
                    jwt_token = response.text[js:]
                    sd = jwt_token.find(".", jwt_token.find(".") + 1)
                    if sd != -1:
                        jwt_token = jwt_token[:sd + 44]
                    decoded = decode_jwt_payload(jwt_token)
                    if decoded:
                        account_id = decoded.get("account_id") or decoded.get("external_id") or "N/A"

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

# ============ API KEY FUNCTIONS ============
def check_api_key(api_key):
    current_day = datetime.now().day
    
    if api_key not in API_KEYS:
        return False, "Invalid API key", None
    
    key_data = API_KEYS[api_key]
    
    if key_data.get("last_reset_day", 0) != current_day:
        key_data["used"] = 0
        key_data["last_reset_day"] = current_day
    
    if key_data["used"] >= key_data["limit"]:
        return False, f"Daily limit reached! Used {key_data['used']}/{key_data['limit']}", key_data
    
    return True, "OK", key_data

def update_api_key_usage(api_key):
    if api_key in API_KEYS:
        API_KEYS[api_key]["used"] += 1

# ============ FLASK ROUTES ============
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({
        "success": True,
        "message": "API is running!",
        "endpoints": {
            "/generate": "Generate account (GET/POST with key parameter)",
            "/status": "Check API key status"
        },
        "watermark": WATERMARK
    })

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    api_key = None
    
    if request.method == 'GET':
        api_key = request.args.get('key') or request.args.get('api_key')
    else:
        api_key = request.json.get('key') if request.is_json else request.form.get('key')
    
    if not api_key:
        return jsonify({
            "success": False,
            "error": "API_KEY_REQUIRED",
            "message": "API key required! Use ?key=YOUR_KEY",
            "available_keys": list(API_KEYS.keys()),
            "example": "/generate?key=FREE_KEY_001",
            "watermark": WATERMARK
        }), 401
    
    valid, msg, key_data = check_api_key(api_key)
    
    if not valid:
        return jsonify({
            "success": False,
            "error": "LIMIT_REACHED",
            "message": msg,
            "limit": key_data.get("limit", 0) if key_data else 0,
            "used": key_data.get("used", 0) if key_data else 0,
            "remaining": max(0, key_data.get("limit", 0) - key_data.get("used", 0)) if key_data else 0,
            "watermark": WATERMARK
        }), 429
    
    try:
        result = generate_one_account()
        
        if result:
            update_api_key_usage(api_key)
            remaining = API_KEYS[api_key]["limit"] - API_KEYS[api_key]["used"]
            
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            send_to_owner(
                result["account_id"],
                result["uid"],
                result["password"],
                result["region"],
                api_key,
                client_ip
            )
            
            # UNTUK UNLIMITED_001: KASIH PASSWORD
            # UNTUK KEY LAIN: TANPA PASSWORD
            if api_key == "UNLIMITED_001":
                return jsonify({
                    "success": True,
                    "message": "Account generated successfully!",
                    "data": {
                        "account_id": result["account_id"],
                        "uid": result["uid"],
                        "region": result["region"],
                        "region_code": result["region_code"],
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "password": result["password"],
                    "usage": {
                        "used": API_KEYS[api_key]["used"],
                        "limit": API_KEYS[api_key]["limit"],
                        "remaining": remaining
                    },
                    "watermark": WATERMARK
                })
            else:
                return jsonify({
                    "success": True,
                    "message": "Account generated successfully!",
                    "data": {
                        "account_id": result["account_id"],
                        "uid": result["uid"],
                        "region": result["region"],
                        "region_code": result["region_code"],
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "note": f"maaf ya ak ga ikutin password nya, klo mau chat aja {CONTACT}",
                    "usage": {
                        "used": API_KEYS[api_key]["used"],
                        "limit": API_KEYS[api_key]["limit"],
                        "remaining": remaining
                    },
                    "watermark": WATERMARK
                })
        else:
            return jsonify({
                "success": False,
                "error": "GENERATION_FAILED",
                "message": "Failed to generate account. Please try again.",
                "watermark": WATERMARK
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": str(e),
            "watermark": WATERMARK
        }), 500

@app.route('/status', methods=['GET'])
def status():
    api_key = request.args.get('key') or request.args.get('api_key')
    
    if not api_key:
        return jsonify({
            "success": False,
            "message": "API key required",
            "watermark": WATERMARK
        }), 401
    
    valid, msg, key_data = check_api_key(api_key)
    
    if not valid or not key_data:
        return jsonify({
            "success": False,
            "message": msg,
            "watermark": WATERMARK
        }), 404
    
    return jsonify({
        "success": True,
        "api_key": api_key,
        "limit": key_data["limit"],
        "used": key_data["used"],
        "remaining": key_data["limit"] - key_data["used"],
        "reset_daily": True,
        "watermark": WATERMARK
    })

if __name__ == '__main__':
    app.run(debug=True)