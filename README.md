# HTTP Server & P2P Chat Application

## Overview

This is a comprehensive networking assignment implementing a **custom HTTP server** and a **Peer-to-Peer (P2P) chat application**. The project is built with Python and demonstrates core networking concepts including socket programming, HTTP protocol handling, request/response management, reverse proxy implementation, and distributed chat communication.

**Course**: CO3093/CO3094 - Computer Networks  
**University**: Ho Chi Minh City University of Technology (VNU-HCM)  
**Framework**: AsynapRous (Custom HTTP Framework)

---

## Project Architecture

The project consists of several key components:

```
├── daemon/                  # Core HTTP framework (AsynapRous)
├── apps/                    # Application layer (Sample app, Chat, Auth)
│   └── peer_node.py         # Main P2P Chat Node application
├── config/                  # Configuration files (Proxy settings)
├── cert/                    # SSL/TLS certificates
├── db/                      # Database files
├── static/                  # Static assets
├── www/                     # Web content (HTML/JS/CSS for Chat UI)
├── start_backend.py         # Backend server launcher
├── start_proxy.py           # Reverse proxy launcher
├── start_sampleapp.py       # Sample app launcher
└── tracker.py               # P2P Discovery Server (Directory)
```

---

<!-- ## Core Components

### 1. **AsynapRous Framework** (`daemon/`)

A custom HTTP framework built from scratch using Python sockets.

#### Key Modules:

- **`backend.py`**: Backend server implementation
  - Manages multiple client connections using threading
  - Handles HTTP request routing
  - Supports daemon threads for concurrent processing

- **`httpadapter.py`**: HTTP request/response adapter
  - Routes HTTP requests to handlers
  - Manages connection lifecycle
  - Integrates Request and Response objects

- **`request.py`**: HTTP Request object
  - Parses incoming HTTP requests
  - Manages headers, cookies, authentication
  - Handles request body processing

- **`response.py`**: HTTP Response object
  - Constructs HTTP responses
  - MIME type detection
  - Header formatting and content loading

- **`proxy.py`**: Reverse proxy implementation
  - Routes requests to backend servers
  - Supports virtual host configurations
  - Implements load balancing policies (round-robin)

- **`dictionary.py`**: Case-insensitive dictionary
  - For HTTP header management (headers are case-insensitive)

- **`utils.py`**: Utility functions
- **`asynaprous.py`**: Main framework class

### 2. **P2P Chat Applications** (`apps/`)

#### Sample Application (`sampleapp.py`)

A RESTful web application demonstrating the framework capabilities:
- User login endpoint (`/login`)
- Active peers tracking
- Chat message storage
- Authentication support

#### Authentication (`auth.py`)

- Decorator-based authentication (`@require_auth`)
- Session cookie validation
- Support for both sync and async route handlers

### 3. **P2P Chat Components** 


--- -->
## Core Components

### 1. **AsynapRous Framework** (`daemon/`)

A custom HTTP framework built from scratch to support asynchronous operations.

#### Key Modules:
- **`backend.py`**: Backend server implementation utilizing **Coroutine (`asyncio`)** to handle concurrent HTTP connections without blocking the main event loop.
- **`httpadapter.py`**: HTTP request/response adapter. Routes requests to handlers and manages session cycling for security.
- **`request.py`**: Parses incoming HTTP requests, manages headers, cookies, and authentication.
- **`response.py`**: Constructs HTTP responses, handles MIME type detection and static file serving.
- **`proxy.py`**: Reverse proxy implementation with load balancing policies (round-robin).

### 2. **P2P Chat Application** (`apps/`)

- **`peer_node.py`**: The core dual-role (Client/Server) application.
  - **Hybrid Non-blocking Architecture**: Uses `asyncio` for the web server to handle thousands of HTTP requests, combined with `ThreadPoolExecutor` (Multi-threading) for non-blocking P2P network transmission.
  - **Pub/Sub Channel Management**: Supports joining and creating Group Channels (prefixed with `#`) via a dynamic UI Modal, alongside Direct Peer-to-Peer messaging.
  - **Strict Node Authentication**: A peer node is strictly bound to its owner at startup to prevent identity spoofing.
