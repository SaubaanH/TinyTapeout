/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (  
    input  wire [7:0] io_in,
    output wire [7:0] io_out,
    output wire [7:0] io_oeb
);
   
    wire clk     = io_in[0];
    wire arst_n  = io_in[1];
    wire load    = io_in[2];
    wire oe      = io_in[3];
    wire sdi     = io_in[4];
    wire sclk    = io_in[5];
    wire up      = io_in[6];
    wire en      = io_in[7];

    reg  [7:0] load_reg;
    reg  [7:0] count_q;

    always @(posedge sclk or negedge arst_n) begin
        if (!arst_n) load_reg <= 8'h00;
        else         load_reg <= {sdi, load_reg[7:1]}; 
    end

    always @(posedge clk or negedge arst_n) begin
        if (!arst_n)       count_q <= 8'h00;
        else if (load)     count_q <= load_reg;               
        else if (en)       count_q <= up ? count_q + 8'd1
                                         : count_q - 8'd1;    
    end

    assign io_out = count_q;
    assign io_oeb = {8{~oe}}; 
endmodule
