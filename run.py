#!/usr/bin/env python3

import os
import subprocess
import argparse
import sim
import re

import shutil
import glob
import json

from git import Repo
from Embench import build_all
from Embench import benchmark_speed


def collect_cpu_and_toolchain_data(cpu_report, mode, test_path):
    working_dir = os.getcwd()
    d = {}

    if (cpu_report["CPU"] == "ibex"):
        os.chdir(f'pythondata-misc-opentitan')
    else:
        os.chdir(f'pythondata-cpu-{cpu_report["CPU"]}')
    repo = Repo(os.getcwd())
    d['CPU'] = {
        cpu_report['CPU']: repo.head.commit.hexsha
    }
    os.chdir(working_dir)

    software_used = {
        'toolchain': f'{cpu_report["TRIPLE"]}-gcc',
        'verilator': 'verilator',
        'yosys': 'yosys',
        'ghdl': 'ghdl'
    }

    for sw, command in software_used.items():
        res = subprocess.run(
            [command, '--version'],
            stdout=subprocess.PIPE
        )
        d[sw] = res.stdout.decode('utf-8').split("Copyright")[0]
        d[sw] = d[sw].replace('\n', ' ')

    os.chdir(f'{test_path}')
    platform_data = open('platform.json', 'w+')
    platform_data.write(json.dumps(d))
    platform_data.close()
    os.chdir(os.pardir)


def extract_json_results_from_file_to_file(path_to_extract, path_to_save,
                                           beg, esc):
    result_f = open(path_to_extract, mode='r')
    content = result_f.read()
    result_f.close()
    match = re.search(f'{beg}({{[\\s\\S]*}}){esc}', content, re.S)

    result_json = open(path_to_save, 'w+')
    result_json.write(match.group(1))
    result_json.close()


def prepare_arguments_for_build_all(soc_kwargs, cpu_par, test_path, cpu_mhz=None, arch="sim"):
    args = argparse.Namespace()
    args.arch = arch
    args.chip = 'generic'
    args.board = 'generic'
    args.env = None
    args.ld = None
    args.cc_define1_pattern = None
    args.cc_define2_pattern = None
    args.cc_incdir_pattern = None
    args.cc_input_pattern = None
    args.cc_output_pattern = None
    args.ld_input_pattern = None
    args.ld_output_pattern = None
    args.dummy_libs = None
    args.cpu_mhz = cpu_mhz
    args.warmup_heat = None
    args.timeout = 5
    args.cc = f"{cpu_par['TRIPLE']}-gcc"
    args.cflags = f'-v -I{cpu_par["BUILDINC_DIRECTORY"]} \
-I{cpu_par["BUILDINC_DIRECTORY"]}/../libc \
-I{cpu_par["CPU_DIRECTORY"]} -I{cpu_par["SOC_DIRECTORY"]}/software/include \
-I{cpu_par["SOC_DIRECTORY"]}/software/libcomm \
-std=gnu99 {cpu_par["CPUFLAGS"]} -I{cpu_par["PICOLIBC_DIRECTORY"]}/newlib/libc/tinystdio \
-I{cpu_par["PICOLIBC_DIRECTORY"]}/newlib/libc/include -O2 -ffunction-sections'
    args.user_libs = f'{cpu_par["BUILDINC_DIRECTORY"]}/../bios/crt0.o \
-L{cpu_par["BUILDINC_DIRECTORY"]} -L{cpu_par["BUILDINC_DIRECTORY"]}/../libc \
-L{cpu_par["BUILDINC_DIRECTORY"]}/../libcompiler_rt \
-L{cpu_par["BUILDINC_DIRECTORY"]}/../libcomm \
{cpu_par["BUILDINC_DIRECTORY"]}/../bios/isr.o \
-lcompiler_rt -lc -lcomm -lgcc'
    args.ldflags = f'-nostdlib -nodefaultlibs -nolibc -Wl,--verbose {cpu_par["CPUFLAGS"]}\
            -T{cpu_par["BUILDINC_DIRECTORY"]}/../../linker.ld -N'
    args.clean = True
    args.logdir = f'../{test_path}/logs'
    args.builddir = f'../{test_path}/benchmarks'
    args.binary_converter = f'{cpu_par["TRIPLE"]}-objcopy'
    args.verbose = None
    return args


def run_arg_parser(parser):
    parser.add_argument(
        '--cpu-type',
        type=str,
        help="CPU type to run benchmarks on",
        required=True
    )
    parser.add_argument(
        '--cpu-variant',
        type=str,
        help="CPU variant to run benchmarks on\n\
When running microwatt set to standard+ghdl"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
    )
    parser.add_argument(
        '--threads',
        type=int,
        help="Specify number of threads for simulation to run on",
        default=1
    )
    parser.add_argument(
        '--arty',
        type=str,
        help="Run benchmarks on arty FPGA",
        default=False
    )
    parser.add_argument(
        '--integrated-sram-size',
        help="Specify how big is sram/program stack\n\
When running microwatt set to at least 0x8000",
        default=0x8000
    )
    parser.add_argument(
        '--bus-data-width',
        help="Set SoC internal bus data width\n\
Only Rocket and Microwatt should use 64 bit busses",
        default=32
    )
    parser.add_argument(
        "--use-cache",
        default=False,
        help="Use caches in rocket chip"
    )
    parser.add_argument(
        '--benchmark-strategy',
        help="Set to absolute, relative or combination of both, to\
test performance in given mode",
        required=True,
        choices=['absolute', 'relative', 'both']
    )