- **`auth.py`**: Decorator-based authentication (`@require_auth`). Intercepts requests to validate session cookies and returns HTTP 401 Unauthorized for invalid access.

## Getting Started

### Prerequisites
- Python 3.7 or higher
- No external libraries required (`pip install` is NOT needed). 
- Uses pure Python standard libraries.

### Running P2P Chat Application

This test demonstrates the core requirement: **Clients can continue chatting directly even if the central server (Tracker) is shut down.**

*Note: The system enforces Strict Authentication based on predefined users in the database (e.g., Nhan, Nghi, Khanh) with the default password `123`.*

#### 1. Start the Tracker (Terminal 1)
```bash
python tracker.py
# Expected output: [*] P2P Tracker is officially running on port 9000...
```

#### 2. Start Peer Node 1 (Terminal 2)
```bash
python apps/peer_node.py Nhan 5001
# Expected output: [*] Nhan successfully registered with Tracker.
```

#### 3. Start Peer Node 2 (Terminal 3)
```bash
python apps/peer_node.py Nghi 5002
# Expected output: [*] Nghi successfully registered with Tracker.
```

#### 4. Start Peer Node 3 (Terminal 4)
```bash
python apps/peer_node.py Khanh 5003
# Expected output: [*] Nghi successfully registered with Tracker.
```

### UI Interaction & Connection Building

**⚠️ IMPORTANT CAVEAT FOR LOCAL TESTING (Cookie Sharing)**
Because the application uses Cookies for strict session management and all test nodes run on the exact same IP (`127.0.0.1`), standard browser tabs will share the same Cookie storage. Opening two normal tabs will cause the sessions to overwrite each other. 

To successfully test multiple peers on a single machine, you **MUST use isolated browser sessions**.

1. **Peer 1 (e.g., Nhan on port 5001):**
   - Open your primary browser (e.g., Google Chrome - Normal Window).
   - Navigate to `http://127.0.0.1:5001/login.html`.
   - Login with **Username:** `Nhan`, **Password:** `123`.

2. **Peer 2 (e.g., Nghi on port 5002):**
   - Open an **Incognito / Private Browsing window** of the same browser.
   - Navigate to `http://127.0.0.1:5002/login.html`.
   - Login with **Username:** `Nghi`, **Password:** `123`.

3. **Peer 3 (e.g., Khanh on port 5003 - Optional):**
   - Open a **completely different web browser** (e.g., Microsoft Edge, Firefox, or Safari).
   - Navigate to `http://127.0.0.1:5003/login.html`.
   - Login with **Username:** `Khanh`, **Password:** `123`.

Once logged in across these isolated environments:
- Click the **`+`** button in the Active Chats sidebar to create a group channel (e.g., `#Study`).
- Check the boxes to invite the other online peers.
- Send a few messages back and forth to verify that the P2P connection logic is routing packets correctly based on the Tracker's directory.

### The "Tracker Shutdown" Test
1. Go back to **Terminal 1** (running `tracker.py`).
2. Press `Ctrl + C` to **completely shut down the Tracker server**.
3. Return to the browser windows (Do NOT refresh the page).
4. Send new messages. 
   > **Result:** The messages will still be delivered instantly. Since the nodes have already cached the peer directory, they use background threading (`urllib.request`) to establish direct HTTP POST connections to each other, proving the network is fully decentralized.

---

### Running on Multiple Physical Machines (LAN Testing)

To demonstrate true decentralized P2P capabilities across separate physical computers, both machines must be connected to the **same Local Area Network (LAN)** (e.g., the same Wi-Fi or router).

#### 1. Network Configuration Adjustments
Before running the scripts, you must replace `127.0.0.1` with the actual local network IPs.

