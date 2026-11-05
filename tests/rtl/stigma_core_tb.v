`timescale 1ns / 1ps
// Drives the OS-CLX memory_accumulator, momentum_engine and vdpa_metric_unit with a
// stimulus file and prints one line per clock: mem momentum v_dpa (hex).
module stigma_core_tb;
    reg clk = 0;
    reg rst_n = 0;
    reg [63:0] ndb = 0;
    reg [63:0] wave = 0;
    wire [63:0] mem, mom, vdpa;
    reg [127:0] stim [0:4095];
    integer n, i;
    reg [1023:0] path;

    memory_accumulator u_mem (.clk(clk), .rst_n(rst_n), .ndb_in(ndb), .mem_out(mem));
    momentum_engine u_mom (.clk(clk), .rst_n(rst_n), .mem_in(mem), .momentum_out(mom));
    vdpa_metric_unit u_vdpa (.clk(clk), .rst_n(rst_n), .ndb_in(ndb), .momentum_in(mom),
                             .wave_in(wave), .v_dpa_out(vdpa));

    always #5 clk = ~clk;

    initial begin
        if (!$value$plusargs("stim=%s", path)) begin
            $display("ERROR no +stim"); $finish;
        end
        if (!$value$plusargs("n=%d", n)) begin
            $display("ERROR no +n"); $finish;
        end
        $readmemh(path, stim);
        @(negedge clk);
        $display("RESET %h %h %h", mem, mom, vdpa);
        rst_n = 1;
        for (i = 0; i < n; i = i + 1) begin
            ndb = stim[i][127:64];
            wave = stim[i][63:0];
            @(posedge clk);
            #1 $display("%h %h %h", mem, mom, vdpa);
            @(negedge clk);
        end
        $finish;
    end
endmodule
