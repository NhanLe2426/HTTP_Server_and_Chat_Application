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

from concurrent.futures import ThreadPoolExecutor
from daemon.asynaprous  import AsynapRous
from        auth        import require_auth

MY_NAME = sys.argv[1] if len(sys.argv) > 1 else "Nhan"
MY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
MY_IP = "127.0.0.1"                            # Put your IP here: 
TRACKER_URL = "http://127.0.0.1:9000"          # http://<your IP>:9000

app = AsynapRous()
# Initialize a Thread Pool to limit maximum concurrent P2P sending tasks to 20
executor = ThreadPoolExecutor(max_workers=20)
CHANNELS = {"Global": []} 
JOINED_CHANNELS = ["Global"]  # Track which group channels this node has subscribed to
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

def send_p2p_worker(target_ip, target_port, sender, text, endpoint="/broadcast-peer", channel="Global"):
    """
    Worker thread to send HTTP POST request to another peer.
    The endpoint will be dynamically set to /broadcast-peer or /send-peer.
    """
    url = f"http://{target_ip}:{target_port}{endpoint}"
    # Removed 'target' from payload to keep it clean for the spec
    payload = json.dumps({"from": sender, "msg": text, "channel": channel}).encode('utf-8')
    try:
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
# CORE APIs
# =================================================================
@app.route('/login', methods=['POST'])
async def api_login(headers=None, body=None):
    """
    Handle user login and issue a session cookie.
    Strictly enforce that the user logging in matches the node's owner (MY_NAME)
    to prevent P2P identity mismatch and channel duplication.
    """
    try:
        # Extract username from the request body
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Verify credentials
        if username == MY_NAME and username in VALID_USERS and VALID_USERS[username] == password:
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

@app.route('/add-list', methods=['POST'])
@require_auth
def api_add_list(headers=None, body=None):
    """
    Allows user to subscribe to a new group channel.
    """
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        channel_name = data.get('channel', '').strip()
        
        if channel_name and channel_name not in JOINED_CHANNELS:
            JOINED_CHANNELS.append(channel_name)
            if channel_name not in CHANNELS:
                CHANNELS[channel_name] = []
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/get-list', methods=['GET'])
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
    
    # Filter out our own name from the active peers list
    peer_list = [p for p in ACTIVE_PEERS.keys() if p != MY_NAME]
    return {"channels": channel_info, "peers": peer_list}

@app.route('/get-messages', methods=['POST'])
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

@app.route('/api/send-message', methods=['POST'])
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
        
        # Split the cookie string into individual pairs
        for p in cookie_str.split(';'):
            # Remove leading/trailing whitespaces for accurate comparison
            clean_p = p.strip() 
            
            # Use startswith() instead of 'in' to ensure we only catch 
            # the exact 'session=' key, avoiding 'session_5001=' or others.
            if clean_p.startswith('session='):
                # Extract the username assigned during the login phase
                true_sender = clean_p.split('session=')[1].strip()
                break
                
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Ensure the channel exists locally before appending
        if target_channel not in CHANNELS:
            CHANNELS[target_channel] = []
            
        CHANNELS[target_channel].append({"from": true_sender, "msg": text, "time": now})
        
        if target_channel == "Global" or target_channel.startswith("#"):
            # Broadcast to all peers, but tag it with the specific channel name
            for name, info in ACTIVE_PEERS.items():
                if name != MY_NAME:
                    # threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], true_sender, text, "/broadcast-peer", target_channel)).start()
                    # IMPLEMENTED: ThreadPoolExecutor instead of raw threads
                    executor.submit(send_p2p_worker, info['ip'], info['port'], true_sender, text, "/broadcast-peer", target_channel)
        else:
            # Unicast: Send directly to the specific peer
            if target_channel in ACTIVE_PEERS:
                info = ACTIVE_PEERS[target_channel]
                # threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], true_sender, text, "/send-peer", target_channel)).start()
                executor.submit(send_p2p_worker, info['ip'], info['port'], true_sender, text, "/send-peer", target_channel)
                
        return {"status": "ok"}
    except Exception as e:
        print(f"[!] Send API Error: {e}")
        return {"status": "error"}

@app.route('/broadcast-peer', methods=['POST'])
def api_broadcast_peer(headers=None, body=None):
    """Handle incoming global broadcast messages."""
    try:
        # Safely handle both bytes and str body payloads
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        
        sender = data['from']
        msg = data['msg']
        channel = data.get('channel', 'Global')
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        # PUB/SUB FILTER: Only accept message if we are subscribed to this channel
        if channel in JOINED_CHANNELS:
            if channel not in CHANNELS:
                CHANNELS[channel] = []
            CHANNELS[channel].append({"from": sender, "msg": msg, "time": now})
            
        return {"status": "ok"}
    except Exception as e:
        # Print the error to the terminal for debugging
        print(f"[!] Broadcast Receive Error: {e}")
        return {"status": "error"}

@app.route('/send-peer', methods=['POST'])
def api_send_peer(headers=None, body=None):
    """Handle incoming private direct messages."""
    try:
        # Safely handle both bytes and str body payloads
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        
        sender = data['from']
        msg = data['msg']
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        if sender not in CHANNELS:
            CHANNELS[sender] = []
            
        CHANNELS[sender].append({"from": sender, "msg": msg, "time": now})
        return {"status": "ok"}
    except Exception as e:
        # Print the error to the terminal for debugging
        print(f"[!] Send-Peer Receive Error: {e}")
        return {"status": "error"}

@app.route('/connect-peer', methods=['GET'])
@require_auth
def api_connect_peer(headers=None, body=None):
    """Force a peer list refresh from the Tracker."""
    update_peers()
    return {"status": "ok", "message": "Synchronized with Tracker"}

@app.route('/api/create-group', methods=['POST'])
@require_auth
def api_create_group(headers=None, body=None):
    """UI Endpoint: Create a channel and invite selected peers."""
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        channel = data.get('channel', '').strip()
        peers = data.get('peers', []) # List of selected peers

        # 1. Join locally
        if channel and channel not in JOINED_CHANNELS:
            JOINED_CHANNELS.append(channel)
            if channel not in CHANNELS:
                CHANNELS[channel] = []
        
        # 2. Extract true sender from cookie
        true_sender = "Unknown"
        cookie_str = headers.get('cookie', headers.get('Cookie', ''))
        for p in cookie_str.split(';'):
            if p.strip().startswith('session='):
                true_sender = p.split('session=')[1].strip()
                break

        # 3. Send P2P invitation to selected peers
        for p in peers:
            if p in ACTIVE_PEERS:
                info = ACTIVE_PEERS[p]
                # Send to the new /invite-peer endpoint
                # threading.Thread(target=send_p2p_worker, args=(info['ip'], info['port'], true_sender, f"Invited to {channel}", "/invite-peer", channel)).start()
                executor.submit(send_p2p_worker, info['ip'], info['port'], true_sender, f"Invited to {channel}", "/invite-peer", channel)
        
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error"}

@app.route('/invite-peer', methods=['POST'])
def api_invite_peer(headers=None, body=None):
    """P2P Endpoint: Handle incoming group invitations."""
    try:
        body_data = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_data)
        channel = data.get('channel')
        
        # Force join the channel upon receiving invite
        if channel and channel.startswith("#") and channel not in JOINED_CHANNELS:
            JOINED_CHANNELS.append(channel)
            if channel not in CHANNELS:
                CHANNELS[channel] = []
        return {"status": "ok"}
    except Exception as e:
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