import json
from daemon.asynaprous import AsynapRous

app = AsynapRous()
REGISTERED_PEERS = {}

@app.route('/submit-info', methods=['POST'])
def submit_info(headers=None, body=None):
    """API for peers to register their IP and Port"""
    try:
        body_str = body.decode('utf-8') if isinstance(body, bytes) else body
        data = json.loads(body_str)
        
        username = data.get('username')
        ip = data.get('ip')
        port = data.get('port')
        
        if username and ip and port:
            REGISTERED_PEERS[username] = {"ip": ip, "port": port}
            print(f"[+] Peer Registered: {username} at {ip}:{port}")
            return b'{"status": "success"}'
    except Exception as e:
        print(f"[-] Registration Error: {e}")
    return b'{"status": "error"}'

@app.route('/get-list', methods=['GET'])
def get_list(headers=None, body=None):
    """API for peers to fetch the active directory"""
    return json.dumps(REGISTERED_PEERS).encode('utf-8')

if __name__ == "__main__":
    app.prepare_address(ip="0.0.0.0", port=9000)
    print("[*] P2P Tracker is officially running on port 9000...")
    app.run()