# bge-netplay
A library for building multiplayer prototypes in Blender's built-in game engine.

**Only the minesweeper example is kept up-to-date.  The others may not work.**

Documentation and examples are lacking.  The API is subject to change.  *I wouldn't use it yet.*

What it does:
- Handle connections
- Abstract things like input bitmasks and remote procedure calls.
- (Sort of) forces you into a certain design pattern.

What it doesn't do:
- Automatic multiplayer.  The developer must have basic programming knowledge to use this library.
- Compete with commercial solutions.  This is intended for prototyping.  Expect bugs and slowness.
- Work on MacOS or Windows64 (yet)



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
