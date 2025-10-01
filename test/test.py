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
    for i in range(7, -1, -1):
        dut.ui_in.value = (int(dut.ui_in.value) & 0b11111011) | (bit(byte, i) << 2)  # sdi=ui_in[2]
        dut.ui_in.value = int(dut.ui_in.value) & 0b11110111  # sclk=0
        await Timer(SCLK_PERIOD // 2, units="ns")
        dut.ui_in.value = int(dut.ui_in.value) | 0b1000      # sclk=1
        await Timer(SCLK_PERIOD // 2, units="ns")
    dut.ui_in.value = int(dut.ui_in.value) & 0b11110111     # leave sclk low


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, CLK_PERIOD, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    if (int(dut.ui_in.value) & 0b10) == 0:
        assert str(dut.uo_out.value) == "zzzzzzzz"
    else:
        assert int(dut.uo_out.value) == 0
    # Load 0xA5 into counter
    val = 0xA5
    await shift_msb_first(dut, val)
    dut.ui_in.value = int(dut.ui_in.value) | 0b1  # load=1
    await RisingEdge(dut.clk)
    dut.ui_in.value = int(dut.ui_in.value) & ~0b1 # load=0
    assert int(dut.uo_out.value) == val

    # Count up
    dut.ui_in.value = int(dut.ui_in.value) | 0b100000  # en=1
    dut.ui_in.value = int(dut.ui_in.value) | 0b10000   # up=1
    await ClockCycles(dut.clk, 4)
    expect = (val + 4) & 0xFF
    assert int(dut.uo_out.value) == expect

    # Count down
    dut.ui_in.value = int(dut.ui_in.value) & ~0b10000  # up=0
    await ClockCycles(dut.clk, 3)
    expect = (expect - 3) & 0xFF
    assert int(dut.uo_out.value) == expect

    # Tri-state test
    dut.ui_in.value = int(dut.ui_in.value) & ~0b10  # oe=0
    await RisingEdge(dut.clk)
    assert str(dut.uo_out.value) == "zzzzzzzz"
    dut.ui_in.value = int(dut.ui_in.value) | 0b10   # oe=1
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == expect