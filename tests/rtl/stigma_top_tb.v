`timescale 1ns / 1ps
module stigma_top_tb;
    reg clk = 0;
    reg rst_n = 1;
    reg [7:0] www_valid = 0;
    reg [71:0] stim [0:4095];
    reg [63:0] www_data [0:7];
    wire [7:0] ndb_valid;
    wire [63:0] ndb_data [0:7];
    wire [63:0] mem_state_vector, momentum_vector, v_dpa_metric, snzg_noise_level;
    wire snzg_gate_pass, resonant;
    wire [7:0] load_band;
    integer n, i, ch;
    reg [1023:0] path;

    stigma_center_core dut (
        .clk(clk),
        .rst_n(rst_n),
        .www_valid(www_valid),
        .www_data(www_data),
        .ndb_valid(ndb_valid),
        .ndb_data(ndb_data),
        .mem_state_vector(mem_state_vector),
        .momentum_vector(momentum_vector),
        .v_dpa_metric(v_dpa_metric),
        .snzg_gate_pass(snzg_gate_pass),
        .snzg_noise_level(snzg_noise_level),
        .resonant(resonant),
        .load_band(load_band)
    );

    always #5 clk = ~clk;

    task print_outputs;
        begin
            $write("OUT %h %h %h %h %h %h %h %h",
                mem_state_vector, momentum_vector, v_dpa_metric,
                snzg_gate_pass, snzg_noise_level, resonant, load_band, ndb_valid);
            for (ch = 0; ch < 8; ch = ch + 1)
                $write(" %h", ndb_data[ch]);
            $write("\n");
        end
    endtask

    task drive_stim;
        input integer index;
        begin
            www_valid = stim[index][71:64];
            for (ch = 0; ch < 8; ch = ch + 1)
                www_data[ch] = stim[index][63:0];
        end
    endtask

    initial begin
        if (!$value$plusargs("stim=%s", path)) begin
            $display("ERROR no +stim"); $finish;
        end
        if (!$value$plusargs("n=%d", n)) begin
            $display("ERROR no +n"); $finish;
        end
        $readmemh(path, stim);
        for (ch = 0; ch < 8; ch = ch + 1)
            www_data[ch] = 0;
        #1 rst_n = 0;
        #1;
        $display("RESET");
        print_outputs();
        rst_n = 1;
        drive_stim(0);
        for (i = 0; i < n; i = i + 1) begin
            @(posedge clk);
            #1 print_outputs();
            if (i + 1 < n) begin
                @(negedge clk);
                drive_stim(i + 1);
            end
        end
        $finish;
    end
endmodule
