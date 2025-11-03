import pyuvm
import sequence_lib as seq_lib
from pyuvm import UVMError
from base_test import MyBaseTest


# --------------------------------------------------
# LLM_GENERATED_START: TESTS
# --------------------------------------------------
# [!!] LLM 的任务:
# 在此 *追加* 多个 @pyuvm.test() 装饰的类.
#
# [!!] 关键: LLM *必须* 生成一个名为 "SanityCheckTest"的测试.
# 这个测试运行一个 "空" 序列, 用于验证平台能否正确构建和启动.


@pyuvm.test()
class SanityCheckTest(MyBaseTest):
    """
    [LLM 生成]
    默认的 "冒烟测试".
    运行一个 "空" 序列, 验证平台是否能正确构建和启动.
    """

    async def main_phase(self):
        self.logger.info("Running SanityCheckTest (empty seq)...")

        try:
            sequencer = self.env.agent.sequencer
        except AttributeError:
            raise UVMError(
                f"'{self.get_name()}' [SanityCheckTest]: "
                "Sequencer not found at 'self.env.agent.sequencer'!"
            )

        # 启动一个 "真正" 的空序列 (uvm_sequence 基类)
        empty_seq = seq_lib.uvm_sequence.create("empty_seq")
        await empty_seq.start(sequencer)

        self.logger.info("SanityCheckTest finished.")


@pyuvm.test()
class BasicDataTest(MyBaseTest):
    """
    [LLM 生成]
    运行 BasicDataTestSeq 序列
    """

    async def main_phase(self):
        self.logger.info("Starting BasicDataTest...")

        try:
            sequencer = self.env.agent.sequencer
        except AttributeError:
            raise UVMError(
                f"'{self.get_name()}' [BasicDataTest]: "
                "Sequencer not found at 'self.env.agent.sequencer'!"
            )

        # 创建 *具体* 序列
        seq = seq_lib.BasicDataTestSeq.create("seq")

        # 启动序列
        await seq.start(sequencer)

        self.logger.info("BasicDataTest finished.")


#
# [LLM 将在这里追加更多 @pyuvm.test() 类...]
#
# --------------------------------------------------
# LLM_GENERATED_END: TESTS
# --------------------------------------------------
