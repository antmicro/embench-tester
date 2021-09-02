#!/usr/bin/env python3

import argparse
import os

from migen import *  # noqa: F403

from litex.build.generic_platform import *  # noqa: F403
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.common import *  # noqa: F403
from litex.soc.integration.soc_core import *  # noqa: F403
from litex.soc.integration.soc_sdram import *  # noqa: F403
from litex.soc.integration.builder import *  # noqa: F403
from litex.soc.integration.soc import *  # noqa: F403
from litex.soc.interconnect.csr import *  # noqa: F403
from litex.soc.cores.bitbang import *  # noqa: F403
from litex.soc.cores.cpu import CPUS


_io = [
    ("sys_clk", 0, Pins(1)),  # noqa: F405
    ("sys_rst", 0, Pins(1)),  # noqa: F405
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),  # noqa: F405
        Subsignal("source_ready", Pins(1)),  # noqa: F405
        Subsignal("source_data", Pins(8)),  # noqa: F405
        Subsignal("sink_valid", Pins(1)),  # noqa: F405
        Subsignal("sink_ready", Pins(1)),  # noqa: F405
        Subsignal("sink_data", Pins(8)), ),  # noqa: F405
]


class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)


class Supervisor(Module, AutoCSR):  # noqa: F405
    def __init__(self):
        self._finish = CSR()    # controlled from CPU  # noqa: F405
        self.finish = Signal()  # controlled from logic  # noqa: F405
        self.sync += If(self._finish.re | self.finish, Finish())  # noqa: F405


class SimSoC(SoCCore):  # noqa: F405
    def __init__(self, **kwargs):
        platform = Platform()
        sys_clk_freq = int(1e6)

        # SoCCore -------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,  # noqa: F405
                         ident="LiteX Simulation",
                         ident_version=True, **kwargs)

        # Supervisor ----------------------------------------------------------
        self.submodules.supervisor = Supervisor()
        self.add_csr("supervisor")

        # CRG -----------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))  # noqa: F405


def sim_args(parser):
    parser.add_argument("--threads",
                        default=1,
                        help="Set number of threads (default=1)")
    parser.add_argument("--rom-init",
                        default=None,
                        help="rom_init file")
    parser.add_argument("--ram-init",
                        default=None,
                        help="ram_init file")
    parser.add_argument("--trace",
                        action="store_true",
                        help="Enable Tracing")
    parser.add_argument("--trace-fst",
                        action="store_true",
                        help="Enable FST tracing (default=VCD)")
    parser.add_argument("--trace-start",
                        default=0,
                        help="Cycle to start tracing")
    parser.add_argument("--trace-end",
                        default=-1,
                        help="Cycle to end tracing")
    parser.add_argument("--opt-level",
                        default="O3",
                        help="Compilation optimization level")
    parser.add_argument("--run-sim",
                        default=False,
                        help="True to simulate")
    parser.add_argument("--use-cache",
                        default=False,
                        help="Use caches in rocket chip")


def sim_configuration(args, soc_kwargs, builder_kwargs):

    # Configuration -----------------------------------------------------------

    sim_config = SimConfig(default_clk="sys_clk")
    cpu = CPUS[soc_kwargs.get("cpu_type", "vexriscv")]
    if soc_kwargs["uart_name"] == "serial":
        soc_kwargs["uart_name"] = "sim"
        sim_config.add_module("serial2console", "serial")
    soc_kwargs['integrated_rom_size'] = 0x10000
    if args.rom_init:
        soc_kwargs["integrated_rom_init"] = get_mem_data(  # noqa: F405
                args.rom_init, cpu.endianness)
    soc_kwargs["integrated_main_ram_size"] = 0x10000000  # 256 MB
    if args.ram_init is not None:
        soc_kwargs["integrated_main_ram_init"] = get_mem_data(  # noqa: F405
                args.ram_init, cpu.endianness)

    # SoC ---------------------------------------------------------------------
    if args.cpu_type == 'rocket' and not args.use_cache:
        soc_kwargs["user_override"] = {"main_ram": 0x40000000}
    soc = SimSoC(
        **soc_kwargs)
    if args.cpu_type == 'rocket' and args.use_cache:
        for bus in soc.cpu.memory_buses:
            wb = wishbone.Interface(data_width=bus.data_width,
                    adr_width=bus.address_width-log2_int(bus.data_width//8))
            conv = ResetInserter()(axi.AXI2Wishbone(bus, wb, base_address=0))
            soc.submodules += conv
            soc.bus.add_master(name="attached memory bus {}".format(wb), master=wb)

    if args.ram_init is not None:
        soc.add_constant("ROM_BOOT_ADDRESS", soc.mem_map["main_ram"])
    # Build/Run ---------------------------------------------------------------

    builder = Builder(soc, **builder_kwargs)  # noqa: F405
    vns = builder.build(run=False, threads=args.threads,  # noqa: F841
                        sim_config=sim_config,
                        opt_level=args.opt_level,
                        trace=args.trace,
                        trace_fst=args.trace_fst,
                        trace_start=int(args.trace_start),
                        trace_end=int(args.trace_end),
                        interactive=False)
    if args.run_sim:
        builder.build(build=False, threads=args.threads,
                      sim_config=sim_config,
                      opt_level=args.opt_level,
                      trace=args.trace,
                      trace_fst=args.trace_fst,
                      trace_start=int(args.trace_start),
                      trace_end=int(args.trace_end),
                    interactive=False)


def main():
    print(os.getcwd())

    parser = argparse.ArgumentParser(
        description="Generic LiteX SoC Simulation")
    builder_args(parser)  # noqa: F405
    soc_sdram_args(parser)  # noqa: F405
    sim_args(parser)  # noqa: F405
    args = parser.parse_args()

    soc_kwargs = soc_sdram_argdict(args)  # noqa: F405
    builder_kwargs = builder_argdict(args)  # noqa: F405

    sim_configuration(args, soc_kwargs, builder_kwargs)


if __name__ == "__main__":
    main()
