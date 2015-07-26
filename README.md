# bge-netplay
A library for building multiplayer prototypes in Blender's built-in game engine.

**Only the minesweeper example is kept up-to-date with current.  The others may not work.**

Documentation and examples are lacking.  The API is subject to change.  *I wouldn't use it yet.*

What it does:
- Handle connections
- Abstract things like input bitmasks and creating remote procedure calls.
- (Sort of) forces you into a certain design pattern.

What it doesn't do:
- Automatic multiplayer.  The developer must have basic programming knowledge to use this library.
- Provide common functions like chat, physics, and movement.  You can find such things in the examples.
- Work on MacOS or Windows64 (yet)



#Running the examples
**Blender 2.74+ is recommended, although it should theoretically work back to version 2.71**

Clone the repository
```
git clone https://github.com/pqftgs/bge-netplay.git
cd bge-netplay
```
Symlink or copy the netplay library to examples/common/
```
ln -rs netplay examples/common/netplay
```
Download extra dependencies (bgui and enet)
```
./download_deps.sh
```
