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


def collect_cpu_and_toolchain_data(cpu_report, mode):
    working_dir = os.getcwd()
    d = {}

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

    os.chdir(f'{cpu_report["CPU"]}')
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


def prepare_arguments_for_build_all(soc_kwargs, dict):
    args = argparse.Namespace()
    args.arch = "sim"
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
    args.cpu_mhz = None
    args.warmup_heat = None
    args.timeout = 5
    args.cc = f"{dict['TRIPLE']}-gcc"
    args.cflags = f'-v -nostdinc -I{dict["BUILDINC_DIRECTORY"]} \
-I{dict["CPU_DIRECTORY"]} -I{dict["SOC_DIRECTORY"]}/software/include/base \
-I{dict["SOC_DIRECTORY"]}/software/include -std=gnu99 {dict["CPUFLAGS"]} \
-O2 -ffunction-sections'
    args.user_libs = f'{dict["BUILDINC_DIRECTORY"]}/../libbase/crt0.o \
-L{dict["BUILDINC_DIRECTORY"]} -L{dict["BUILDINC_DIRECTORY"]}/../libbase \
-L{dict["BUILDINC_DIRECTORY"]}/../libm \
-L{dict["BUILDINC_DIRECTORY"]}/../libcompiler_rt \
{dict["BUILDINC_DIRECTORY"]}/../bios/isr.o -lm -lbase-nofloat \
-lcompiler_rt -lgcc'
    args.ldflags = f'-nostdlib -nodefaultlibs -Wl,--verbose {dict["CPUFLAGS"]}\
            -T{dict["BUILDINC_DIRECTORY"]}/../../linker.ld -N'
    args.clean = True
    args.logdir = f'../{soc_kwargs["cpu_type"]}/logs'
    args.builddir = f'../{soc_kwargs["cpu_type"]}/benchmarks'
    args.binary_converter = f'{dict["TRIPLE"]}-objcopy'
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
        '--threads',
        type=int,
        help="Specify number of threads for simulation to run on",
        default=1
    )
    parser.add_argument(
        '--integrated-sram-size',
        help="Specify how big is sram/program stack\n\
When running microwatt set to at least 0x8000",
        default=0x8000
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
    else:
        args.cpu_variant = 'standard'

    soc_kwargs = sim.soc_sdram_argdict(args)
    builder_kwargs = sim.builder_argdict(args)
    builder_kwargs["output_dir"] = soc_kwargs["cpu_type"]
    builder_kwargs["compile_gateware"] = False
    soc_kwargs["opt_level"] = "O3"

    # Create software for simulated SoC
    sim.sim_configuration(args, soc_kwargs, builder_kwargs)

    # Copy universal linker script
    shutil.copy2('./Embench/config/sim/boards/generic/linker.ld',
                 f'./{soc_kwargs["cpu_type"]}/linker.ld')

    cpu_report = {}

    variables = f"./{soc_kwargs['cpu_type']}/software\
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
        collect_cpu_and_toolchain_data(cpu_report, i)

    # Make directories for benchamrks and logs from embench
    if not os.path.exists(f'{soc_kwargs["cpu_type"]}/benchmarks'):
        os.mkdir(f'{soc_kwargs["cpu_type"]}/benchmarks')

    if not os.path.exists(f'{soc_kwargs["cpu_type"]}/logs'):
        os.mkdir(f'{soc_kwargs["cpu_type"]}/logs')

    # Prepare namespace for build_all
    arglist = prepare_arguments_for_build_all(soc_kwargs, cpu_report)
    # Build all benchmarks
    build_all.submodule_main(arglist)

    # Prepare argument namespace for benchmark
    arglist = argparse.Namespace()
    arglist.builddir = f'../{soc_kwargs["cpu_type"]}/benchmarks'
    arglist.logdir = f'../{soc_kwargs["cpu_type"]}/logs'
    arglist.output_format = benchmark_speed.output_format.JSON
    arglist.target_module = 'run_litex_sim'
    arglist.timeout = 7200
    arglist.baselinedir = 'baseline-data'
    arglist.json_comma = False
    arglist.change_dir = False

    remnant = f'--cpu-type {args.cpu_type}'.split()
    remnant.extend(f'--cpu-variant {args.cpu_variant}'.split())
    remnant.extend(f'--threads {args.threads}'.split())
    remnant.extend(f'--integrated-sram-size \
{args.integrated_sram_size}'.split())

    logs_before = set(glob.glob(f'./{soc_kwargs["cpu_type"]}/logs/speed*'))

    # Bench relative speed
    if 'relative' in run_args.benchmark_strategy:
        arglist.absolute = 1
        benchmark_speed.submodule_main(arglist, remnant)
        relative_result_path = f'./{soc_kwargs["cpu_type"]}/result.json'

    # Bench absolute speed
    if 'absolute' in run_args.benchmark_strategy:
        arglist.absolute = 0
        benchmark_speed.submodule_main(arglist, remnant)
        absolute_result_path = f'./{soc_kwargs["cpu_type"]}/result_abs.json'

    # Bench both speed
    if 'both' in run_args.benchmark_strategy:
        arglist.absolute = 2
        benchmark_speed.submodule_main(arglist, remnant)
        relative_result_path = f'./{soc_kwargs["cpu_type"]}/result.json'
        absolute_result_path = f'./{soc_kwargs["cpu_type"]}/result_abs.json'

    # Extract results
    logs_path = f'./{soc_kwargs["cpu_type"]}/logs/speed*'
    logs_new = set(glob.glob(logs_path))-logs_before

    logs_new = sorted(list(logs_new))

    if 'both' in run_args.benchmark_strategy:
        extract_json_results_from_file_to_file(logs_new[0],
                                               relative_result_path,
                                               '"speed results" :\\s*',
                                               '\\s*"speed results"')
        extract_json_results_from_file_to_file(logs_new[0],
                                               absolute_result_path,
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
