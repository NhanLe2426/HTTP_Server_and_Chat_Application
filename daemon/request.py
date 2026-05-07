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
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
import base64
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "_raw_headers",
        "_raw_body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        # The raw header
        self._raw_headers = None
        #: The raw body
        self._raw_body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def fetch_headers_body(self, request):
        """
        Prepares the given HTTP headers.
        Handles both Windows (\r\n\r\n) and Unix (\n\n) line endings dynamically.
        """
        # Split request into header section and body section
        # parts = request.split("\r\n\r\n", 1)  # split once at blank line

        # _headers = parts[0]
        # _body = parts[1] if len(parts) > 1 else ""
        # return _headers, _body
        if "\r\n\r\n" in request:
            parts = request.split("\r\n\r\n", 1)
        elif "\n\n" in request:
            parts = request.split("\n\n", 1)
        else:
            parts = [request, ""]
            
        _headers = parts[0]
        _body = parts[1].strip()        # Remove trailing whitespaces with strip()
        return _headers, _body
    
    def parse_cookies(self):
        """
        Extract and parse the 'cookie' header from the internal headers dictionary.
        Converts the semicolon-separated cookie string into a key-value dictionary
        and stores it in the 'self.cookies' attribute.
        
        This isolated method is crucial for session management and user authentication.
        """
        cookie_header = self.headers.get('cookie', '')

        # Exit early if no cookies were sent by the client
        if not cookie_header:
            return
        
        cookies = {}
        parts = cookie_header.split(';')

        for p in parts:
            if '=' in p:
                # Split each cookie into key and value pairs, and strip whitespace
                key, value = p.strip().split('=', 1)
                cookies[key] = value

        self.cookies = cookies
        print(f"[Request] Parsed cookies: {self.cookies}")

    def parse_basic_auth(self):
        """
        Extracts and decodes the Base64 'Authorization' header to retrieve user credentials.
        """
        auth_header = self.headers.get('authorization', '')
        if auth_header.lower().startswith('basic '):
            # Extract the Base64 encoded part after "Basic "
            encoded_credentials = auth_header.split(' ', 1)[1]
            try:
                decoded_str = base64.b64decode(encoded_credentials).decode('utf-8')
                username, password = decoded_str.split(':', 1)
                self.auth = (username, password)
                print(f"[Request] Authenticated user via Basic Auth: {username}")
            except Exception as e:
                print(f"[Request] Base64 decoding failed for Basic Auth: {e}")

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        print("[Request] prepare request missg {}".format(request))
        self.method, self.path, self.version = self.extract_request_line(request)
        if not self.method:
            return

        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # ---- EXTRACT HEADERS AND BODY ----
        # Fetch Header and Body from the raw request string
        raw_headers, raw_body = self.fetch_headers_body(request)
        
        # Convert Header string to Dictionary so that system can use the .get() function
        self.headers = self.prepare_headers(raw_headers)
        if self.headers is None:
            self.headers = CaseInsensitiveDict()
        
        # If raw_body is empty, assign it to an empty string instead of leaving it as default None
        self.body = raw_body if raw_body else ""
        # ----------------------------------

        #
        # @bksysnet Preapring the webapp hook with AsynapRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if not routes == {}:
            self.routes = routes
            print("[Request] Routing METHOD {} path {}".format(self.method, self.path))
            self.hook = routes.get((self.method, self.path))
            print("[Request] Hook has request {}".format(request))
            #
            # self.hook manipulation goes here
            # ...
            #

        # self._raw_headers = ""
        # self._raw_body =  ""
        # cookies = self.headers.get('cookie', '')
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #
            
        # Extract and parse Cookies by calling the parsing method
        self.parse_cookies()
        # Extract and decode the Base64 'Authorization' header to retrieve user credentials
        self.parse_basic_auth()

        return

    def prepare_body(self, data, files, json=None):
        self.prepare_content_length(self.body)
        self.body = data
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
