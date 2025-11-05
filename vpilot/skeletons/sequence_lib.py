# vpilot/skeletons/sequence_lib.py
#
# UVM 序列库 (Sequence Library)
# 职责: 1. 定义 'MyBaseSeq'. 2. LLM *追加* 具体序列.
import random
import cocotb

from cocotb.triggers import RisingEdge, Timer
from pyuvm import uvm_sequence, UVMNotImplemented
from seq_item import MySeqItem


# --------------------------------------------------
# [!!] 框架固定代码 (Static)
# --------------------------------------------------
class MyBaseSeq(uvm_sequence):
    """
    所有测试序列的基类
    """

    def __init__(self, name="MyBaseSeq"):
        super().__init__(name)
        self.item = MySeqItem()  # 预先创建一个 'item' 句柄, 方便子类使用

    async def body(self):
        """
        [!!] 规范2: 这是一个 "抽象" 方法.
        如果 LLM (或工程师) 忘记在子类中重写此方法,
        测试将立即失败并显示此错误.
        (此设计 100% 基于您提供的 'AluReg_base_sequence' 示例)
        """
        raise UVMNotImplemented(
            "v-pilot: "
            "The sequence running on the sequencer "
            f"({self.get_name()}) must override the 'body' method."
        )


# --------------------------------------------------
# LLM_GENERATED_START: SEQUENCES
# --------------------------------------------------
# [!!] LLM 的任务:
# LLM 将根据<验证计划>的 'sequence_library' 部分
# 在此 *追加* 多个具体的序列类
#
# 示例 (一个基本的随机测试):
#
# class BasicDataTestSeq(MyBaseSeq):
#     async def body(self):
#         self.logger.info("Running BasicDataTestSeq...")
#
#         for _ in range(10):
#             # 1. 随机化 item
#             #    (我们假设 'randomize()' 在 seq_item.py 中已由 LLM 实现)
#             self.item.randomize()
#
#             # 2. [!!] 启动 item (将其发送给 Driver)
#             # 'await self.start_item(item)' 会:
#             #   a. 将 item 发送给 Sequencer -> Driver
#             #   b. *等待* Driver 调用 item_done()
#             await self.start_item(self.item)
#
#             # 3. [!!] 接收 item (它可能已被 Driver 的 BFM 调用修改)
#             #    (这对于 "读" 操作至关重要)
#             await self.finish_item(self.item)
#
#             self.logger.debug(f"Seq received item back: {self.item}")
#
#
# 示例 (一个 fork/join 序列, 像 'TestAllForkSeq'):
#
# class ParallelTestSeq(MyBaseSeq):
#     async def body(self):
#         self.logger.info("Running ParallelTestSeq...")
#
#         # 创建子序列
#         seq_a = BasicDataTestSeq("seq_a")
#         seq_b = BasicDataTestSeq("seq_b")
#
#         # 并行启动它们
#         task_a = cocotb.start_soon(seq_a.start(self.sequencer))
#         task_b = cocotb.start_soon(seq_b.start(self.sequencer))
#
#         # 等待两者都完成
#         await cocotb.triggers.Combine(task_a, task_b)
#
# --------------------------------------------------
# LLM_GENERATED_END: SEQUENCES
# --------------------------------------------------
