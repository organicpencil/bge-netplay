ln -s netplay examples/common/netplay

cd netplay/enet/

wget http://pqftgs.net/downloads/netplay/enet.cpython-35m-x86_64-linux-gnu.so

cd ../../examples/common

wget http://pqftgs.net/downloads/netplay/compz.zip
rm -rf compz
unzip compz.zip
rm compz.zip
