## Embench tester

This project is an open source tool designed for benchmarking CPU cores available in the [LiteX SoC builder](https://github.com/enjoy-digital/litex)
The cores are tested using the using the [Embench](https://github.com/embench/embench-iot) open source test suite for embedded systems.

LiteX is a toolset for System-on-a-Chip designing with many CPU cores designs and multiple architectures e.g. RISC-V, OpenPOWER or OpenRISC.
Embench on the other hand is new open source test suite for embedded systems.
Project achieves its goal by executing Embench tests on simulated minimalistic SoC design, with a core design we want to benchmark.
After execution results are avaiable in absolute and relative form.
Absolute results are time in ms to finish test, and relative is compared to ARM Cortex M4 core.

## Project files

This project consists of the following files:
* `pylib/run_litex_sim.py` - contains an Embench module enabling LiteX simulation target
* `config/sim` - Embench configuration adding LiteX simulation target
* `sim.py` - contains minimalistic LiteX SoC configuration used in simulation
* `run.py` - script for running benchmarks on a single CPU
* `table_maker.py` - script used to aggregate multiple json results from multiple cores and create .csv and .rst tables summerising all tests performed
* `install.sh` - bash script you can execute to install needed software to perform testing

## Instalation

To install LiteX, Embench and all required software run:

```
sudo ./install.sh
export PATH=$PATH:~/.local.bin:$(echo $PWD/riscv64-*/bin/):$PWD/or1k/bin:$PWD/lm32gcc/bin
```

It will install required repositories to curent directory. LiteX will be installed
with --user flag, so it will be avaiable everywhere on your system.

## Usage

To test CPU core run:
```
./run.py --cpu-type <cpu_name>
```

Currently available targets are:

* vexriscv
* serv
* picorv32
* minerva
* cv32e40p
* mor1kx
* microwatt
* lm32


Results are stored in directory named after the tested CPU as a set of json files.
To create summarizing tables run the `./table_maker.py` script.
The script will create the following files:

* `relative_results.csv/rst` - aggregated cores results in relation to ARM Cortex M4
* `absolute_results.csv/rst` - aggregated absolute cores results in ms
* `platform.csv/rst` - contains information about the toolchains, simulators and core versions used in the benchmark.
