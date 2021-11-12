#!/usr/bin/env python3


__all__ = [
    'get_target_args',
    'build_benchmark_cmd',
    'decode_results'
]

import argparse
import re
import io
import subprocess

from embench_core import log

cpu_mhz = 100


def get_target_args(remnant):
    """Parse left over arguments"""
    parser = argparse.ArgumentParser(
            description='Get simulation specific arguments')

    parser.add_argument(
        '--cpu-type',
        type=str,
        help=""
    )
    parser.add_argument(
        '--cpu-variant',
        type=str,
        help="",
        default="standard"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
    )
    parser.add_argument(
        '--integrated-sram-size',
        type=int,
        default=0x200
    )
    parser.add_argument(
        '--bus-data-width',
        type=int,
        default=32
    )
    parser.add_argument(
        "--use-cache",
        default=False,
        help="Use caches in rocket chip"
    )
    return parser.parse_args(remnant)


def build_benchmark_cmd(bench, args):
    """Construct the command to run the benchmark.  "args" is a
        namespace with target specific arguments"""

    cmd = ['./sim.py']
    cmd.extend(f'--cpu-type {args.cpu_type}'.split())
    cmd.extend(f'--cpu-variant {args.cpu_variant}'.split())
    cmd.extend(['--ram-init',
                f'{args.output_dir}/benchmarks/src/{bench}/{bench}.bin',
                '--run=True'])
    cmd.extend(f'--output-dir ./{args.output_dir}'.split())
    cmd.extend(f'--bus-data-width {args.bus_data_width}'.split())
    cmd.extend(f'--use-cache {args.use_cache}'.split())
    cmd.extend(f'--arty=True'.split())
    cmd.extend(f'--integrated-sram-size {args.integrated_sram_size}'.split())
    return cmd


def decode_results(stdout_str, stderr_str):
    """Extract the results from the output string of the run. Return the
        elapsed time in milliseconds or zero if the run failed."""

    proc = subprocess.Popen(["./terminal.py", "--speed", "115200", "/dev/ttyUSB1"], stdout=subprocess.PIPE)

    line = b""
    while True:
        c =  proc.stdout.read(1)
        if c != b'\n':
            line += c
        else:
            print(line.decode("utf-8", errors="ignore"))
            line = line.decode("utf-8", errors="ignore")
            time_re = re.search('Bench time:(\\d+)', line, re.S)
            if time_re:
                time = int(time_re.group(1))
                proc.kill()
                return time / cpu_mhz / 1000.0
            line = b''

    raise
