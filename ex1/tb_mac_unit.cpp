// tb_mac_unit.cpp
// Testbench Verilator for mac_unit.
// Calculates the dot product of two known vectors and verifies the result
// against the expected value calculated in C++.

#include "Vmac_unit.h"
#include "verilated.h"
#include <cstdio>
#include <cstdlib>
#include <vector>

static vluint64_t main_time = 0;
double sc_time_stamp() { return main_time; }

static void tick(Vmac_unit* dut) {
    dut->clk = 0; dut->eval();
    main_time++;
    dut->clk = 1; dut->eval();
    main_time++;
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vmac_unit* dut = new Vmac_unit();

    // Vectors to calculate the dot product 
    std::vector<int8_t> va = {1, 2, 3, 4};
    std::vector<int8_t> vb = {5, 6, 7, 8};

    int64_t expected = 0;
    for (size_t i = 0; i < va.size(); i++)
        expected += (int64_t)va[i] * (int64_t)vb[i];

    // Reset
    dut->rst_n   = 0;
    dut->valid_in = 0;
    dut->a = 0; dut->b = 0; dut->last = 0;
    tick(dut);
    tick(dut);
    dut->rst_n = 1;
    tick(dut);

    // Stream the elements, one per cycle
    bool got_done = false;
    int32_t result = 0;

    for (size_t i = 0; i < va.size(); i++) {
        dut->valid_in = 1;
        dut->a = va[i];
        dut->b = vb[i];
        dut->last = (i == va.size() - 1) ? 1 : 0;
        tick(dut);
    }
    dut->valid_in = 0;
    dut->last = 0;

    // 'done' arrives a cycle later than the last 'last' valid: we check a few extra cycles
    for (int i = 0; i < 4 && !got_done; i++) {
        if (dut->done) {
            got_done = true;
            result = dut->acc_out;
        }
        tick(dut);
    }

    dut->final();

    printf("Expected value  : %ld\n", (long)expected);
    printf("Got: %d\n", result);

    if (!got_done) {
        printf("FAILED: signal 'done' not raised\n");
        return 1;
    }
    if (result != expected) {
        printf("FAILED: incorrect result\n");
        return 1;
    }

    printf("PASSED: the MAC unit calculates the dot product correctly\n");
    delete dut;
    return 0;
}