import sys
import os
import json
import time
import asyncio
import urllib.request
import threading
import datetime

# Add parent directory to path to locate 'daemon'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from daemon.asynaprous  import AsynapRous
from        auth        import require_auth

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Nhan"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"                            # Put your IP here: 192.168.135.47
TRACKER_URL = "http://127.0.0.1:9000"          # http://192.168.135.47:9000

app = AsynapRous()
CHANNELS = {"Global": []} 
ACTIVE_PEERS = {}

VALID_USERS = {
    "Nhan": "123",
    "Nghi": "123",
    "Khanh": "123",
    "Hien": "123",
    "An": "123"
}

def register_to_tracker():
    url = f"{TRACKER_URL}/submit-info"
    payload = json.dumps({"username": MY_NAME, "ip": MY_IP, "port": MY_PORT}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        # Increased timeout for LAN environments
        urllib.request.urlopen(req, timeout=3)
        print(f"[*] {MY_NAME} successfully registered with Tracker.")
    except Exception as e:
        # Print the exact error if registration fails
        print(f"[!] Tracker Registration Error: {e}")

def update_peers():
    """
    Fetch the latest active peer list from the central Tracker.
    Dynamically create new private chat channels for newly discovered peers.
    """
    global ACTIVE_PEERS, CHANNELS
    try:
        url = f"{TRACKER_URL}/get-list"
        # Increased timeout for LAN environments
        with urllib.request.urlopen(url, timeout=2) as response:
            new_peers = json.loads(response.read().decode('utf-8'))
            # SELF-HEALING MECHANISM
            # Check if the current node is missing from the central tracker
            if MY_NAME not in new_peers:
                print("[!] Tracker seems to have restarted. Re-registering...")
                register_to_tracker()
            else:
                # Only update the active list if the data is valid
                ACTIVE_PEERS = new_peers

                # STEP 2 UPGRADE: DYNAMIC CHANNEL CREATION
                # Loop through all online peers provided by the Tracker
                for peer_name in new_peers.keys():
                    # Do not create a private channel for ourselves
                    # Only create if the channel does not already exist
                    if peer_name != MY_NAME and peer_name not in CHANNELS:
                        CHANNELS[peer_name] = []
                        print(f"[*] Created new private channel for: {peer_name}")
    except Exception as e:
        # Silently fail in background to avoid spamming the console, 
        # but you can uncomment the next line for debugging
        # print(f"[!] Fetch Peers Error: {e}")
        pass

def send_p2p_worker(target_ip, target_port, sender, text, target="Global"):
    """
    Worker thread to send HTTP POST request to another peer.
    Includes the 'target' channel (Global or Private) in the payload.
    """
    url = f"http://{target_ip}:{target_port}/api/receive"
    payload = json.dumps({"from": sender, "target": target, "msg": text}).encode('utf-8')
    try:
        # Method must be 'POST', headers must be explicitly declared
        req = urllib.request.Request(url, data=payload, method='POST', headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        print(f"[!] P2P Delivery Failed to {target_ip}: {e}")

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
async def api_login(headers=None, body=None):
    """
    Handle user login and issue a session cookie.
    """
    try:
        # Extract username from the request body
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Verify credentials
        if username in VALID_USERS and VALID_USERS[username] == password:
            return {
                "status": "ok", 
                "message": "Login Successful",
                "session": username
            }
        else:
            # Block access if credentials do not match
            return {"status": "error", "message": "Invalid username or password"}
            
    except Exception as e:
        print(f"[!] Login API Error: {e}")
    
    return {"status": "error", "message": "Invalid request"}

@app.route('/api/channels', methods=['GET'])
@require_auth
def api_get_channels(headers=None, body=None):
    """
    Return the list of all available chat channels (Global + Private Peers).
    This enables the Frontend UI to dynamically render the left sidebar.
    """
    # Verify authentication cookie
    # The @require_auth decorator handles it automatically.
        
    # Extract all channel names (keys) from the CHANNELS dictionary
    channel_info = {}
    
    # Iterate through all existing channels and count their messages
    for ch_name, msgs in CHANNELS.items():
        channel_info[ch_name] = len(msgs)
        
    return {"channels": channel_info}

@app.route('/chat/messages', methods=['POST'])
@require_auth
def api_get_msg(headers=None, body=None):
    """
    Retrieve messages for a specific channel requested by the Frontend.
    """
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data) if body_data else {}
        
        # Default to Global if no channel is specified
        target_channel = data.get('channel', 'Global')
        
        formatted = []
        if target_channel in CHANNELS:
            for m in CHANNELS[target_channel]:
                formatted.append({
                    "timestamp": m.get("time", ""),
                    "sender": m["from"],
                    "text": m["msg"]
                })
        return {"messages": formatted}
    except Exception as e:
        print(f"[!] Get Messages Error: {e}")
        return {"error": "Invalid request"}

@app.route('/chat/send', methods=['POST'])
@require_auth
def api_send(headers=None, body=None):
    """
    Route messages to the appropriate channel (Global broadcast or Private direct).
    """
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        
        text = data.get('text', '')
        # Determine the destination channel (default to Global if not provided)
        target_channel = data.get('channel', 'Global')
        
        # Extract verified identity from Cookie
        cookie_str = headers.get('cookie', headers.get('Cookie', ''))
        true_sender = "Unknown"
        for p in cookie_str.split(';'):
            if 'session=' in p:
                true_sender = p.split('session=')[1].strip()
                break
                
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Ensure the channel exists locally before appending
        if target_channel not in CHANNELS:
            CHANNELS[target_channel] = []
            
        CHANNELS[target_channel].append({"from": true_sender, "msg": text, "time": now})
        
        # ROUTING LOGIC
        if target_channel == "Global":
            # Broadcast to all peers
            for name, info in ACTIVE_PEERS.items():
                if name != MY_NAME:
                    threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], true_sender, text, "Global")).start()
        else:
            # Unicast: Send directly to the specific peer
            if target_channel in ACTIVE_PEERS:
                info = ACTIVE_PEERS[target_channel]
                threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], true_sender, text, target_channel)).start()
                
        return {"status": "ok"}
    except Exception as e:
        print(f"[!] Send API Error: {e}")
        return {"status": "error"}

