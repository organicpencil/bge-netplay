# bge-netplay
A framework for building multiplayer games in Blender.

Documentation and examples are lacking.  The API is subject to change.  *I wouldn't use it yet.*

What it does:
- Abstracts ENet to manage connections
- Things like input bitmasks and remote procedure calls
- Builtin physics prefabs that kind of suck
- (eventually) NAT punchthrough, relay hosting, LAN discovery

What it doesn't do:
- Automatic multiplayer.  You still need to know how multiplayer works.
- Real games.  The framework is very much work-in-progress, expect bugs/slowness/security issues.
- Work on MacOS or Win64 (yet)


#Running the examples
**Blender 2.76 or newer is required**

Clone the repository
```
git clone https://github.com/pqftgs/bge-netplay.git
cd bge-netplay
```
Set up dependencies
```
./download_deps.sh
```
Navigate to the examples folder and fire away!  It's recommended to run the server with the standalone player, as your system may hold onto the socket while blender remains open.
