<img src=
"https://github.com/jonnyhyman/ResolveCollaboration/blob/main/collab/icon.png?raw=true"
alt="drawing" width="75"/> <h> Resolve Mission Control </h>

This project makes the **DaVinci Resolve 17** Live Collaboration features better, and makes them work over the internet in a secure manner.

<img src="https://github.com/jonnyhyman/ResolveCollaboration/blob/main/images/Screen%20Shot%202021-04-12%20at%2011.55.11%20AM.png?raw=true"
alt="drawing" width="500"/>

## Features
- Authentication and control of Wireguard Tunnel for over-the-internet collaboration
- Check connection status to remote databases before launching Resolve
- 

## Client
- These are the builds for 
| Platform | Support | Link |
|:----------:|:----------:|:---------------:|
| **macOS**  | Tested on Catalina 10.15.7 | [Download]() |
| **Windows** | Only client is supported ||

## Server
- Can only be run from source!
- macOS requires:
    - `brew install wireguard-tools`

## Dependencies

Running from source requires following python packages:
- Install all in one: `pip install PyQt5==5.15.2 cryptography psycopg2-binary`
- Install individually:
   - `pip install PyQt5==5.15.2`
   - `pip install cryptography`
   - `pip install psycopg2-binary`

## Setup Example

#### Context
- There are at least two sides to collaboration!
- Call one the "Server" and one "Client", assuming the Server is where the shared Resolve Database is stored
- You can distinguish if we're talking about Client or Server in this example by noting the OS. The server was on Windows and the client was on macOS

# Contributing
- I welcome *anyone* to contribute to this project, regardless of skill level - and I'll try to be prompt about pull requests.
- Alpha testers are welcome to post their issues in the `Issues` tab on this repo so that things can be improved/expanded.
- If anyone has issues with the security model, please do post an Issue. This is my first project dealing with secure connections, and I think that it's pretty solid but I'm not entirely sure.
