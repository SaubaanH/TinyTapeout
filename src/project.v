//------------------------------------------------------------------------------
// 8-bit programmable binary counter for TinyTapeout (ttsky-verilog-template)
// Requirements satisfied:
//   • Asynchronous reset  (active-low on io_in[1])
//   • Synchronous load    (load from an 8-bit shift-register)
//   • Tri-state outputs   (controlled via io_oeb)
// Interface (using the stock TinyTapeout "io_*" ports):
//   io_in[0] : clk           - counter clock (rising edge)
//   io_in[1] : arst_n        - asynchronous reset (active LOW)
//   io_in[2] : load          - synchronous load strobe; sample on clk↑
//   io_in[3] : oe            - output enable; 1 = drive uo, 0 = hi-Z
//   io_in[4] : sdi           - serial data input for the load value (MSB-first)
//   io_in[5] : sclk          - shift clock for the loader (rising edge active)
//   io_in[6] : up            - 1 = count up, 0 = count down
//   io_in[7] : en            - counter enable
//
// Loading protocol:
//   Shift 8 bits MSB-first into an internal register using (sclk,sdi).
//   Then assert io_in[2] = 1 for one clk↑ to synchronously load that value
//   into the counter.
//------------------------------------------------------------------------------

module project (
    input  wire [7:0] io_in,   // inputs
    output wire [7:0] io_out,  // outputs
    output wire [7:0] io_oeb   // output enable: 1 = hi-Z, 0 = drive
);

    // Named wires for clarity
    wire clk     = io_in[0];
    wire arst_n  = io_in[1];
    wire load    = io_in[2];
    wire oe      = io_in[3];
    wire sdi     = io_in[4];
    wire sclk    = io_in[5];
    wire up      = io_in[6];
    wire en      = io_in[7];

    // Internal registers
    reg  [7:0] load_reg;    // holds the value shifted in over (sclk,sdi)
    reg  [7:0] count_q;     // the 8-bit counter

    // ----------------------
    // Async reset & loader
    // ----------------------
    // Shift in MSB-first on rising edge of sclk.
    // Asynchronous reset clears the loader as well.
    always @(posedge sclk or negedge arst_n) begin
        if (!arst_n) begin
            load_reg <= 8'h00;
        end else begin
            // New bit enters MSB so that MSB-first serial writes land in place.
            load_reg <= {sdi, load_reg[7:1]};
        end
    end

    // ----------------------
    // Counter with:
    //  - async reset (active-low)
    //  - synchronous load
    //  - up/down and enable
    // ----------------------
    always @(posedge clk or negedge arst_n) begin
        if (!arst_n) begin
            count_q <= 8'h00;
        end else if (load) begin
            count_q <= load_reg;           // synchronous parallel load
        end else if (en) begin
            count_q <= up ? (count_q + 8'd1) : (count_q - 8'd1);
        end
    end

    // Drive the user outputs with tri-state control.
    // io_oeb uses "1 = hi-Z, 0 = drive". Replicate ~oe across all 8 bits.
    assign io_out = count_q;
    assign io_oeb = {8{~oe}};

endmodule