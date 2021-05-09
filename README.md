<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/collab/icon.png?raw=true"
alt="drawing" width="75"/> 

# Welcome to Mission Control

Work on **DaVinci Resolve 17** Live Collaboration projects __from anywhere on Earth__

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-12%20at%2011.55.11%20AM.png?raw=true"
alt="drawing" width="500"/>

## Features
- Secure user authentication
- Wireguard secure tunnel configuration management and control
- Resolve PostgreSQL Database Management, __replacing__ _the overly-limited DaVinci Resolve Project Manager_

## Downloads
- Resolve Mission Control Client [**macOS** .app](), [**Windows** .exe]()

## Quickstart
- __Client on macOS/Windows__
    - Open the app
    - Authenticate to the Resolve Mission Control Server, save the configuration file
    - Install the [Wireguard app]()
    - Import Tunnel configuration file into Wireguard
    - Export Database Connection file somewhere
    - Drag/drop or double-click connection file to connect  
    - __Edit collaboratively!__

---
- __Server on macOS__
    - Install [Homebrew]()
    - `brew install wireguard-tools`
    - `brew install python3` (if you don't already have Python 3)
    - `pip install PyQt5==5.15.2 cryptography psycopg2-binary elevate`
    - Run `python rmc_server.py`
    - Use setup
- __Server on Windows__
    - Install [Python 3.9]()
    - `pip install PyQt5==5.15.2 cryptography psycopg2-binary pywin32 elevate`
    - Install [Wireguard app]()
    - Run `python rmc_server.py`

4. Server setup

5. Tell user to launch the client app
(image)

6. Activate authentication server

7. Activate Wireguard tunnel

8. Edit to your heart's desire

## Plans for a paid version
I'm trying to gauge interest for a paid version of this app, which would be far more powerful 

- Client app:
    - High performance, written in native languages (Go?) (C++ Windows/Linux, Swift macOS)
    - 2Fac Auth, Tunnel (embedded), Extended Userlist (IP/Loc, Machine ID, Productivity)
    - Cloud Sync Info (Dropbox, Drive, etc…)
    - Private Interplanetary File System (IPFS)
- Server app:
    - High performance, written in native languages (Go?) (C++ Windows/Linux, Swift macOS)
    - 2Fac Auth, Tunnel (embedded), Extended Userlist (IP/Loc, Machine ID, Productivity)
    - Cloud Sync Info (Dropbox, Drive, etc…)
    - Seamless support for linked-star tunnels or maybe meshes?
    - More user information and security features (IP lock, Machine ID lock, etc…)
- Admin app:
    - Control unlimited number of servers from afar through a powerful web app
