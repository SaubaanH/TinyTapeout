# TinyTapeout testbench for 8-bit programmable counter
# Keep the file header/comments from the template; only add the code below.

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

CLK_PERIOD_NS = 10  # 100 MHz sim clock is fine

async def tt_reset(dut):
    """Apply async active-low reset and bring DUT to a known state."""
    dut.rst_n.value = 0
    dut.ena.value   = 1   # enable project so registers update
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await Timer(CLK_PERIOD_NS * 2, units="ns")
    dut.rst_n.value = 1
    # Give it one clock to settle after deassert
    await RisingEdge(dut.clk)

@cocotb.test()
async def test_prog_counter8(dut):
    """Verify async reset, synchronous load, counting, and tri-state outputs."""

    # Start clock
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, units="ns").start())

    # === 1) Async reset ===
    await tt_reset(dut)
    assert int(dut.uo_out.value) == 0, "Counter should be 0 after async reset"

    # uio should be high-Z (oe=0) by default since DRIVE_EN=0
    assert int(dut.uio_oe.value) == 0, "uio_oe should be 0 (Hi-Z) when DRIVE_EN=0"

    # === 2) Synchronous load ===
    LOAD_VAL = 0xA5
    dut.ui_in.value  = LOAD_VAL
    # Set LOAD=1 for exactly one cycle (uio_in[0])
    dut.uio_in.value = (1 << 0)  # LOAD=1, COUNT_EN=0, DRIVE_EN=0
    await RisingEdge(dut.clk)    # capture load at this edge
    # Drop LOAD back to 0
    dut.uio_in.value = 0
    await RisingEdge(dut.clk)

    assert int(dut.uo_out.value) == LOAD_VAL, "Synchronous load failed (uo_out mismatch)"

    # === 3) Counting when enabled ===
    # Enable counting: uio_in[1]=1
    dut.uio_in.value = (1 << 1)  # COUNT_EN=1
    await RisingEdge(dut.clk)
    c1 = int(dut.uo_out.value)
    await RisingEdge(dut.clk)
    c2 = int(dut.uo_out.value)
    assert c2 == ((c1 + 1) & 0xFF), "Counter did not increment by 1"

    # Count a few more and spot-check sequence
    for _ in range(5):
        prev = int(dut.uo_out.value)
        await RisingEdge(dut.clk)
        assert int(dut.uo_out.value) == ((prev + 1) & 0xFF), "Counter sequence error"

    # === 4) Tri-state outputs on uio_* ===
    # First, still Hi-Z because DRIVE_EN=0
    assert int(dut.uio_oe.value) == 0, "uio_oe should be 0 before enabling drive"

    # Now enable tri-state drivers: uio_in[3]=1  (keep COUNT_EN=1 so it keeps ticking)
    dut.uio_in.value = (1 << 1) | (1 << 3)
    await RisingEdge(dut.clk)
    assert int(dut.uio_oe.value) == 0xFF, "uio_oe should be all 1s when DRIVE_EN=1"
    assert int(dut.uio_out.value) == int(dut.uo_out.value), "uio_out should mirror count when driven"

    # Turn drivers back off and verify Hi-Z again via oe
    dut.uio_in.value = (1 << 1)  # disable DRIVE_EN, keep counting
    await RisingEdge(dut.clk)
    assert int(dut.uio_oe.value) == 0, "uio_oe should return to Hi-Z when DRIVE_EN=0"

    # Final quick sanity: load again while enabled
    NEW_LOAD = 0x3C
    dut.ui_in.value  = NEW_LOAD
    dut.uio_in.value = (1 << 0) | (1 << 1)  # LOAD=1, COUNT_EN=1
    await RisingEdge(dut.clk)
    dut.uio_in.value = (1 << 1)            # LOAD=0 again
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value) == NEW_LOAD, "Second synchronous load failed"

    # If we made it here, everything passed