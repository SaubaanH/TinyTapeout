# ------------------------------------------------------------------------------
# Cocotb tests for the 8-bit programmable counter
# Only this file and project.v are edited.
#
# Test plan:
#   1) Asynchronous reset clears both loader and counter.
#   2) Shift a known byte (0xA5) MSB-first via (sclk,sdi); pulse load on clk↑;
#      expect counter to equal 0xA5.
#   3) Count up for N cycles with en=1, verify result.
#   4) Count down for M cycles, verify wrap-around arithmetic.
#   5) Tri-state: when oe=0, io_oeb must be all 1's; when oe=1, all 0's.
# ------------------------------------------------------------------------------

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.binary import BinaryValue

CLK_PERIOD_NS = 20   # 50 MHz "clk"
SCLK_PERIOD_NS = 40  # 25 MHz "sclk" (independent of main clk)


def bit(val, n):
    return (val >> n) & 1


async def pulse(dut, sig, cycles=1):
    # Helper for pulsing boolean control signals for a given number of clk edges
    for _ in range(cycles):
        sig.value = 1
        await RisingEdge(dut.io_in[0])  # main clk
        sig.value = 0
        await RisingEdge(dut.io_in[0])


async def shift_msb_first(dut, byte):
    """Shift 8 bits MSB-first into (sdi on io_in[4]) using sclk on io_in[5]."""
    for i in range(7, -1, -1):
        dut.io_in[4].value = bit(byte, i)   # sdi
        # sclk rising edge captures sdi into MSB of load_reg
        dut.io_in[5].value = 0
        await Timer(SCLK_PERIOD_NS // 2, units="ns")
        dut.io_in[5].value = 1
        await Timer(SCLK_PERIOD_NS // 2, units="ns")
    dut.io_in[5].value = 0  # leave sclk low


@cocotb.test()
async def test_counter_program_load_and_tristate(dut):
    # Shortcuts to the io_in bits (readable names)
    clk    = dut.io_in[0]
    arst_n = dut.io_in[1]
    load   = dut.io_in[2]
    oe     = dut.io_in[3]
    sdi    = dut.io_in[4]
    sclk   = dut.io_in[5]
    up     = dut.io_in[6]
    en     = dut.io_in[7]

    # Initialize inputs
    for i in range(8):
        dut.io_in[i].value = 0

    # Start the main counter clock
    cocotb.start_soon(Clock(clk, CLK_PERIOD_NS, units="ns").start())

    # ---------------------------
    # 1) Asynchronous reset
    # ---------------------------
    arst_n.value = 0
    await Timer(2 * CLK_PERIOD_NS, units="ns")
    arst_n.value = 1
    await RisingEdge(clk)
    # On reset deassertion, counter should be 0.
    assert int(dut.io_out.value) == 0, "Counter did not reset to 0"

    # ---------------------------
    # 2) Shift 0xA5 and load it
    # ---------------------------
    val = 0xA5
    await shift_msb_first(dut, val)

    # Synchronous load on next clk↑ (load=1 for one cycle)
    await pulse(dut, load, cycles=1)
    assert int(dut.io_out.value) == val, f"Load failed: got {int(dut.io_out.value):02X}"

    # ---------------------------
    # 3) Count up
    # ---------------------------
    up.value = 1
    en.value = 1
    steps_up = 5
    for _ in range(steps_up):
        await RisingEdge(clk)
    expect_up = (val + steps_up) & 0xFF
    assert int(dut.io_out.value) == expect_up, "Up-counting mismatch"

    # ---------------------------
    # 4) Count down
    # ---------------------------
    up.value = 0
    steps_down = 9
    for _ in range(steps_down):
        await RisingEdge(clk)
    expect_down = (expect_up - steps_down) & 0xFF
    assert int(dut.io_out.value) == expect_down, "Down-counting mismatch"

    # ---------------------------
    # 5) Tri-state behaviour
    # ---------------------------
    # When oe=0, all io_oeb bits must be 1 (high-Z)
    oe.value = 0
    await RisingEdge(clk)
    oeb_now = int(dut.io_oeb.value)
    assert oeb_now == 0xFF, f"Expected io_oeb=0xFF when oe=0, got 0x{oeb_now:02X}"

    # When oe=1, io_oeb bits must be 0 (actively driving)
    oe.value = 1
    await RisingEdge(clk)
    oeb_now = int(dut.io_oeb.value)
    assert oeb_now == 0x00, f"Expected io_oeb=0x00 when oe=1, got 0x{oeb_now:02X}"

    # Final sanity: counter still enabled and ticking down
    await RisingEdge(clk)
    assert int(dut.io_out.value) == ((expect_down - 1) & 0xFF)