@app.route('/api/receive', methods=['POST'])
def api_receive(headers=None, body=None):
    """
    Receive incoming P2P messages and route them to the correct local channel.
    """
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        
        sender = data['from']
        target = data.get('target', 'Global')
        msg = data['msg']
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Determine the correct local folder to store the message
        if target == "Global":
            save_channel = "Global"
        else:
            # If it is a private message sent to me, save it in the sender's folder
            save_channel = sender
            
        if save_channel not in CHANNELS:
            CHANNELS[save_channel] = []
            
        CHANNELS[save_channel].append({"from": sender, "msg": msg, "time": now})
        return {"status": "ok"}
    except Exception as e:
        print(f"[!] Receive API Error: {e}")
        return {"status": "error"}

def tracker_sync_worker():
    """
    Background daemon that periodically synchronizes the peer list
    with the central tracker every 3 seconds.
    """
    while True:
        update_peers()
        time.sleep(3)

# =================================================================
# NON-BLOCKING DEMONSTRATION ROUTE
# =================================================================
@app.route('/api/slow-task', methods=['GET'])
async def api_slow_task(headers=None, body=None):
    # Simulate a heavy database query or slow network calculation that takes 30 seconds
    print("[*] Received a heavy request. Processing for 30 seconds...")
    await asyncio.sleep(30) 
    print("[*] Heavy request completed!")
    return {"status": "ok", "message": "Heavy task finished after 30 seconds"}

if __name__ == "__main__":
    app.prepare_address("0.0.0.0", MY_PORT)
    register_to_tracker()
    print(f"[*] P2P Node {MY_NAME} is active at http://{MY_IP}:{MY_PORT}/login.html")
    # START THE BACKGROUND SYNC DAEMON
    threading.Thread(target=tracker_sync_worker, daemon=True).start()
    app.run()