#!/bin/bash
# build essensials
set -e

sudo apt update
sudo apt install -y gnat

BASE_DIR=$PWD

# Get Embench
cp -r third_party/Embench Embench

# Adding integration tools to Embench
cp -r ./config/* ./Embench/config/
cp -r ./pylib/* ./Embench/pylib/

# LiteX install
cp -r third_party/litex litex/
cp litex/litex_setup.py .
chmod +x litex_setup.py
./litex_setup.py init install --user

cd third_party

# ghdl download and install
cd ghdl
./configure --prefix=$BASE_DIR/env/conda/envs/embench-tester/bin
make -j $(nproc)
make install
cd ..

# yosys-gdhl-plugin download and install
cd ghdl-yosys-plugin
make -j $(nproc)
make install
cd ..

cd ..