- **Find Local IP:** Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) in the terminal. 
  - *Example:* Machine 1 IP is `192.168.1.15`, Machine 2 IP is `192.168.1.20`.
- **Update Code Configuration:**
  - In `apps/peer_node.py` on **Machine 1**, set `TRACKER_URL = "http://192.168.1.15:9000"`.
  - In `apps/peer_node.py` on **Machine 2**, set `TRACKER_URL = "http://192.168.1.15:9000"` (pointing back to Machine 1).
  - Ensure the `MY_IP` variable inside each node's script correctly reflects its own physical LAN IP.

#### 2. Execution Steps

**On Machine 1 (Acts as Tracker Host & Peer 1):**
1. Start the central directory server:
   ```bash
   python tracker.py
   ```

2. In a separate terminal, launch the first peer node:
   ```bash
   python apps/peer_node.py Nhan 5001
   ```

3. Access the UI via a standard browser window at `http://127.0.0.1:5001/login.html`.

**On Machine 2 (Acts as Peer 2):**
1. Launch the second peer node directly (No tracker needed here):
   ```bash
   python apps/peer_node.py Nghi 5002
   ```

2. Access the UI via any browser window at `http://127.0.0.1:5002/login.html`.

#### 3. Troubleshooting & Firewalls

If Machine 2 encounters a connection timeout when reaching out to Machine 1, it is highly likely that **Machine 1's firewall is blocking incoming traffic**.

- **Fix:** Temporarily disable the firewall on the host machine or add an inbound rule allowing TCP traffic through ports `9000`, `5001`, and `5002`.

---

## File Structure Details

| File / Directory | Purpose |
|------------------|---------|
| `daemon/backend.py` | Core backend server initialization |
| `daemon/proxy.py` | Reverse proxy implementation & load balancing |
| `daemon/httpadapter.py` | HTTP request routing and connection handling |
| `daemon/request.py` | HTTP request parsing and data extraction |
| `daemon/response.py` | HTTP response construction and MIME type detection |
| `daemon/asynaprous.py` | Framework main class and routing definitions |
| `daemon/dictionary.py` | Case-insensitive dictionary for HTTP headers |
| `apps/peer_node.py` | **Main P2P chat node (Client & Server dual role)** |
| `apps/sampleapp.py` | Sample RESTful application |
| `apps/auth.py` | Authentication logic and decorators |
| `config/proxy.conf` | Proxy routing configuration rules |
| `www/` | **Static web assets (HTML/JS/CSS for Chat UI)** |
| `tracker.py` | **P2P Discovery Server (Directory for active peers)** |

---

## Important Notes

- The framework is designed for **educational purposes** to understand networking fundamentals
- This is **assignment work** - not production-ready code
- Production use requires additional:
  - Security hardening (TLS/SSL, input validation)
  - Error handling and logging
  - Performance optimization
  - Scalability improvements
- The proxy configuration parser supports NGINX-style syntax
- Chat application demonstrates P2P networking concepts
- Authentication system can be extended with JWT or OAuth2 mechanisms

---

## License

This project is part of the **CO3093/CO3094 - Computer Networks** course at HCMC University of Technology and is released under the **MIT License**.

**MIT License Summary:**
- ✅ You can use, modify, and distribute this code freely
- ✅ You must include the license and copyright notice
- ✅ The code is provided "as-is" without warranty

```
MIT License

Copyright (c) 2026 Computer Networks Course - HCMC University of Technology (VNU-HCM)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

For the full license text, see the LICENSE file in the repository.

---

## Author & Contributors

**Course**: CO3093/CO3094 - Computer Networks  
**Institution**: HCMC University of Technology (VNU-HCM)  
**Semester**: 2025-2026  
**Project Type**: Assignment 1 - HTTP Server & P2P Chat Application  

**AsynapRous Framework**: Custom HTTP framework developed as part of this course assignment  
**Based On**: Networking principles, socket programming, and distributed systems concepts

---
