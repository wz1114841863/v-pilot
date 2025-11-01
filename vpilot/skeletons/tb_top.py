import cocotb
import os
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from pyuvm import ConfigDB, uvm_root

import test_lib


# --------------------------------------------------
# LLM_GENERATED_START: VIRTUAL_INTERFACE
# --------------------------------------------------
# LLM 将根据<设计规范>的 'ports' 部分生成这个VIF
class VIF:
    """
    Virtual Interface: 捆绑所有DUT的物理信号
    """

    def __init__(self, dut):
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        # 示例:
        # self.data_in = dut.data_in
        # self.data_out = dut.data_out
        # self.valid_in = dut.valid_in
        # self.valid_out = dut.valid_out


# --------------------------------------------------
# LLM_GENERATED_END: VIRTUAL_INTERFACE
# --------------------------------------------------


@cocotb.test()
async def run_uvm_test(dut):
    """
    Cocotb 测试入口点 (v-pilot 框架核心)
    """
    # 启动时钟
    vif = VIF(dut)
    cocotb.start_soon(Clock(vif.clk, 10, units="ns").start())

    # 将 VIF 放入 pyuvm 的 ConfigDB
    ConfigDB().set(None, "*", "VIF", vif)

    # 确定要运行的测试用例
    #    从 "TESTCASE" 环境变量中获取
    # --------------------------------------------------
    # LLM_GENERATED_START: DEFAULT_TESTCASE
    # --------------------------------------------------
    # 基础的冒烟测试, 验证可以正常运行.
    default_test = "BasicDataTest"
    # --------------------------------------------------
    # LLM_GENERATED_END: DEFAULT_TESTCASE
    # --------------------------------------------------
    test_name = os.getenv("TESTCASE", default_test)

    if not test_name:
        raise RuntimeError(
            "必须通过 TESTCASE 环境变量指定要运行的测试, 或在骨架中设置默认值"
        )

    # 启动UVM测试
    await uvm_root().run_test(test_name)
