ln -s netplay examples/common/netplay

cd netplay/enet/

wget https://pqftgs.net/downloads/netplay/enet.cpython-35m.so.linux64
mv enet.cpython-35m.so.linux64 enet.cpython-35m.so

cd ../../examples/common

wget https://pqftgs.net/downloads/netplay/bgui.zip
rm -rf bgui
unzip bgui.zip
rm bgui.zip