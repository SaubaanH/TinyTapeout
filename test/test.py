# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, Timer

CLK_PERIOD = 20
SCLK_PERIOD = 40

def bit(val, n):
    return (val >> n) & 1

async def shift_msb_first(dut, byte):
    """Shift 8 bits MSB-first into ui_in[2] using ui_in[3] as sclk."""
    for i in range(7, -1, -1):
        # drive sdi = ui_in[2]
        dut.ui_in.value = (int(dut.ui_in.value) & 0b11111011) | (bit(byte, i) << 2)
        # sclk = 0
        dut.ui_in.value = int(dut.ui_in.value) & 0b11110111
        await Timer(SCLK_PERIOD // 2, units="ns")
        # sclk = 1
        dut.ui_in.value = int(dut.ui_in.value) | 0b1000
        await Timer(SCLK_PERIOD // 2, units="ns")
    # leave sclk low
    dut.ui_in.value = int(dut.ui_in.value) & 0b11110111

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # start main clock
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD, units="ns").start())

    # reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # enable OE so outputs are driven
    dut.ui_in.value = int(dut.ui_in.value) | 0b10
    await RisingEdge(dut.clk)

    # after reset, counter should be 0
    assert int(dut.uo_out.value) == 0

    # ------------------------------------------------------
    # Load 0xA5 into counter
    # ------------------------------------------------------
    val = 0xA5
    await shift_msb_first(dut, val)
    # set load=1 (ui_in[0])
    dut.ui_in.value = int(dut.ui_in.value) | 0b1
    await RisingEdge(dut.clk)
    dut.ui_in.value = int(dut.ui_in.value) & ~0b1
    await RisingEdge(dut.clk)

    # ensure OE=1 before checking
    dut.ui_in.value = int(dut.ui_in.value) | 0b10
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == val

    # ------------------------------------------------------
    # Count up by 4
    # ------------------------------------------------------
    dut.ui_in.value = int(dut.ui_in.value) | 0b100000  # en=1
    dut.ui_in.value = int(dut.ui_in.value) | 0b10000   # up=1
    await ClockCycles(dut.clk, 4)
    expect = (val + 4) & 0xFF
    assert int(dut.uo_out.value) == expect

    # ------------------------------------------------------
    # Count down by 3
    # ------------------------------------------------------
    dut.ui_in.value = int(dut.ui_in.value) & ~0b10000  # up=0
    await ClockCycles(dut.clk, 3)
    expect = (expect - 3) & 0xFF
    assert int(dut.uo_out.value) == expect

    # ------------------------------------------------------
    # Tri-state test
    # ------------------------------------------------------
    dut.ui_in.value = int(dut.ui_in.value) & ~0b10  # oe=0
    await RisingEdge(dut.clk)
    assert str(dut.uo_out.value) == "zzzzzzzz"

    dut.ui_in.value = int(dut.ui_in.value) | 0b10   # oe=1
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == expect