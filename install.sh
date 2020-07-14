#!/bin/bash
# build essensials     
set -e

apt-get update
apt-get -y install gnat-8 python3 python3-setuptools make build-essential wget gcc-powerpc64-linux-gnu gcc-powerpc64le-linux-gnu
apt-get -y install bison flex libreadline-dev gawk tcl-dev libffi-dev graphviz xdot pkg-config libboost-system-dev git
apt-get -y install libboost-python-dev libboost-filesystem-dev zlib1g-dev autoconf libevent-dev libjson-c-dev python3-pip
pip3 install gitpython

# Verilator download and build
git clone --branch stable https://github.com/verilator/verilator.git
cd verilator
autoconf
./configure
make -j $(nproc)
make install
cd ..

git clone --branch embench-tester https://github.com/antmicro/embench-iot.git Embench
#
# Adding integration tools to Embench
mv ./config/sim/ ./Embench/config/
mv ./pylib/run_litex_sim.py ./Embench/pylib/run_litex_sim.py

git clone --branch embench-tester https://github.com/antmicro/litex

mv litex/litex_setup.py .
chmod +x litex_setup.py
./litex_setup.py init install --user
./litex_setup.py gcc

# nMigen install
pip3 install git+https://github.com/m-labs/nmigen.git
pip3 install nmigen-yosys

# yosys download and install
git clone https://github.com/YosysHQ/yosys.git
cd yosys
make config-gcc
make -j $(nproc)
make install
cd ..

# ghdl download and install
git clone https://github.com/ghdl/ghdl.git
cd ghdl
./configure --prefix=/usr/local
make -j $(nproc)
make install
cd ..

# yosys-gdhl-plugin download and install
git clone https://github.com/ghdl/ghdl-yosys-plugin.git
cd ghdl-yosys-plugin
make -j $(nproc)
make install
cd ..

# conda download and install  
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
source $HOME/miniconda/bin/activate

# OpenRISC gcc dwonload and install
mkdir or1k 
conda install -y -c timvideos gcc-or1k-elf -p ./or1k
ln -s $PWD/or1k/lib/libmpfr.so.6 $PWD/or1k/lib/libmpfr.so.4

# lm32 gcc download and install
mkdir lm32gcc
conda install -y -c timvideos gcc-lm32-elf  -p ./lm32gcc
ln -s $PWD/lm32gcc/lib/libmpfr.so.6 $PWD/lm32gcc/lib/libmpfr.so.4

