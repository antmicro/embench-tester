## Embench tester

This project is an open source tool for benchmarking CPU cores available in the [LiteX SoC builder](https://github.com/enjoy-digital/litex)
The cores are tested with the [Embench](https://github.com/embench/embench-iot) open source test suite for embedded systems.
LiteX is a toolset for building Systems-on-a-Chip with many CPU cores and with support for multiple architectures, e.g. RISC-V, OpenPOWER or OpenRISC.

Embench tester project achieves its goal by executing Embench tests on simulated minimalistic SoC designs featuring core designs that the user wants to benchmark.
Once the tests are done, the execution results are provided in absolute and relative forms.
Absolute results show the time that was needed to finish the test, while relative results show performance in relation to the reference Arm Cortex M4 core

## Project files

This project consists of the following files:
* `pylib/run_litex_sim.py` - contains an Embench module enabling LiteX simulation target
* `config/sim` - Embench configuration adding LiteX simulation target
* `sim.py` - contains minimalistic LiteX SoC configuration used in simulation
* `run.py` - script for running benchmarks on a single CPU
* `table_maker.py` - script used to aggregate multiple json results from multiple cores and create .csv and .rst tables summarising all performed tests
* `install.sh` - bash script you can execute to install needed software to perform testing

## Installation

To install LiteX, Embench and all required software run:

```
sudo ./install.sh
export PATH=$PATH:~/.local.bin:$(echo $PWD/riscv64-*/bin/):$PWD/or1k/bin:$PWD/lm32gcc/bin
```

It will install required repositories to curent directory.

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

The results are provided as a set of json files stored in a directory named after the tested CPU.
To create the summarizing tables, run the ``./table_maker.py`` script.
The script will create the following files:

* `relative_results.csv/rst` - aggregated in relation to Arm Cortex M4
* `absolute_results.csv/rst` - aggregated absolute results in ms
* `platform.csv/rst` - contains information about the toolchains, simulators and cores versions used in the benchmark.
