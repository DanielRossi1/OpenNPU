TOPMODULE = mac_unit
OBJ_DIR   = obj_dir

.PHONY: all sim clean

all: sim

sim:
	verilator -Wall --cc $(TOPMODULE).v --exe tb_mac_unit.cpp --top-module $(TOPMODULE) -CFLAGS "-std=c++14"
	make -C $(OBJ_DIR) -f V$(TOPMODULE).mk
	./$(OBJ_DIR)/V$(TOPMODULE)

clean:
	rm -rf $(OBJ_DIR)