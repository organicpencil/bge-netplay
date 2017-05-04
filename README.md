# bge-netplay
A framework for multiplayer games in Blender.

**Features**
- Reliable/unreliable UDP using enet
- Reasonably efficient serialization using python-serializer
- Several examples to get you up and running quickly (mileage may vary)

**Requirements**
- Blender 2.77 or newer, UPBGE also supported
- pyenet built against Blender's Python version.  Prebuilt libs here: https://pqftgs.net/downloads/enet/


# Running the examples

Clone the repository
```bash
git clone https://github.com/pqftgs/bge-netplay.git
```
Copy the appropriate pyenet lib to the netplay folder.

On Linux64:
```bash
cd bge-netplay/netplay
wget https://pqftgs.net/downloads/enet/pyenet-1.3.13/enet.cpython-35m-x86_64-linux-gnu.so
```

Now open at least two instances of Blender - client and server - and run the examples!


# 3rd party stuff
- enet - https://github.com/lsalzman/enet
- pyenet - https://github.com/aresch/pyenet
- bitstring - https://github.com/scott-griffiths/bitstring
- python-serializer - https://github.com/pqftgs/python-serializer
