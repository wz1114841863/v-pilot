# vpilot/skeletons/base_test.py
#
# UVM 测试基类
# 职责: 1. 实例化 Env 和 BFM. 2. 启动时钟. 3. 管理 Objection.
import cocotb
from cocotb.clock import Clock
from pyuvm import uvm_test, uvm_root
from env import TestEnv
from base_bfm import BaseBfm


class MyBaseTest(uvm_test):
    """所有测试用例的基类"""

    def build_phase(self):
        """实例化环境和BFM"""
        super().build_phase()
        # 实例化我们的顶层环境
        self.env = TestEnv.create("env", self)
        # 获取 BFM 单例 (它在 base_bfm.py 中被创建)
        self.bfm = BaseBfm()

    def end_of_elaboration_phase(self):
        """打印测试平台拓扑, 有助于调试"""
        super().end_of_elaboration_phase()
        print(uvm_root())

    async def run_phase(self):
        """启动时钟, 管理 objection, 调用 main_phase"""
        # 1. 升起 UVM_TEST_DONE objection, 阻止仿真过早结束
        self.raise_objection()

        # 2. [!!] 启动 Cocotb 时钟
        #    我们从 BFM 获取时钟句柄 (该句柄由 LLM 在 base_bfm.py 中设置)
        if self.bfm.clk is None:
            self.fail("BFM did not correctly initialize 'self.clk' handle.")

        # 在这里从 ConfigDB 或 LLM 获取时钟周期, 暂时硬编码为 10ns
        cocotb.start_soon(Clock(self.bfm.clk, 10, unit="ns").start())

        # 3. 执行 BFM 中的复位任务
        #    确保每个测试开始时 DUT 都被复位
        await self.bfm.reset()

        # 4. 调用 'main_phase'
        #    这个方法是空的, 将由 'test_lib.py' 中的子类来重写
        await self.main_phase()

        # 5. 降下 objection, 允许仿真结束
        self.drop_objection()

    async def main_phase(self):
        """
        [!!] 这是一个空的 "placeholder" (占位符) 方法.

        LLM 生成的 *具体测试用例* (在 test_lib.py 中)
        将 *重写* (override) 这个方法,
        并在这里启动它们各自的测试序列.
        """
        self.logger.info("MyBaseTest main_phase (does nothing by default)")
        pass  # 子类将重写此方法
