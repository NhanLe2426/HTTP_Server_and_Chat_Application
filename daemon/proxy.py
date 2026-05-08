#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}

# Global dictionary to track the last used server index for Round-Robin load balancing
ROUND_ROBIN_STATE = {}


def forward_request(host, port, request):
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 404 Not Found response.
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Optional Enhancement: Set timeout to prevent proxy from hanging if backend is slow
    backend.settimeout(2.0)

    try:
        backend.connect((host, port))
        backend.sendall(request.encode())
        response = b""
        while True:
            try:
                chunk = backend.recv(4096)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                print(f"[Proxy] Warning: Read timeout from backend {host}:{port}")
                break
        return response
    except socket.error as e:
      print("Socket error: {}".format(e))
      return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
    finally:
        # Ensure the socket is properly closed after forwarding
        backend.close()


def resolve_routing_policy(hostname, routes):
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server.
    :params routes (dict): dictionary mapping hostnames and location.
    """
    global ROUND_ROBIN_STATE

    print(f"[Proxy] Resolving hostname: {hostname}")
    
    # Check if hostname exists in routes
    if hostname not in routes:
        print(f"[Proxy] Hostname '{hostname}' not in routes, cannot resolve")
        return '', ''
    
    proxy_map, policy = routes.get(hostname)
    print(f"[Proxy] proxy_map: {proxy_map}, policy: {policy}")

    proxy_host = ''
    proxy_port = '9000'
    
    # proxy_map should always be a list now
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print(f"[Proxy] Empty backend list for hostname '{hostname}'")
            return '', ''
        elif len(proxy_map) == 1:
            # Single backend
            proxy_host, proxy_port = proxy_map[0].split(":", 1)
            print(f"[Proxy] Single backend selected: {proxy_host}:{proxy_port}")
        else:
            # Multiple backends - apply load balancing policy
            if policy in ['round-robin', 'round']:
                if hostname not in ROUND_ROBIN_STATE:
                    ROUND_ROBIN_STATE[hostname] = 0

                # Get the current index position
                current_idx = ROUND_ROBIN_STATE[hostname]
                # Choose server based on the current index
                target = proxy_map[current_idx]
                proxy_host, proxy_port = target.split(":", 1)

                print(f"[Load Balancer] Round-Robin selected server: {target} (index {current_idx})")
                
                # Update the state for the next incoming request
                ROUND_ROBIN_STATE[hostname] = (current_idx + 1) % len(proxy_map)
            else:
                # Fallback to the first server if policy is unknown
                proxy_host, proxy_port = proxy_map[0].split(":", 1)
                print(f"[Proxy] Unknown policy '{policy}', using first backend: {proxy_host}:{proxy_port}")
    else:
        print(f"[Proxy] ERROR: proxy_map is not a list, it's {type(proxy_map)}")
        return '', ''

    return proxy_host, proxy_port

def handle_client(ip, port, conn, addr, routes):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition,it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """

    # request = conn.recv(1024).decode()
    # Kept the decode method to process the string request
    request = conn.recv(4096).decode('utf-8', errors='ignore')
    if not request:
        return

    # Extract hostname
    hostname = ""
    hostname_only = ""
    for line in request.splitlines():
        if line.lower().startswith('host:'):
            raw_host = line.split(':', 1)[1].strip()
            # Extract just the hostname part (without port)
            hostname_only = raw_host.split(':')[0] if ':' in raw_host else raw_host
            # Keep the full host value for matching
            hostname = raw_host
            break

    print("[Proxy] {} at Host: {} (hostname_only: {})".format(addr, hostname, hostname_only))

    # Try to find a route: first with full hostname, then without port
    if hostname not in routes:
        if hostname_only in routes:
            hostname = hostname_only
        else:
            # If no match found, try localhost
            if "localhost" in routes:
                hostname = "localhost"
            elif "127.0.0.1" in routes:
                hostname = "127.0.0.1"

    # Resolve the matching destination in routes and need conver port
    # to integer value
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    try:
        resolved_port = int(resolved_port)
    except ValueError:
        print("Not a valid integer")

    if resolved_host:
        print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname,resolved_host, resolved_port))
        response = forward_request(resolved_host, resolved_port, request)        
    else:
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
    conn.sendall(response)
    conn.close()

def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 

    The process dinds the proxy server to the specified IP and port.
    In each incomping connection, it accepts the connections and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.

    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow port to be reused immediately after restart
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print("[Proxy] Listening on IP {} port {}".format(ip,port))
        while True:
            conn, addr = proxy.accept()
            #
            #  TODO: implement the step of the client incomping connection
            #        using multi-thread programming with the
            #        provided handle_client routine
            #
            proxy_thread = threading.Thread(
                target=handle_client,
                args=(ip, port, conn, addr, routes)
            )
            proxy_thread.daemon = True
            proxy_thread.start()
    except socket.error as e:
        print("Socket error: {}".format(e))

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
