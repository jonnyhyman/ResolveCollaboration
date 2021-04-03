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
