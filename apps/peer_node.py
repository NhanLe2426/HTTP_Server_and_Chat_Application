import sys
import os
import json
import urllib.request
import threading
import datetime

# Add parent directory to path to locate 'daemon'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from daemon.asynaprous import AsynapRous

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Ken"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"
TRACKER_URL = "http://127.0.0.1:9000"

app = AsynapRous()
CHANNELS = {"Global": []} 
ACTIVE_PEERS = {}

def register_to_tracker():
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps({"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=1)
        print(f"[*] {MY_NAME} successfully registered with Tracker.")
    except: pass

def update_peers():
    global ACTIVE_PEERS
    try:
        url = f"{TRACKER_URL}/get-list"
        with urllib.request.urlopen(url, timeout=0.5) as response:
            ACTIVE_PEERS = json.loads(response.read().decode('utf-8'))
    except: pass

def send_p2p_worker(target_ip, target_port, sender, text):
    url = f"http://{target_ip}:{target_port}/api/receive"
    payload = json.dumps({"from": sender, "msg": text}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        urllib.request.urlopen(req, timeout=2)
    except: pass

# =================================================================
# STATIC FILE SERVERS (Fixed TypeError causing ERR_EMPTY_RESPONSE)
# =================================================================
def get_static_file(filename):
    try:
        # Files must be inside a folder named 'www' at the root level
        file_path = os.path.join(os.path.dirname(current_dir), "www", filename)
        with open(file_path, "rb") as f:
            return f.read()
    except:
        return b"<h1>404 File Not Found</h1>"

@app.route('/', methods=['GET'])
def serve_root(headers=None, body=None): return get_static_file("login.html")

@app.route('/index.html', methods=['GET'])
def serve_index(headers=None, body=None): return get_static_file("index.html")

@app.route('/login.html', methods=['GET'])
def serve_login(headers=None, body=None): return get_static_file("login.html")

@app.route('/chat.html', methods=['GET'])
def serve_chat(headers=None, body=None): return get_static_file("chat.html")

# =================================================================
# CORE APIs (Aligned with your HTML files)
# =================================================================
@app.route('/login', methods=['POST'])
def api_login(headers=None, body=None):
    # Accept any login to let frontend handle user session via localStorage
    return {"status": "ok", "message": "Login Successful"}

@app.route('/chat/messages', methods=['GET'])
def api_get_msg(headers=None, body=None):
    update_peers()
    # Format messages EXACTLY as required by chat.html's JavaScript
    formatted = []
    for m in CHANNELS["Global"]:
        formatted.append({
            "timestamp": m.get("time", ""),
            "sender": m["from"],
            "text": m["msg"]
        })
    return {"messages": formatted}

@app.route('/chat/send', methods=['POST'])
def api_send(headers=None, body=None):
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        text = data.get('text', '')
        # Get sender name from payload or default to current Node name
        sender = data.get('username', MY_NAME)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        CHANNELS["Global"].append({"from": sender, "msg": text, "time": now})
        
        # Broadcast to all other discovered peers
        for name, info in ACTIVE_PEERS.items():
            if name != MY_NAME:
                threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], sender, text)).start()
        return {"status": "ok"}
    except:
        return {"status": "error"}

@app.route('/api/receive', methods=['POST'])
def api_receive(headers=None, body=None):
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        CHANNELS["Global"].append({"from": data['from'], "msg": data['msg'], "time": now})
        return {"status": "ok"}
    except: return {"status": "error"}

if __name__ == "__main__":
    app.prepare_address(MY_IP, MY_PORT)
    register_to_tracker()
    print(f"[*] P2P Node {MY_NAME} is active at http://{MY_IP}:{MY_PORT}/login.html")
    app.run()