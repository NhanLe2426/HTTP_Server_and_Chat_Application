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
├── device1.py               # P2P Chat Device 1
├── device2.py               # P2P Chat Device 2
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

## Getting Started

### Prerequisites
- Python 3.7 or higher
- No external libraries required (`pip install` is NOT needed). 
- Uses pure Python standard libraries.

### Running P2P Chat Application

This test demonstrates the core requirement: **Clients can continue chatting directly even if the central server (Tracker) is shut down.**

#### 1. Start the Tracker (Terminal 1)
```bash
python tracker.py
# Expected output: [*] P2P Tracker is officially running on port 9000...
```

#### 2. Start Peer Node 1 (Terminal 2)
```bash
python apps/peer_node.py <peer_name_1> 5001
# Example: python apps/peer_node.py Alice 5001
# Expected output: [*] Alice successfully registered with Tracker.
```

#### 3. Start Peer Node 2 (Terminal 3)
```bash
python apps/peer_node.py <peer_name_2> 5002
# Example: python apps/peer_node.py Bob 5002
# Expected output: [*] Bob successfully registered with Tracker.
```

### UI Interaction & Connection Building
1. Open a web browser and split the screen.
2. **Left Window:** Navigate to `http://127.0.0.1:5001/login.html`. In the Username field, enter the exact name you used for Node 1 (e.g., Alice), enter any password, and login.
3. **Right Window:** Navigate to `http://127.0.0.1:5002/login.html`. In the Username field, enter the exact name you used for Node 2 (e.g., Bob), enter any password, and login.
4. Send a few messages between the two windows to ensure the nodes have successfully retrieved each other's IPs from the Tracker.

### The "Tracker Shutdown" Test
1. Go back to **Terminal 1** (running `tracker.py`).
2. Press `Ctrl + C` to **completely shut down the Tracker server**.
3. Return to the browser windows (Do NOT refresh the page).
4. Send new messages. 
   > **Result:** The messages will still be delivered instantly. Since the nodes have already cached the peer directory, they use background threading (`urllib.request`) to establish direct HTTP POST connections to each other, proving the network is fully decentralized.

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
