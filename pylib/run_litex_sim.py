#!/usr/bin/env python3


__all__ = [
    'get_target_args',
    'build_benchmark_cmd',
    'decode_results'
]

import argparse
import re

from embench_core import log

cpu_mhz = 1


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
        '--threads',
        type=int,
        default=1
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
                f'{args.cpu_type}/benchmarks/src/{bench}/{bench}.bin',
                '--run-sim=True'])
    cmd.extend(f'--output-dir ./{args.cpu_type}/{bench}'.split())
    cmd.extend(f'--bus-data-width {args.bus_data_width}'.split())
    cmd.extend(f'--use-cache {args.use_cache}'.split())
    cmd.extend(f'--threads {args.threads} --opt-level O3 \
--integrated-sram-size {args.integrated_sram_size}'.split())
    return cmd


def decode_results(stdout_str, stderr_str):
    """Extract the results from the output string of the run. Return the
        elapsed time in milliseconds or zero if the run failed."""

    time_re = re.search('Bench time:(\\d+)', stdout_str, re.S)
    time = int(time_re.group(1))
    if not time:
        log.debug('Warning: Failed to find timing')
        return 0.0

    return time / cpu_mhz / 1000.0
