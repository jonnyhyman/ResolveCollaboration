# ResolveCollaboration
Makes the **DaVinci Resolve 17** Live Collaboration features better, and makes them work over the internet in a secure manner.

![Resolve Mission Control](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.51.56%20AM.png?raw=true)

# Status
This project is seriously in development, I've only tested on the following configuration:
- Windows running Resolve 17's Project Server (PostgreSQL) and the Wireguard Server
- macOS clients on Resolve 17

# Features
- Simplifies connecting to a Wireguard Tunnel for over-the-internet collaboration
- Give a status list of project database connections (allows you to check connection status before launching Resolve)
- Give a status list of projects, and who is editing them

TODO:
- Status updates of connection speed/ping through the VPN and to the Project Server
- Provide user-friendly symlink generation so that media addresses can be linked across systems (Windows C:/... to Mac /Users/... or wherever your paths are). This is supposedly doable using Mapped Media in Resolve but this seems to be a bit shoddy. Hopefully there can be a multiplatform symlink solution?

# Setup Example

#### Context
- There are at least two sides to collaboration!
- Call one the "Server" and one "Client", assuming the Server is where the shared Resolve Database is stored
- You can distinguish if we're talking about Client or Server in this example by noting the OS. The server was on Windows and the client was on macOS

#### Walkthrough
Note that this walkthrough was made when the GUI wasn't visually complete. But the  terminology and process is exactly the same

First, launch main.py on both Server and client:
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.29.00%20AM.png?raw=true)

On the server, switch from Client context to Server context by clicking **Client**
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.07%20AM.png?raw=true)

Create a password for the authentication server, or type in a password previously created. Optionally, supply the Public Key of the Wireguard interface of the server if one already exists. **Leave Public Key blank if there is no Wireguard server configuration yet.**
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.31%20AM.png?raw=true)

If you left Public Key blank, save the configuration file containing the server's private key and interface information
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.32.40%20AM.png?raw=true)

Click **New Team Member** to create a new user on the authentication server. Give this user a username and an assigned IP, which must be on the appropriate subnet *(default is 9.0.0.0/24)* and cannot match any other previously assigned IP
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.34.32%20AM.png?raw=true)

On client side, click **Make New Connection**. `Server IP` will be the `network IP` of the Server's host network if connecting from another network, or the `local IP` of the hosting machine if connecting from the same network. `Username` **must** be ***exactly*** the username string created on the Server side. This username is used to encrypt the traffic to the server. `Server Password` **must** be ***exactly*** the server password created on the Server side. This password is used to decrypt traffic coming back from the server.
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.12.12%59PM.png?raw=true)

Once the client has done entered this prompt, click **Authenticate** to launch the Authentication server
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.35.18%20AM.png?raw=true)

If authentication was successful, you will see the following message on the client
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.36.48%20AM.png?raw=true)

If authentication was successful, you will see the following message on the server
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.14%20AM.png?raw=true)

Next, save the new authenticated connection to the Server `.conf` file we created earlier (or some other Wireguard server configuration file)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.32%20AM.png?raw=true)

Likewise, save the Wireguard client configuration somewhere
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.54%20AM.png?raw=true)

On the client side, open up the Wireguard app [available for download here on all platforms here](https://www.Wireguard.com/install/) and click **Import tunnel(s) from file** and open the client configuration file you just created.
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.40.51%20AM.png?raw=true)

On the server side, open up the Wireguard app [available for download here on all platforms here](https://www.Wireguard.com/install/) and click **Import tunnel(s) from file** and open the server configuration file you just created.
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.42.51%20AM.png?raw=true)

For a Windows server, to give clients access your internet connection, you must modify the internet adapter you're connected to the internet with. For me, that's `Ethernet 2`
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.44.27%20AM.png?raw=true)

Go to the Sharing tab, check both boxes, and select the Wireguard server you created as the Home network connection
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.45.51%20AM.png?raw=true)

Now, fire up the Wireguard server!
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.43.25%20AM.png?raw=true)

And fire up the Wireguard client! *(Note that it might look like its connected even if its not)*
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.46.27%20AM.png?raw=true)

If the connection was *actually* successful, the server will see a connected peer with a handshake
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.07%20AM.png?raw=true)

Once connected to the Wireguard VPN, the client can click **Reconnect** to connect to the Resolve database and populate the tables
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.27%20AM.png?raw=true)

And that's it! **Fire up Resolve and connect to the Project Server along with your colleagues! Chat features, and bin locking should work**
![](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.51.56%20AM.png?raw=true)
