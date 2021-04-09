<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/collab/icon.png?raw=true" 
alt="drawing" width="75"/>
# Resolve Collaboration
Makes the **DaVinci Resolve 17** Live Collaboration features better, and makes them work over the internet in a secure manner.

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.51.56%20AM.png?raw=true"
alt="drawing" width="500"/>


<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/ResolveCollabFlow@4x.png?raw=true"
alt="drawing" width="1000"/>

## Builds:
- **MacOS** - [Download v0.0 Alpha for Catalina](https://github.com/jonnyhyman/ResolveCollaboration/releases/download/v0.0-alpha/Resolve.Collaboration.app.zip)
  - This .app has been found to fail on Big Sur. I am awaiting the next release of `pyinstaller` which addresses bugs related to Big Sur builds.
- **Windows** - *.exe is in development, for now, use `python resolve_collab.py`*
- **Linux** - *Help appreciated!*

## Status: *Alpha*
This project is seriously in development, I've only tested on the following configuration:
- Windows running Resolve 17's Project Server (PostgreSQL) and the Wireguard Server
- macOS clients on Resolve 17

## Features
- Simplifies connecting to a Wireguard Tunnel for over-the-internet collaboration
- Give a status list of project database connections (allows you to check connection status before launching Resolve)
- Give a status list of projects, and who is editing them

## Roadmap (help wanted!)
- Match the visual style to Resolve with Qt stylesheets for `QPushButton`, `QTableView`, `QDialog`, and `QWindow`
- Keep login details stored for database connections
- Secure the Server-side authentication database (currently just a .csv file)
- Host/control the WireGuard client from within the ResolveCollaboration codebase
- Status updates of connection speed/ping through the VPN and to the Project Server for all clients
- Move authentication port to same port as WireGuard so only one port forward needed for TCP+UDP

## Dependencies
Running with Python will not work without the following python packages:
- `pip install PyQt5 cryptography pandas psycopg2-binary wgnlpy`

## Setup Example

#### Context
- There are at least two sides to collaboration!
- Call one the "Server" and one "Client", assuming the Server is where the shared Resolve Database is stored
- You can distinguish if we're talking about Client or Server in this example by noting the OS. The server was on Windows and the client was on macOS

#### Walkthrough
Note that this walkthrough was made when the GUI wasn't visually complete. But the  terminology and process is exactly the same

First, launch the app on both Server and client. If you're running a packaged app, just open it. If you're running from python, run: `python collab/resolve_collab.py`

On the server, switch from Client context to Server context by clicking **Client**

<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.07%20AM.png?raw=true"
alt="drawing" width="250"/>

Create a password for the authentication server, or type in a password previously created. Optionally, supply the Public Key of the Wireguard interface of the server if one already exists. **Leave Public Key blank if there is no Wireguard server configuration yet.**

<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.31%20AM.png?raw=true" 
alt="drawing" width="250"/>

If you left Public Key blank, save the configuration file containing the server's private key and interface information

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.32.40%20AM.png?raw=true"
alt="drawing" width="500"/>


Click **New Team Member** to create a new user on the authentication server. Give this user a username and an assigned IP, which must be on the appropriate subnet *(default is 9.0.0.0/24)* and cannot match any other previously assigned IP

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.34.32%20AM.png?raw=true"
alt="drawing" width="500"/>

On client side, click **Make New Connection**. `Server IP` will be the `network IP` of the Server's host network if connecting from another network, or the `local IP` of the hosting machine if connecting from the same network. `Username` **must** be ***exactly*** the username string created on the Server side. This username is used to encrypt the traffic to the server. `Server Password` **must** be ***exactly*** the server password created on the Server side. This password is used to decrypt traffic coming back from the server.

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2012.12.59%20PM.png?raw=true"
alt="drawing" width="500"/>

Once the client has done entered this prompt, click **Authenticate** to launch the Authentication server

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.35.18%20AM.png?raw=true"
alt="drawing" width="500"/>

If authentication was successful, you will see the following message on the client

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.36.48%20AM.png?raw=true"
alt="drawing" width="250"/>

If authentication was successful, you will see the following message on the server

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.14%20AM.png?raw=true"
alt="drawing" width="500"/>

Next, save the new authenticated connection to the Server `.conf` file we created earlier (or some other Wireguard server configuration file)

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.32%20AM.png?raw=true"
alt="drawing" width="500"/>

Likewise, save the Wireguard client configuration somewhere

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.54%20AM.png?raw=true"
alt="drawing" width="500"/>

On the client side, open up the Wireguard app [available for download here on all platforms here](https://www.Wireguard.com/install/) and click **Import tunnel(s) from file** and open the client configuration file you just created.

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.40.51%20AM.png?raw=true"
alt="drawing" width="500"/>

On the server side, open up the Wireguard app [available for download here on all platforms here](https://www.Wireguard.com/install/) and click **Import tunnel(s) from file** and open the server configuration file you just created.

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.42.51%20AM.png?raw=true"
alt="drawing" width="500"/>

For a Windows server, to give clients access your internet connection, you must modify the internet adapter you're connected to the internet with. For me, that's `Ethernet 2`

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.44.27%20AM.png?raw=true"
alt="drawing" width="500"/>

Go to the Sharing tab, check both boxes, and select the Wireguard server you created as the Home network connection

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.45.51%20AM.png?raw=true"
alt="drawing" width="250"/>

Now, fire up the Wireguard server!

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.43.25%20AM.png?raw=true"
alt="drawing" width="500"/>

And fire up the Wireguard client! *(Note that it might look like its connected even if its not)*

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.46.27%20AM.png?raw=true"
alt="drawing" width="500"/>

If the connection was *actually* successful, the server will see a connected peer with a handshake

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.07%20AM.png?raw=true"
alt="drawing" width="500"/>

Once connected to the Wireguard VPN, the client can click **Reconnect** to connect to the Resolve database and populate the tables

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.27%20AM.png?raw=true"
alt="drawing" width="250"/>

And that's it! **Fire up Resolve and connect to the Project Server along with your colleagues! Chat features, and bin locking should work**

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.51.56%20AM.png?raw=true"
alt="drawing" width="500"/>

# Contributing
- I welcome *anyone* to contribute to this project, regardless of skill level - and I'll try to be prompt about pull requests. 
- Alpha testers are welcome to post their issues in the `Issues` tab on this repo so that things can be improved/expanded.
- If anyone has issues with the security model, please do post an Issue. This is my first project dealing with secure connections, and I think that it's pretty solid but I'm not entirely sure. 
