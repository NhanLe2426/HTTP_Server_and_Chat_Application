#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
app.sampleapp
~~~~~~~~~~~~~~~~~

"""

import sys
import os
import importlib.util
import json
import time

from   daemon import AsynapRous
from    .auth import require_auth

# Global dictionary to act as the Tracker server memory
# Format: {"username": {"ip": "192.168.1.X", "port": 5000, "last_seen": "10:00:00"}}
active_peers = {}

# Global list to store actual P2P chat messages
chat_messages = []

app = AsynapRous()

@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))
    try:
        # Parse the incoming JSON payload safely
        data = json.loads(body) if isinstance(body, str) else body
        
        username = data.get("username")
        password = data.get("password")

        # Validate credentials (simulating a database check)
        if username == "admin" and password == "123":
            # Authentication successful
            data_response = {"message": "login success"}
        else:
            # Authentication failed due to invalid credentials
            data_response = {"error": "Unauthorized"}
            
        # Convert dictionary to JSON string and encode to bytes
        json_str = json.dumps(data_response)
        return json_str.encode("utf-8")
        
    except Exception as e:
        # Handle cases where the client sends a malformed JSON body
        data_response = {"error": "Invalid JSON format"}
        json_str = json.dumps(data_response)
        return json_str.encode("utf-8")
    #data = {"message": "Welcome to the RESTful TCP WebApp"}

    # Convert to JSON string
    #json_str = json.dumps(data)
    #return (json_str.encode("utf-8"))

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        data = {"received": message }
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))


@app.route('/hello', methods=['PUT'])
@require_auth
async def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] **ASYNC** Hello in {} to {}".format(headers, body))
    data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

# =====================================================================
# TRACKER SERVER APIs (INITIALIZATION PHASE - CLIENT-SERVER)
# =====================================================================

@app.route('/submit-info', methods=['POST'])
@require_auth
def submit_info(headers="guest", body="anonymous"):
    """
    Peer registration endpoint.
    When a new peer joins, it submits its IP and port to the centralized server.
    Updates the tracking list of active peers.
    """
    try:
        data = json.loads(body) if isinstance(body, str) else body
        username = data.get("username")
        peer_ip = data.get("ip")
        peer_port = data.get("port")

        # Validate that all required configuration data is present
        if not all([username, peer_ip, peer_port]):
            return json.dumps({"error": "Missing peer configuration data"}).encode("utf-8")

        # Update the tracker with the peer's listening address
        active_peers[username] = {
            "ip": peer_ip,
            "port": peer_port,
            "last_seen": time.strftime("%H:%M:%S")
        }

        # Return successful registration response
        return json.dumps({"status": "Registration successful", "peer": username}).encode("utf-8")
    except Exception as e:
        return json.dumps({"error": "Invalid payload format"}).encode("utf-8")


@app.route('/get-list', methods=['GET'])
@require_auth
def get_list(headers="guest", body="anonymous"):
    """
    Peer discovery endpoint.
    Peers request the current list of active peers from the server 
    to initiate direct P2P connections later.
    """
    # Return the dictionary of all active peers
    response_data = {
        "active_peers_count": len(active_peers),
        "peers": active_peers
    }
    return json.dumps(response_data).encode("utf-8")

# =====================================================================
# P2P COMMUNICATION APIs (PEER CHATTING PHASE)
# =====================================================================

@app.route('/send-peer', methods=['POST'])
def receive_direct_message(headers="guest", body="anonymous"):
    """
    Direct peer communication endpoint.
    Receives a direct message from another peer and stores it in the local chat history.
    Does not require @require_auth because the sender is another peer's server, 
    not a logged-in human user on a browser.
    """
    import json
    try:
        data = json.loads(body) if isinstance(body, str) else body
        
        # Extract sender info and message content
        sender_name = data.get("sender", "Unknown Peer")
        message_text = data.get("text", "")
        
        # Append to local chat UI memory
        new_msg = {
            "sender": f"[Direct] {sender_name}",
            "text": message_text,
            "timestamp": time.strftime("%H:%M:%S")
        }
        chat_messages.append(new_msg)
        
        return json.dumps({"status": "Direct message received"}).encode("utf-8")
    except Exception as e:
        return json.dumps({"error": "Failed to parse peer message"}).encode("utf-8")


@app.route('/broadcast-peer', methods=['POST'])
def receive_broadcast_message(headers="guest", body="anonymous"):
    """
    Broadcast connection endpoint.
    Receives a broadcast message from a peer and stores it in the local chat history.
    """
    import json
    try:
        data = json.loads(body) if isinstance(body, str) else body
        
        sender_name = data.get("sender", "Unknown Peer")
        message_text = data.get("text", "")
        
        new_msg = {
            "sender": f"[Broadcast] {sender_name}",
            "text": message_text,
            "timestamp": time.strftime("%H:%M:%S")
        }
        chat_messages.append(new_msg)
        
        return json.dumps({"status": "Broadcast message received"}).encode("utf-8")
    except Exception as e:
        return json.dumps({"error": "Failed to parse broadcast message"}).encode("utf-8")

# --- (Restore GET /chat/messages API to allow the UI to retrieve chat history) ---
@app.route('/chat/messages', methods=['GET'])
@require_auth
def get_ui_messages(headers="guest", body="anonymous"):
    """
    API endpoint for the local UI (chat.html) to retrieve the full chat history.
    """
    import json
    response_data = {"messages": chat_messages}
    return json.dumps(response_data).encode("utf-8")

import urllib.request
import urllib.error

@app.route('/chat/send', methods=['POST'])
@require_auth
def send_to_network(headers="guest", body="anonymous"):
    """
    Local UI endpoint to send a message.
    It saves the message locally and then acts as a P2P Client 
    to BROADCAST the payload to all other active peers in the network.
    """
    import json
    try:
        data = json.loads(body) if isinstance(body, str) else body
        sender_name = data.get("username", "Unknown")
        message_text = data.get("text", "")
        
        # 1. Save the message locally so the UI can render it
        new_msg = {
            "sender": f"[{sender_name}]",
            "text": message_text,
            "timestamp": time.strftime("%H:%M:%S")
        }
        chat_messages.append(new_msg)
        
        # 2. P2P Broadcast: Iterate over known peers and transmit
        # (Using the active_peers dictionary maintained by the Tracker)
        for peer, info in active_peers.items():
            # Prevent sending the message back to ourselves
            if peer == sender_name:
                continue
            
            # Construct the destination URL of the remote peer
            target_url = f"http://{info['ip']}:{info['port']}/broadcast-peer"
            payload = json.dumps({"sender": sender_name, "text": message_text}).encode('utf-8')
            
            # Comply with strict rules: Utilize standard Python library (urllib)
            req = urllib.request.Request(
                target_url, 
                data=payload, 
                headers={'Content-Type': 'application/json'}
            )
            
            try:
                # Transmit the packet with a timeout to prevent blocking the event loop
                urllib.request.urlopen(req, timeout=2)
                print(f"[P2P Success] Transmitted to {peer} at {target_url}")
            except Exception as e:
                # Handle cases where the peer is offline or unreachable
                print(f"[P2P Error] Could not reach {peer} at {target_url}: {e}")

        return json.dumps({"status": "Message broadcasted"}).encode("utf-8")
        
    except Exception as e:
        return json.dumps({"error": "Failed to broadcast message"}).encode("utf-8")

# =====================================================================
# STATIC FILE SERVING ROUTES
# =====================================================================

@app.route('/login.html', methods=['GET'])
def serve_login_page(headers="guest", body="anonymous"):
    """
    Reads and serves the static login.html file.
    Returns a tuple containing: (content bytes, HTTP status code, MIME type).
    """
    try:
        with open("www/login.html", "rb") as file:
            content = file.read()
        # Return the 3-element tuple to instruct the framework explicitly
        return content, 200, "text/html; charset=utf-8"
    except FileNotFoundError:
        return b"404 File Not Found", 404, "text/plain"

@app.route('/chat.html', methods=['GET'])
def serve_chat_page(headers="guest", body="anonymous"):
    """
    Reads and serves the static chat.html file.
    """
    try:
        with open("www/chat.html", "rb") as file:
            content = file.read()
        return content, 200, "text/html; charset=utf-8"
    except FileNotFoundError:
        return b"404 File Not Found", 404, "text/plain"

@app.route('/css/styles.css', methods=['GET'])
def serve_css(headers="guest", body="anonymous"):
    """
    Reads and serves the stylesheet for frontend rendering.
    """
    try:
        with open("static/css/styles.css", "rb") as file:
            content = file.read()
        return content, 200, "text/css; charset=utf-8"
    except FileNotFoundError:
        return b"404 File Not Found", 404, "text/plain"