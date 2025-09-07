#!/bin/bash

set -e

echo "Cai dat package cho embedded linux..."

sudo apt update

echo "Cai dat build tools..."
sudo apt install -y build-essential cmake pkg-config git

echo "Cai dat Boost libraries..."
sudo apt install -y libboost-all-dev libboost-system-dev libboost-thread-dev

echo "Cai dat OpenCV..."
sudo apt install -y libopencv-dev libopencv-contrib-dev

echo "Cai dat CURL..."
sudo apt install -y libcurl4-openssl-dev

echo "Cai dat ncurses cho FTXUI..."
sudo apt install -y libtinfo-dev libncurses-dev

if apt-cache show nlohmann-json3-dev >/dev/null 2>&1; then
    echo "Cai dat nlohmann-json..."
    sudo apt install -y nlohmann-json3-dev
fi

echo "Hoan thanh cai dat!"
echo "Chay lenh: mkdir build && cd build && cmake .. && make"