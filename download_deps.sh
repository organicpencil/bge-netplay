cd netplay/enet/

rm -rf linux32
mkdir linux32
cd linux32
wget https://dl.dropboxusercontent.com/u/19279604/static/netplay/linux32/enet.cpython-34m.so
cd ..

rm -rf linux64
mkdir linux64
cd linux64
wget https://dl.dropboxusercontent.com/u/19279604/static/netplay/linux64/enet.cpython-34m.so
cd ..

rm -rf windows32
mkdir windows32
cd windows32
wget https://dl.dropboxusercontent.com/u/19279604/static/netplay/windows32/enet.pyd
cd ..
cd ..
cd ..


cd examples/common
wget https://dl.dropboxusercontent.com/u/19279604/static/netplay/bgui.zip
rm -rf bgui
unzip bgui.zip
rm bgui.zip
cd ../../
