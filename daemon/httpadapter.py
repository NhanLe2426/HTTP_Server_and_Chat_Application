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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

import asyncio
import inspect
import json

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def _process_hook_result(self, hook_result, req, resp):
        """
        Helper method to format the application's return value into bytes.
        Intercepts session cookies for the login route to set headers properly.
        """
        body_bytes = b""
        if isinstance(hook_result, dict):
            body_bytes = json.dumps(hook_result).encode("utf-8")
        elif isinstance(hook_result, str):
            body_bytes =  hook_result.encode("utf-8")
        elif isinstance(hook_result, bytes):
            body_bytes = hook_result

        # Intercept logic: Extract session ID from login response and set it as a Cookie
        if req.path == "/login" and req.method == "POST":
            try:
                data = json.loads(body_bytes.decode('utf-8'))
                session_id = data.get("session")
                if session_id:
                    resp.set_cookie("session", session_id)
                    # Remove session from body response for security
                    del data["session"]
                    body_bytes = json.dumps(data).encode("utf-8")
            except Exception:
                pass

        return body_bytes

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        msg = conn.recv(1024).decode()
        req.prepare(msg, routes)
        print("[HttpAdapter] Invoke handle_client connection {}".format(addr))

        # Handle request hook
        if req.hook:
            #
            # TODO: handle for App hook here
            #
            #response = ""
            import uuid
            # Execute the API handler (e.g., login route) to get the raw result
            hook_result = req.hook(headers=req.headers, body=req.body)
            
            # Check if the hook_result is a Response object
            if isinstance(hook_result, Response):
                # If it's already a Response object, use it directly
                print("[HttpAdapter] Hook returned Response object, using it directly")
                response = hook_result.build_response_header(req) + hook_result._content
            else:
                # Format the hook result to ensure safe byte encoding and dictionary extraction
                data_dict = {}
                if isinstance(hook_result, dict):
                    data_dict = hook_result
                    body_bytes = json.dumps(hook_result).encode('utf-8')

                    if data_dict.get("error") and "401" in str(data_dict.get("error")):
                        resp.status_code = 401
                        resp.reason = "Unauthorized"
                elif isinstance(hook_result, str):
                    body_bytes = hook_result.encode('utf-8')
                    try:
                        data_dict = json.loads(hook_result)
                    except Exception:
                        pass
                else:
                    body_bytes = hook_result if isinstance(hook_result, bytes) else b""

                # --- SESSION INTERCEPTION FOR AUTHENTICATION (TASK 2) ---
                if req.path == "/login" and req.method == "POST":
                    try:
                        # Extract existing session or auto-generate a new unique session ID
                        session_id = data_dict.get("session", uuid.uuid4().hex)
                        
                        # Inject the session directly into the cookies dictionary
                        resp.cookies["session"] = session_id
                        
                        # Log to terminal for debugging and verification
                        print(f"[HttpAdapter] Successfully injected session cookie: {session_id}")
                    except Exception as e:
                        print(f"[HttpAdapter] Session generation error: {e}")
                # --------------------------------------------------------

                # Construct the HTTP payload (Headers + Body) and assign to response
                response = resp.build_response(req, envelop_content=body_bytes)
        else:
            # Return 404 if no matching route is found
            response = resp.build_notfound()
            
        #print("[HttpAdapter] Response content {}".format(response))
        conn.sendall(response)
        conn.close()

    async def handle_client_coroutine(self, reader, writer):
        """
        Handle an incoming client connection using stream reader writer asynchronously.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """
        addr = writer.get_extra_info("peername")
        print("[HttpAdapter] Invoke handle_client_coroutine connection {})".format(addr))
        
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # TODO Handle the request asynchronously
        try:
            # Read the raw request data asynchronously
            msg = await reader.read(4096)
            if not msg:
                print("[HttpAdapter] Empty payload received from {}".format(addr))
                return
            
            # Decoding the raw request data and preparing the Request object
            req.prepare(msg.decode("utf-8", errors="ignore"), routes=self.routes)

            # Handle request hook
            if req.hook:
                #
                # TODO: handle for App hook here
                #
                import uuid
                # Prepare exact arguments to pass to the API handler
                kwargs = {"headers": req.headers, "body": req.body}

                # Dynamically execute the API handler (async or sync)
                if inspect.iscoroutinefunction(req.hook):
                    hook_result = await req.hook(**kwargs)
                else:
                    hook_result = req.hook(**kwargs)

                # Format the hook result to ensure safe byte encoding
                data_dict = {}
                if isinstance(hook_result, dict):
                    data_dict = hook_result
                    body_bytes = json.dumps(hook_result).encode('utf-8')

                    if data_dict.get("error") and "401" in str(data_dict.get("error")):
                        resp.status_code = 401
                        resp.reason = "Unauthorized"
                elif isinstance(hook_result, str):
                    body_bytes = hook_result.encode('utf-8')
                    try:
                        data_dict = json.loads(hook_result)
                    except Exception:
                        pass
                else:
                    body_bytes = hook_result if isinstance(hook_result, bytes) else b""

                # --- SESSION INTERCEPTION FOR AUTHENTICATION ---
                if req.path == "/login" and req.method == "POST":
                    try:
                        # Extract existing session or auto-generate a new unique session ID
                        session_id = data_dict.get("session", uuid.uuid4().hex)
                        
                        # Inject the session directly into the cookies dictionary
                        resp.cookies["session"] = session_id
                        
                        # Log to terminal for debugging and verification
                        print(f"[HttpAdapter] Successfully injected session cookie: {session_id}")
                    except Exception as e:
                        print(f"[HttpAdapter] Session generation error: {e}")
                # --------------------------------------------------------

                # --- ADDITION: MIME TYPE DETECTION FOR STATIC FILES ---
                # Initialize the headers dictionary if it does not exist
                if not resp.headers:
                    resp.headers = CaseInsensitiveDict()
                
                # Check the file extension in the URL path to assign the correct Content-Type
                if req.path.endswith(".html"):
                    resp.headers["Content-Type"] = "text/html; charset=utf-8"
                elif req.path.endswith(".css"):
                    resp.headers["Content-Type"] = "text/css; charset=utf-8"
                else:
                    # Default to JSON for other API responses
                    resp.headers["Content-Type"] = "application/json; charset=utf-8"
                # ----------------------------------------------------

                # Construct the HTTP payload (Headers + Body)
                response = resp.build_response(req, envelop_content=body_bytes)
            else:
                # Return 404 if no matching route is found
                response = resp.build_notfound()

            # Bulletproof check: Ensure payload is bytes before transmitting
            if isinstance(response, str):
                response = response.encode('utf-8')
            # Build response
            #print("[HttpAdapter] Start **ASYNC** build_response with type {}".format(type(req)))
            # response = resp.build_response(req)

            # Send all the response asynchronously
            writer.write(response)
            await writer.drain()
        
        except Exception as e:
            print("[HttpAdapter] Error handling client {}: {}".format(addr, e))

    # =========================================================================
    # ORIGINAL SKELETON METHODS (Preserved for structural compliance)
    # =========================================================================

    # @property
    # def extract_cookies(self, req, resp):
    #    """
    #    Build cookies from the :class:`Request <Request>` headers.
    #
    #    :param req:(Request) The :class:`Request <Request>` object.
    #    :param resp: (Response) The res:class:`Response <Response>` object.
    #    :rtype: cookies - A dictionary of cookie key-value pairs.
    #    """
    #    cookies = {}
    #    for header in headers:
    #        if header.startswith("Cookie:"):
    #            cookie_str = header.split(":", 1)[1].strip()
    #            for pair in cookie_str.split(";"):
    #                key, value = pair.strip().split("=")
    #                cookies[key] = value
    #    return cookies

    # def build_response(self, req, resp):
    #    """Builds a :class:`Response <Response>` object 
    #
    #    :param req: The :class:`Request <Request>` used to generate the response.
    #    :param resp: The  response object.
    #    :rtype: Response
    #    """
    #    response = Response()
    #
    #    # Set encoding.
    #    response.encoding = get_encoding_from_headers(response.headers)
    #    response.raw = resp
    #    response.reason = response.raw.reason
    #
    #    if isinstance(req.url, bytes):
    #        response.url = req.url.decode("utf-8")
    #    else:
    #        response.url = req.url
    #
    #    # Add new cookies from the server.
    #    response.cookies = extract_cookies(req)
    #
    #    # Give the Response some context.
    #    response.request = req
    #    response.connection = self
    #
    #    return response

    # def build_json_response(self, req, resp):
    #    """Builds a :class:`Response <Response>` object from JSON data
    #
    #    :param req: The :class:`Request <Request>` used to generate the response.
    #    :param resp: The  response object.
    #    :rtype: Response
    #    """
    #    response = Response(req)
    #
    #    # Set encoding.
    #    response.raw = resp
    #
    #    if isinstance(req.url, bytes):
    #        response.url = req.url.decode("utf-8")
    #    else:
    #        response.url = req.url
    #
    #    # Give the Response some context.
    #    response.request = req
    #    response.connection = self
    #
    #    return response


    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username and password:
            import base64
            # Standard HTTP headers require base64 encoding for Basic Auth
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            headers["Proxy-Authorization"] = f"Basic {encoded_credentials}"

        return headers