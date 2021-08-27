#!/bin/bash
# build essensials     
set -e

sudo apt update
sudo apt install -y gnat-9

# Get Embench
mv third_party/Embench Embench

# Adding integration tools to Embench
mv ./config/sim/ ./Embench/config/
mv ./pylib/run_litex_sim.py ./Embench/pylib/run_litex_sim.py

# LiteX install
mv third_party/litex litex/
mv litex/litex_setup.py .
chmod +x litex_setup.py
./litex_setup.py init install --user

cd third_party

# ghdl download and install
cd ghdl
./configure --prefix=/usr/local
make -j $(nproc)
make install
cd ..

# yosys-gdhl-plugin download and install
cd ghdl-yosys-plugin
make -j $(nproc)
make install
cd ..

cd ..
