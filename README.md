# Welcome to Resolve Mission Control
Work on **DaVinci Resolve 17** Live Collaboration projects __with anyone, from anywhere__

|Client (somewhere far away) | Server (home base) |
|:---|:---|
|<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Image%205-9-21%20at%207.00%20PM.jpg?raw=true" alt="Client" width="800"/>|<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-05-09%20at%206.40.03%20PM.png?raw=true" alt="Server" width="800"/>|

## Features
- Secure __over the internet__ video editing collaboration for Resolve
- [Wireguard](https://www.wireguard.com/) VPN tunnel setup, management and control
- Secure user authentication
- Resolve database management, __replacing__ _the overly-limited DaVinci Resolve Project Server_

## Downloads
__Client__ Beta 0.1.0

| Platform | Download     |
|:---------|-------------:|
|macOS 10.15+ | [**macOS** .app]() |
|Windows 10 |[**Windows** .exe]() |
|Linux | Looking for beta testers |

---
## Quickstart
- __Client__
    - Open the app
    - Authenticate to the Resolve Mission Control Server
    - Save the configuration file somewhere you remember
    - Install [Wireguard](https://www.wireguard.com/install/)
    - Import the configuration file into Wireguard
    - Connect to Resolve database in the top left
    - Use _Export Database Connection_ to save the database connection
    - Double-click the exported file or drag-drop into Resolve to connect  
    - __Have fun!__

---
#### Check out the [Server guide]() for more details
- __Server on macOS__
    - Download Resolve Mission Control Server source code
    - Install [Homebrew](https://brew.sh/)
    - Run in Terminal:
        - `brew install wireguard-tools`
        - `brew install python3` (if you don't already have Python 3)
        - `pip install PyQt5==5.15.2 cryptography psycopg2-binary elevate`
        - `python rmc_server.py`
- __Server on Windows__
    - Download Resolve Mission Control Server source code
    - Install [Python 3.9](https://www.python.org/downloads/)
    - Install [Wireguard for Windows](https://www.wireguard.com/install/)
    - Run in Powershell/Command Prompt:
        - `pip install PyQt5==5.15.2 cryptography psycopg2-binary pywin32 elevate`
        - `python rmc_server.py`
---

## Plans for a fully-featured paid version
I'm trying to gauge interest for a paid version of this app, which would be far more powerful, adding: 

- __Client__
    - High performance, written in native languages (C++ Windows/Linux, Swift macOS)
    - 2Fac Auth, Tunnel (embedded), Extended Userlist (IP/Loc, Machine ID, Productivity)
    - Cloud Sync Info (Dropbox, Drive, etc…)
    - [Interplanetary File System](https://ipfs.io/) project media storage and sync
    - [Filecoin](https://filecoin.io/) long-term project media storage and archiving
- __Server__
    - High performance, written in native languages (C++ Windows/Linux, Swift macOS)
    - 2Fac Auth, Tunnel (embedded), Extended Userlist (IP/Loc, Machine ID, Productivity)
    - Cloud Sync Info (Dropbox, Drive, etc…)
    - Seamless support for linked-star tunnels or maybe meshes?
    - More user information and security features (IP lock, Machine ID lock, etc…)
- Admin app:
    - Control unlimited number of servers from afar through a powerful web app

__If the above sounds enticing to you, please go [upvote this post!]()__
