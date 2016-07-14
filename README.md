# bge-netplay
A client-server framework for multiplayer games in Blender.  Only 64 bit Linux is supported at the moment.

**Features**
- Reliable/unreliable UDP using enet
- Reasonably efficient serialization using python-serializer
- Several examples to get you up and running quickly (mileage may vary)

**Requirements**
- Blender 2.77 or newer, UPBGE 0.0.7 or newer
- pyenet built against Blender's Python version


# Running the examples

Clone the repository
```bash
git clone https://github.com/pqftgs/bge-netplay.git
cd bge-netplay
```
Set up the example environment
```bash
./setup_linux64.sh
```

Navigate to the examples folder and fire away!  It's recommended to close blender between server runs, or simply use the standalone player.


**For other platforms you'll need to build pyenet from source**


# 3rd party stuff
- enet - https://github.com/lsalzman/enet
- pyenet - https://github.com/aresch/pyenet
- bitstring - https://github.com/scott-griffiths/bitstring
- python-serializer - https://github.com/pqftgs/python-serializer
- compz - https://github.com/DCubix/Compz
