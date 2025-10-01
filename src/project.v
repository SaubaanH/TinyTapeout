module tt_um_example (
    input  wire clk,
    input  wire rst_n,
    input  wire ena,
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe
);

    wire load = ui_in[0];
    wire oe   = ui_in[1];
    wire sdi  = ui_in[2];
    wire sclk = ui_in[3];
    wire up   = ui_in[4];
    wire en   = ui_in[5];

    reg [7:0] load_reg;
    reg [7:0] count_q;

    // Shift register: MSB-first, always active
    always @(posedge sclk or negedge rst_n) begin
        if (!rst_n)
            load_reg <= 8'h00;
        else
            load_reg <= {sdi, load_reg[7:1]};
    end

    // Counter: async reset, sync load, gated by ena
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count_q <= 8'h00;
        else if (ena) begin
            if (load)
                count_q <= load_reg;
            else if (en)
                count_q <= up ? count_q + 8'd1 : count_q - 8'd1;
        end
    end

    assign uo_out  = oe ? count_q : 8'hZZ;
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;

endmodule