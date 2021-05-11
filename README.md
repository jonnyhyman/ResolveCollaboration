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

## Download the Client

There are mandatory installation instructions, [please see this page](https://github.com/jonnyhyman/ResolveCollaboration/releases/tag/0.1.0)

| Platform | Download     |
|:---------|-------------:|
|macOS 10.15+ | [**macOS** .app](https://github.com/jonnyhyman/ResolveCollaboration/releases/download/0.1.0/macOS_Resolve.Mission.Control-v0.1.0-signed.zip) |
|Windows 10 |[**Windows** .exe](https://github.com/jonnyhyman/ResolveCollaboration/releases/download/0.1.0/Win10-Resolve.Mission.Control-v0.1.0.zip) |
|Linux | Looking for beta testers |

---
## Quickstart
- __Client__
    - Open the app
    - Authenticate to the Resolve Mission Control Server
    - Save the configuration file somewhere you remember
    - Install [Wireguard](https://www.wireguard.com/install/)
    - Import the configuration file into Wireguard
    - Click the ⇄ button to connect to a Resolve database
    - Use _Export Database Connection_ to save the database connection
    - Double-click the exported file or drag-drop into Resolve to connect  
    - __Have fun!__

---
> For more details on what's below, read the [Server guide](https://github.com/jonnyhyman/ResolveCollaboration/wiki/Server-guide)

- Clone this repo's source code:
    - Option 1) `git clone https://github.com/jonnyhyman/ResolveCollaboration.git`
    - Option 2) [Download and unzip this](https://github.com/jonnyhyman/ResolveCollaboration/archive/refs/heads/main.zip)

- __Server on macOS__
    - Install [Homebrew](https://brew.sh/)
    - Run in Terminal:
        - `brew install wireguard-tools`
        - `brew install python3` (if you don't already have Python 3)
        - `pip install PyQt5==5.15.2 cryptography psycopg2-binary elevate`
        - `python rmc_server.py`
- __Server on Windows__    
    - Install [Python 3.9](https://www.python.org/downloads/)
    - Install [Wireguard for Windows](https://www.wireguard.com/install/)
    - Run in Powershell/Command Prompt:
        - `pip install PyQt5==5.15.2 cryptography psycopg2-binary pywin32 elevate`
        - `python rmc_server.py` 
        
The GUI will automatically demand root/admin privileges using the `elevate` package, to allow:
- Control of Wireguard
- Opening of Firewall (macOS)
- Reconfiguring of Network Sharing settings (Windows)
- Read/write of configuration files in protected directories
- PostgreSQL Server restarts (macOS via pg_ctl, Windows via the postgres service)

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

__If the above sounds enticing to you, please go [upvote this post!](https://github.com/jonnyhyman/ResolveCollaboration/issues/4)__
