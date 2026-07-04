# Verilog glossary — Exercise 1 (mac_unit.v)

This Verilog module is a hardware dot-product calculator. Every clock cycle it takes in one pair of numbers, multiplies them together, and adds the result to a running total stored in a register. Once it has seen every pair in the sequence, it outputs the final sum: a[0]*b[0] + a[1]*b[1] + ... + a[N-1]*b[N-1]. This single operation (multiply-then-accumulate) is the basic building block behind almost all deep learning math. In PyTorch, it directly corresponds to torch.dot(a, b), and it's also the repeated inner step used inside bigger operations like nn.Linear layers, torch.matmul, and convolutions.

## File structure

### `module ... endmodule`
```verilog
module mac_unit #( ... ) ( ... );
    ...
endmodule
```
A `module` is roughly the hardware equivalent of a "function" or "class" in software, except it describes a piece of hardware instead of a piece of sequential logic. Everything between `module` and `endmodule` describes ONE circuit. It's not code that "runs top to bottom": it's a description of wires and components that all exist simultaneously, all the time.

### `parameter`
```verilog
module mac_unit #(
    parameter DATA_W = 8,
    parameter ACC_W = 32
)
```
These are "compile-time configurable constants", similar to C++ templates or generics in other languages. Whoever instantiates the module can decide to use `DATA_W=16` instead of 8, without touching the internal code. **Watch out**: the last parameter in the list does NOT get a trailing comma.

---

## Module inputs/outputs

### `input` / `output`
```verilog
input wire clk,
output reg done,
```
These define the direction of a signal relative to the module: `input` comes in, `output` goes out. They're like a function's parameters and its return value, except here they are physical wires, not software variables.

### `wire` vs `reg`
This is the most confusing distinction for anyone coming from software:
- **`wire`**: a wire. Its value is always "whatever is on the other end right now". You can't "assign" it inside an `always` block, only via
  `assign` or as the direct output of an expression.
- **`reg`**: something that can "remember" a value between one clock cycle and the next (it typically becomes a real flip-flop/register in hardware). It's assigned inside an `always` block.

Note: `reg` **does not necessarily mean** "this will become a physical register". If you assign it with pure combinational logic it can synthesize into just a wire. But for now, in the MAC unit, the `reg`s inside `always @(posedge clk...)` really do become flip-flops.

### `signed`
```verilog
input wire signed [DATA_W - 1 : 0] a,
```
By default Verilog signals are treated as unsigned numbers. `signed` tells the simulator/synthesizer "interpret this bit bus as a two's complement number". It is essential for the MAC unit because the weights/activations can be negative.

### `[DATA_W - 1 : 0]` — bit bus
```verilog
[DATA_W - 1 : 0] a
```
Defines how many bits a signal has: from bit `DATA_W-1` (most significant) down to bit `0` (least significant). With `DATA_W=8` this is `[7:0]`, i.e. 8 bits. An 8-bit integer, exactly like `int8_t` in C.

---

## Module body

### Declaration + continuous assignment on a `wire`
```verilog
wire signed [2 * DATA_W - 1 : 0] raw_prod = a * b;
```
This is NOT "run the multiplication once". It's a description of a wire that is **always and continuously** equal to the product of `a` and `b`: if `a` or `b` change, `raw_prod` changes instantly (in simulation) or after the propagation delay of the physical multiplier (in real hardware). Note the width is `2*DATA_W`: multiplying two N-bit numbers can require up to 2N bits to hold the result.

### Concatenation `{ }`
```verilog
{ACC_W{1'b0}}
```
Curly braces concatenate bits. `{ACC_W{1'b0}}` means "repeat the bit `1'b0` for `ACC_W` times", a compact way to write "all zeros over ACC_W bits" (equivalent to `32'b0` if ACC_W=32).

### Replication for sign extension
```verilog
{{(ACC_W - 2 * DATA_W){raw_prod[2 * DATA_W - 1]}}, raw_prod}
```
A more advanced construct, let's break it down:
- `raw_prod[2*DATA_W-1]` takes **a single bit**: the most significant bit of `raw_prod`, i.e. the sign bit.
- `{(ACC_W - 2*DATA_W){that_bit}}` repeats that sign bit enough times to fill the gap between `ACC_W` and `2*DATA_W`.
- The comma concatenates this "filler" together with `raw_prod` itself.

In practice: this is manual sign extension, the same thing that happens automatically in C when you assign an `int16_t` to an `int32_t`. In Verilog, if you don't do it explicitly, the simulator warns you about it.

### `1'b0`, `2'b01`, etc. — sized literals
Format: `<number of bits>'<base><value>`.
- `1'b0` = 1 bit, binary base (`b`), value 0
- `8'd70` would be = 8 bits, decimal base (`d`), value 70
Specifying the size avoids ambiguity about how many bits a literal number should occupy.

### `always @(posedge clk or negedge rst_n)`
```verilog
always @(posedge clk or negedge rst_n) begin
    ...
end
```
This is a **sequential block**: its content is only re-evaluated when one of these events happens:
- `posedge clk`: the clock transitions from 0 to 1 (rising edge)
- `negedge rst_n`: the reset transitions from 1 to 0 (it "activates", since it's active-low)

This is the construct that describes a flip-flop/register: "update your state when the clock ticks (or when a reset arrives)".

### `if (!rst_n) ... else ...` inside an `always`
```verilog
if (!rst_n) begin
    acc <= {ACC_W{1'b0}};
    ...
end else begin
    ...
end
```
`rst_n` is "active-low reset": when it's 0, reset is "pressed". `!rst_n` is therefore true when reset is active. Inside that block, all registers get cleared, and this is the circuit's clean starting condition.

### Non-blocking assignment `<=`
```verilog
acc <= acc + prod;
```
Inside an `always @(posedge clk...)` block you **always** use `<=` (non-blocking), not `=` (blocking). The conceptual difference: with `<=`, all assignments in the block "prepare" their new values and apply them all together at the end of the clock cycle, as if simultaneous. This mirrors how real hardware works, where all flip-flops switch at the same instant. If you used `=` instead, you'd risk different behavior between simulation and real hardware (one of the most common traps for Verilog beginners).

### `done <= 1'b0;` as a default, then possibly overwritten
```verilog
done <= 1'b0;
if (valid_in) begin
    if (last) begin
        ...
        done <= 1'b1;
    end
    ...
end
```
Common pattern: you assign a "default" value at the start of the block, then overwrite it in the branches that need something different. Because `<=` only applies the **last** assignment written for that signal in that cycle, this guarantees `done` is high for exactly one clock cycle exactly when needed, and low everywhere else, without having to write it explicitly in every branch of the `if`.