def main():
    # Reading provided arguments


    parser = argparse.ArgumentParser(
            description='Build benchmarks for given cpu type')
    run_arg_parser(parser)
    run_args = parser.parse_args()

    internal_parser = argparse.ArgumentParser()

    sim.sim_args(internal_parser)
    sim.builder_args(internal_parser)
    sim.soc_sdram_args(internal_parser)
    args, rest = internal_parser.parse_known_args()
    args.integrated_sram_size = run_args.integrated_sram_size

    if (args.cpu_type == 'microwatt'):
        args.cpu_variant = 'standard+ghdl'
    elif (args.cpu_type == 'blackparrot'):
        args.cpu_variant = 'sim'
    else:
        args.cpu_variant = 'standard'

    soc_kwargs = sim.soc_sdram_argdict(args)
    test_path = f"{soc_kwargs['cpu_type']}_{soc_kwargs['cpu_variant']}" + \
                f"_{args.bus_data_width}_{args.use_cache}"

    builder_kwargs = sim.builder_argdict(args)
    builder_kwargs["output_dir"] = test_path
    builder_kwargs["compile_gateware"] = False
    soc_kwargs["opt_level"] = "O3"


    # Create software for simulated SoC
    if not args.arty:
        sim.sim_configuration(args, soc_kwargs, builder_kwargs, test_path)
    else:
        sim.arty_configuration(args, soc_kwargs, builder_kwargs, test_path)

    # Copy universal linker script
    shutil.copy2('./Embench/config/sim/boards/generic/linker.ld',
                 f'./{test_path}/linker.ld')

    cpu_report = {}

    variables = f"./{test_path}/software\
/include/generated/variables.mak"
    with open(os.path.abspath(variables)) as f:
        for line in f:
            line = line.rstrip()
            test = line.split()
            if (len(test) > 1 and test[0] == "export"):
                continue
            (key, val) = line.split("=", 1)
            cpu_report[key] = val

    # Collect imformation about cpu repo and toolchain version
    for i in run_args.benchmark_strategy:
        collect_cpu_and_toolchain_data(cpu_report, i, test_path)

    # Make directories for benchamrks and logs from embench
    if not os.path.exists(f'{test_path}/benchmarks'):
        os.mkdir(f'{test_path}/benchmarks')

    if not os.path.exists(f'{test_path}/logs'):
        os.mkdir(f'{test_path}/logs')

    # Prepare namespace for build_all
    arch = "arty" if args.arty else "sim"
    cpu_mhz = 100 if args.arty else None
    arglist = prepare_arguments_for_build_all(soc_kwargs, cpu_report, test_path, cpu_mhz, arch)
    # Build all benchmarks
    build_all.submodule_main(arglist)

    # Prepare argument namespace for benchmark
    arglist = argparse.Namespace()
    arglist.builddir = f'../{test_path}/benchmarks'
    arglist.logdir = f'../{test_path}/logs'
    arglist.output_format = benchmark_speed.output_format.JSON
    if not args.arty:
        arglist.target_module = 'run_litex_sim'
    else:
        arglist.target_module = 'run_litex_arty'
    arglist.timeout = 7200
    arglist.baselinedir = 'baseline-data'
    arglist.json_comma = False
    arglist.change_dir = False
    arglist.sim_parallel = False

    remnant = f'--cpu-type {args.cpu_type}'.split()
    remnant.extend(f'--cpu-variant {args.cpu_variant}'.split())
    if not args.arty:
        remnant.extend(f'--threads {args.threads}'.split())
    remnant.extend(f'--bus-data-width {args.bus_data_width}'.split())
    remnant.extend(f'--use-cache {args.use_cache}'.split())
    remnant.extend(f'--output-dir {test_path}'.split())
    remnant.extend(f'--integrated-sram-size \
{args.integrated_sram_size}'.split())

    logs_before = set(glob.glob(f'./{test_path}/logs/speed*'))

    # Bench relative speed
    if 'relative' in run_args.benchmark_strategy:
        arglist.absolute = 1
        benchmark_speed.submodule_main(arglist, remnant)
        relative_result_path = f'./{test_path}/result.json'

    # Bench absolute speed
    if 'absolute' in run_args.benchmark_strategy:
        arglist.absolute = 0
        benchmark_speed.submodule_main(arglist, remnant)
        absolute_result_path = f'./{test_path}/result_abs.json'

    # Bench both speed
    if 'both' in run_args.benchmark_strategy:
        arglist.absolute = 2
        benchmark_speed.submodule_main(arglist, remnant)
        relative_result_path = f'./{test_path}/result.json'
        absolute_result_path = f'./{test_path}/result_abs.json'

    # Extract results
    logs_path = f'./{test_path}/logs/speed*'
    logs_new = set(glob.glob(logs_path))-logs_before

    logs_new = sorted(list(logs_new))

    if 'both' in run_args.benchmark_strategy:
        extract_json_results_from_file_to_file(logs_new[0],
                                               absolute_result_path,
                                               '"speed results" :\\s*',
                                               '\\s*"speed results"')
        extract_json_results_from_file_to_file(logs_new[0],
                                               relative_result_path,
                                               '}\\s*"speed results" :\\s*',
                                               '\\s*All')

    elif 'relative' in run_args.benchmark_strategy:
        extract_json_results_from_file_to_file(logs_new[0],
                                               relative_result_path)

    elif 'absolute' in run_args.benchmark_strategy:
        extract_json_results_from_file_to_file(logs_new[0],
                                               absolute_result_path)


if __name__ == '__main__':
    main()
