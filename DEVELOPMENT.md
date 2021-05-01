# Development todo list:
_(many things here may be in code TODOs or not)_

## Minimum release
_Assume both macOS and Windows support for all of the below:_


Common:
- DB list
    - Removable
    - Duplicates
    
- Project list
    - Simple
        - Project name
        - Live Collaboration: "On", "Off"
        - Users in project

Client:
- Authentication to Server
    -  Async TCP client in the background with polling for output/updates
        -  Terminate on cancel/crash

- Wireguard configuration management
    -  Option A: Copy and paste into Wireguard app
        -  small gif walkthrough
    -  Option B: Save .conf file
        -  small gif walkthrough

- Userlist
    -  Request userlist from Server
    -  Update userlist on timer
    -  Update whose online
        -  Whose online: Ping on timer

Server:
- Authentication to Client
    -  Async TCP server in the background with polling for output/updates
        -  Terminate on close
    -  Save user details to userlist
    -  Clients can request userlist
    
- Userlist
    -  Serve userlist to Clients
    -  Update userlist on timer
        -  Whose online: Ping on timer
    
- Wireguard management
    - Create config with post-up and post-down commands
        -  macOS
        -  Windows
        
- Database management
    - Updaing hba_conf
    

## Icing on the cake

- Configuration reset option common

Server:
- Pinging of users
- Extra details about projects
- PostgreSQL database user creation and management see `postgres_management.ipynb`
- Dropbox sync page / Media management in general
