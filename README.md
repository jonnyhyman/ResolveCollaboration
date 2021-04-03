# ResolveCollaboration
I'm developing an app that makes the **DaVinci Resolve 17** Live Collaboration features better, and makes them work over the internet in a secure manner.

# Status
This project is seriously in development, I've only tested on the following configuration:
- Windows running Resolve 17's Project Server (PostgreSQL) and the WireGuard Server
- macOS clients on Resolve 17

# Features
- Simplifies connecting to a WireGuard Tunnel for over-the-internet collaboration
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
Note that this walkthrough was made when the GUI wasn't complete. But terminology should be the same
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.29.00%20AM.png?raw=true)

![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.07%20AM.png?raw=true)

![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.30.31%20AM.png?raw=true)

![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.32.40%20AM.png?raw=true)

![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.34.32%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.34.53%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.35.18%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.36.48%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.14%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.32%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.37.54%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.38.18%20AM.png?raw=true)

![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.40.51%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.42.51%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.43.25%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.44.27%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.45.51%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%209.46.27%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.07%20AM.png?raw=true)
![Image](https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-03%20at%2010.14.27%20AM.png?raw=true)
