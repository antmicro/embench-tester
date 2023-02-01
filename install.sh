#!/bin/bash
# build essensials
set -e
set -x

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
./litex_setup.py --init --install --user --dev --config full

# apply cpu patches
quilt push -a

cd third_party

# yosys install
cd yosys
make config-gcc
echo -n "PREFIX := $BASE_DIR/env/conda/envs/embench-tester" >> Makefile.conf
make -j $(nproc)
make install
cd ..

#verilator install
cd verilator
autoconf
./configure --prefix=$BASE_DIR/env/conda/envs/embench-tester
make -j $(nproc)
make install
cd ..

# ghdl download and install
cd ghdl
./configure --prefix=$BASE_DIR/env/conda/envs/embench-tester
make -j $(nproc)
make install
cd ..

# ghdl-yosys-plugin download and install
cd ghdl-yosys-plugin
make -j $(nproc)
make install
cd ..

cd ..
