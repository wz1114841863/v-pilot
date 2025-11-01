from pyuvm import uvm_test
from env import TestEnv


class MyBaseTest(uvm_test):
    """
    所有测试用例的基类

    职责:
    1. 实例化顶层环境 (TestEnv).
    2. 管理 UVM_TEST_DONE objection,确保测试能正确开始和结束.
    3. (可选) 打印测试平台拓扑.
    4. 提供一个 'main_phase' 供子类重写.
    """

    def build_phase(self):
        super().build_phase()
        # 实例化我们的顶层环境
        self.env = TestEnv.create("env", self)

    def end_of_elaboration_phase(self):
        # (可选) 打印测试平台结构,非常有助于调试
        self.print_topology()

    async def run_phase(self):
        """
        UVM测试的主执行阶段
        """
        # 1. 升起 UVM_TEST_DONE objection, 阻止仿真过早结束
        self.raise_objection()
        await self.main_phase()
        self.drop_objection()

    async def main_phase(self):
        """
        这是一个空的 "placeholder" 方法.
        LLM 生成的 *具体测试用例* (在 test_lib.py 中)
        将 *重写* (override) 这个方法,
        并在这里启动它们各自的测试序列.
        """
        self.logger.info("MyBaseTest main_phase (does nothing)")
        pass
