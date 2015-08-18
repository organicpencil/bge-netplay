# bge-netplay
A library for building multiplayer prototypes in Blender's built-in game engine.

Documentation and examples are lacking.  The API is subject to change.  *I wouldn't use it yet.*

**Only the minesweeper example is kept up-to-date.  The others may not work.**

What it does:
- Handle data transfer and connection management using ENet
- Abstract things like input bitmasks and remote procedure calls
- Gives the developer control over what kind of data is sent (for the most part)

What it doesn't do:
- Automatic multiplayer.  The developer must have intermediate Python skills.
- Overcomplicate things.  Stuff like audio isn't abstracted, so your BGE knowledge still applies.
- Compete.  This is intended for prototyping, so expect bugs/slowness/security issues.
- Work on MacOS (yet)



#Running the examples
**Blender 2.74+ is recommended, although it should theoretically work back to version 2.71**

Clone the repository
```
git clone https://github.com/pqftgs/bge-netplay.git
cd bge-netplay
```
Set up dependencies
```
./download_deps.sh
```
