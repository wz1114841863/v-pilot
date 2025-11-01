from pyuvm import *
from base_test import MyBaseTest

import sequence_lib as seq_lib

# --------------------------------------------------
# LLM_GENERATED_START: TESTS
# --------------------------------------------------
# LLM 将根据<验证计划>的 'sequence_library' 部分注册测试
# 每一个测试用例都是一个类


# 示例:
@test()
class BasicDataTest(MyBaseTest):
    """
    [LLM生成的]
    运行 BasicDataTestSeq 序列
    """

    async def main_phase(self):
        self.logger.info("Starting BasicDataTest...")

        # 1. 创建序列
        seq = seq_lib.BasicDataTestSeq.create("seq")

        # 2. 找到 Sequencer (假设在 env.agent.sequencer)
        sequencer = self.env.agent.sequencer
        if sequencer is None:
            self.logger.critical("Sequencer not found! Did you instantiate it?")
            UVM_FATAL(self.get_name(), "Sequencer not found")

        # 3. 启动序列
        await seq.start(sequencer)

        self.logger.info("BasicDataTest finished.")


@test()
class ResetTest(MyBaseTest):
    """
    [LLM生成的]
    运行 ResetTestSeq 序列
    """

    async def main_phase(self):
        self.logger.info("Starting ResetTest...")
        seq = seq_lib.ResetTestSeq.create("seq")
        await seq.start(self.env.agent.sequencer)
        self.logger.info("ResetTest finished.")


# --------------------------------------------------
# LLM_GENERATED_END: TESTS
# --------------------------------------------------
