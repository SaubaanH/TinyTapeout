// TinyTapeout Sky130 – 8-bit programmable counter
// Features: async reset (active-low), synchronous load, tri-state outputs on uio_*

module project (
    input            clk,      // clock
    input            rst_n,    // asynchronous, active-low reset
    input            ena,      // high when this project is selected (TT mux)
    input      [7:0] ui_in,    // dedicated inputs  (load value)
    output     [7:0] uo_out,   // dedicated outputs (mirrors count for easy viewing)
    input      [7:0] uio_in,   // bidirectional inputs
    output     [7:0] uio_out,  // bidirectional outputs
    output     [7:0] uio_oe    // bidirectional output enables (1=drive, 0=high-Z)
);

    // Internal state
    reg [7:0] count;

    // Control signals from uio_in
    wire load     = uio_in[0];
    wire count_en = uio_in[1];
    wire drive_en = uio_in[3];

    // Asynchronous reset, synchronous load, synchronous increment
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'h00;
        end else if (ena) begin
            if (load) begin
                count <= ui_in;            // sync load from ui_in on next clk edge
            end else if (count_en) begin
                count <= count + 8'd1;     // increment when enabled
            end
        end
    end

    // Always-on mirror of the counter to dedicated outputs (helps in bring-up & tests)
    assign uo_out  = count;

    // Tri-stateable copy on the uio bus
    assign uio_out = count;
    assign uio_oe  = {8{drive_en}};  // all 8 bits drive only when DRIVE_EN=1

endmodule