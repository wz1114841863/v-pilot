# vpilot/skeletons/sequence_lib.py

from pyuvm import *
from seq_item import MySeqItem
import random


class MyBaseSeq(UVMSequence):
    """
    所有测试序列的基类
    """

    async def body(self):
        # 默认的 'body',什么都不做
        # 子类将重写此方法
        self.logger.info("Running MyBaseSeq (does nothing)")
        await Timer(100, "ns")


# --------------------------------------------------
# LLM_GENERATED_START: SEQUENCES
# --------------------------------------------------
# LLM 将根据<验证计划>的 'sequence_library' 部分在此追加序列类
#
# 示例:
# class ResetTestSeq(MyBaseSeq):
#     async def body(self):
#         self.logger.info("Running ResetTestSeq...")
#         # (复位通常在 base_test 中完成, 这里可以做一些复位后的检查)
#         await Timer(50, "ns")
#
# class BasicDataTestSeq(MyBaseSeq):
#     async def body(self):
#         self.logger.info("Running BasicDataTestSeq...")
#         item = MySeqItem()
#         for _ in range(10):
#             item.randomize()
#             await self.start_item(item)
#             await self.finish_item(item)
#             await RisingEdge(ConfigDB().get(self, "", "VIF").clk)
#
# --------------------------------------------------
# LLM_GENERATED_END: SEQUENCES
# --------------------------------------------------
