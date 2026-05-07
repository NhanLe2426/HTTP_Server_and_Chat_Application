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

from   daemon import AsynapRous
from    .auth import require_auth

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

