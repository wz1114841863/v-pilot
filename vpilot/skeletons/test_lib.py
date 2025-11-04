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
# (LLM 填充示例:)

# @pyuvm.test() #
# class SanityCheckTest(MyBaseTest):
#     """
#     默认 "冒烟测试".
#     """
#     async def main_phase(self): #
#         self.logger.info("Running SanityCheckTest (empty seq)...")
#         try:
#             # (LLM 必须知道 'env' 中 'sequencer' 的路径)
#             sequencer = self.env.input_agent.sequencer
#         except AttributeError:
#             raise UVMError(f"Sequencer path is incorrect!")
#
#         # (启动一个 *真正* 的空序列)
#         empty_seq = seq_lib.uvm_sequence.create("empty_seq")
#         await empty_seq.start(sequencer)
#         self.logger.info("SanityCheckTest finished.")
#
#
# @pyuvm.test()
# class BasicDataTest(MyBaseTest):
#     """
#     运行 BasicDataTestSeq 序列
#     """
#     async def main_phase(self): # 👈 [!!] 关键: 重写
#         self.logger.info("Starting BasicDataTest...")
#         try:
#             sequencer = self.env.input_agent.sequencer
#         except AttributeError:
#             raise UVMError(f"Sequencer path is incorrect!")
#
#         seq = seq_lib.BasicDataTestSeq.create("seq")
#         await seq.start(sequencer)
#         self.logger.info("BasicDataTest finished.")

#
# [LLM 将在这里追加更多 @pyuvm.test() 类...]
#
# --------------------------------------------------
# LLM_GENERATED_END: TESTS
# --------------------------------------------------
