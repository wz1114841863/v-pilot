# vpilot/skeletons/Makefile
# v-pilot 自动生成的 Cocotb + Verilator 仿真入口
# v-pilot 将自动维护此文件中的 LLM_GENERATED 区域
# --------------------------------------------------

# --- 仿真器设置 ---
# 默认使用 verilator, 允许用户通过命令行覆盖 (e.g., make SIM=vcs)
SIM ?= verilator

# --- 语言设置 ---
TOPLEVEL_LANG ?= verilog

# --- Verilator 特定编译参数 ---
ifeq ($(SIM), verilator)
	COMPILE_ARGS += --timing
	EXTRA_ARGS += --trace --trace-structs
endif

# --- HDL 时间单位 ---
COCOTB_HDL_TIMEUNIT ?= 1ns
COCOTB_HDL_TIMEPRECISION ?= 1ps

# --- 日志格式 ---
export COCOTB_REDUCED_LOG_FMT = 1

# --- RTL 源码 (v-pilot 自动修改) ---
# 假设 Makefile 在 uvm_tb/ 目录下运行, 源码在 ../rtl/
# LLM_GENERATED_START: VERILOG_SOURCES
VERILOG_SOURCES := $(shell find ../rtl -name "*.v" -o -name "*.sv")
# LLM_GENERATED_END: VERILOG_SOURCES

# 默认的冒烟测试名称
# LLM_GENERATED_START: DEFAULT_TESTCASE
TESTCASE ?= SanityCheckTest
# LLM_GENERATED_END: DEFAULT_TESTCASE

# --- Verilog 顶层模块 (v-pilot 自动填充) ---
# COCOTB_TOPLEVEL 是 Verilog/VHDL 顶层实体的名称
# LLM_GENERATED_START: COCOTB_TOPLEVEL
COCOTB_TOPLEVEL := my_design  # 替换my_design为实际顶层模块名称
# LLM_GENERATED_END: COCOTB_TOPLEVEL

# --- Cocotb 测试模块 ---
# COCOTB_TEST_MODULES 是 Python 入口文件的 basename (e.g., test_lib.py)
# 我们的框架固定使用 test_lib
COCOTB_TEST_MODULES := test_lib

# --- 包含 Cocotb 的 Make 规则 ---
include $(shell cocotb-config --makefiles)/Makefile.sim
