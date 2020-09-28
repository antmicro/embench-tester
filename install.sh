#!/bin/bash
# build essensials     
set -e

sudo apt-get update
sudo apt-get -y install gnat-8 python3 python3-setuptools make build-essential wget gcc-powerpc64-linux-gnu gcc-powerpc64le-linux-gnu
sudo apt-get -y install bison flex libreadline-dev gawk tcl-dev libffi-dev graphviz xdot pkg-config libboost-system-dev git libfl-dev
sudo apt-get -y install libboost-python-dev libboost-filesystem-dev zlib1g-dev autoconf libevent-dev libjson-c-dev python3-pip
sudo pip3 install gitpython

# Verilator download and build
git clone --branch stable https://github.com/verilator/verilator.git
cd verilator
autoconf
./configure
make -j $(nproc)
sudo make install
cd ..

git clone --branch embench-tester https://github.com/antmicro/embench-iot.git Embench
#
# Adding integration tools to Embench
mv ./config/sim/ ./Embench/config/
mv ./pylib/run_litex_sim.py ./Embench/pylib/run_litex_sim.py

# LiteX install
git clone --branch embench-tester https://github.com/antmicro/litex
mv litex/litex_setup.py .
chmod +x litex_setup.py
./litex_setup.py init install --user

# nMigen install
pip3 install git+https://github.com/m-labs/nmigen.git
pip3 install nmigen-yosys

cd third_party
# yosys download and install
cd yosys
make config-gcc
make -j $(nproc)
sudo make install
cd ..

# ghdl download and install
cd ghdl
./configure --prefix=/usr/local
make -j $(nproc)
sudo make install
cd ..

# yosys-gdhl-plugin download and install
cd ghdl-yosys-plugin
make -j $(nproc)
sudo make install
cd ..

cd ..
# conda download and install  
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
export PATH=$PATH:$HOME/miniconda/bin

# OpenRISC gcc dwonload and install
mkdir or1k 
conda install -y -c timvideos gcc-or1k-elf-newlib -p ./or1k

# lm32 gcc download and install
mkdir lm32gcc
conda install -y -c timvideos gcc-lm32-elf-newlib=8  -p ./lm32gcc

# RISC-V gcc download and install
mkdir riscv64
conda install -y -c timvideos gcc-riscv64-elf-newlib  -p ./riscv64

# OpenPOWER gcc download and install
mkdir ppc64le
conda install -y -c timvideos gcc-ppc64le-linux-musl  -p ./ppc64le
