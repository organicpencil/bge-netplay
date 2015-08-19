# bge-netplay
A library for building multiplayer prototypes in Blender's built-in game engine.

Documentation and examples are lacking.  The API is subject to change.  *I wouldn't use it yet.*

**Most of the examples are broken except 04_physics**

What it does:
- Handle data transfer and connection management using ENet
- Abstract things like input bitmasks and remote procedure calls
- Builtin physics prefabs to get you up and running quickly
- (eventually) NAT punchthrough, relay hosting, LAN discovery

What it doesn't do:
- Automatic multiplayer.  You'll still need general knowledge on how multiplayer games work.
- Real games.  The lib is a work-in-progress, so expect bugs/slowness/security issues.
- Work on MacOS or Win64 Blender builds (yet)



#Running the examples
**Blender 2.75+ is recommended, support for older versions will soon be dropped**

Clone the repository
```
git clone https://github.com/pqftgs/bge-netplay.git
cd bge-netplay
```
Set up dependencies
```
./download_deps.sh
```
Navigate to the examples folder and fire away!  I suggest running the server with the standalone player, as your system may want to hold onto the socket until the process is closed.  Need to look into that...
