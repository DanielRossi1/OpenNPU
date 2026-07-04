# OpenNPU

A from-scratch, hands-on journey into how **Neural Processing Units (NPUs)** work. Step by step, this repo builds up the pieces needed to run AI models efficiently on real hardware: starting from a single multiply-accumulate unit, all the way up (eventually) to a small custom instruction set and a high-level kernel language for it.

Target hardware: an Altera **Cyclone II** FPGA (`EP2C5T144C8N`). Everything is first verified in simulation, then (later exercises) deployed and verified on the real board.

---

## Prerequisites

```bash
sudo apt install verilator graphviz nodejs npm
sudo npm install -g netlistsvg
```

- **verilator** — compiles Verilog into a C++ model you can simulate and test
- **graphviz** — renders circuit schematics
- **netlistsvg** *(optional but recommended)* — nicer schematic rendering, with proper mux/register symbols instead of plain boxes

Python tooling (schematic viewer, future test/utility scripts) is managed with [`uv`](https://docs.astral.sh/uv/):

```bash
uv python install 3.12
uv sync
```

---

## Project layout

```
OpenNPU/
├── ex1/                  # Exercise 1: MAC unit
├── view_circuit.py       # generic Verilog -> schematic viewer
├── pyproject.toml        # Python deps (uv-managed)
└── verilog_glossary_ex1.md  # plain-English glossary of constructs used so far
```

Each exercise gets its own folder with the RTL, a testbench, and a `makefile` to build and run it.

---

## Exercise 1 — Multiply-Accumulate unit

**Goal:** build a MAC unit, the fundamental building block behind dot products, and in turn behind almost every deep learning operation (`torch.dot`, `nn.Linear`, `matmul`, convolutions...).

Build and run the simulation:

```bash
cd ex1
make sim
```

That both compiles and runs the testbench in one step. It streams in two known vectors, computes their dot product, and checks the result. You should see something like:

```
Expected: 70
Got     : 70
PASS: the MAC unit calculates the dot product correctly
```

To re-run without recompiling:

```bash
./obj_dir/Vmac_unit
```

### Visualizing the circuit

From the repo root:

```bash
uv run python view_circuit.py ex1/mac_unit.v
```

This synthesizes the RTL with Yosys and opens a schematic, by default with `netlistsvg` (proper digital symbols), falling back automatically to a plain Graphviz rendering if `netlistsvg` isn't installed. See `python view_circuit.py --help` for gate-level (`--synth`) and classic-style (`--style classic`) options.

---

## Exercise 2

🚧 Coming soon.

---

## License

See [LICENSE](./LICENSE).