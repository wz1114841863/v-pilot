from pyuvm import *
import random


class MySeqItem(UVMSequenceItem):
    """
    定义了在 Sequencer, Driver, Monitor 之间传递的数据包
    """

    def __init__(self, name="MySeqItem"):
        super().__init__(name)
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_FIELDS
        # --------------------------------------------------
        # LLM 将根据<验证计划>填充数据字段
        # 示例:
        # self.addr = 0
        # self.data = 0
        # self.rw = 0 # 0 for read, 1 for write
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_FIELDS
        # --------------------------------------------------

    def randomize(self):
        """(可选) LLM 可以实现一个基础的 randomize 方法"""
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_RANDOMIZE
        # --------------------------------------------------
        # 示例:
        # self.addr = random.randint(0, 255)
        # self.data = random.randint(0, 0xFFFFFFFF)
        # self.rw = random.randint(0, 1)
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_RANDOMIZE
        # --------------------------------------------------
        pass

    def __str__(self):
        """(可选) LLM 可以实现 __str__ 以便调试"""
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_STR
        # --------------------------------------------------
        # 示例:
        # return f"SeqItem(Addr: {self.addr}, Data: {self.data}, R/W: {self.rw})"
        return super().__str__()
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_STR
        # --------------------------------------------------

    def __eq__(self, other):
        """(可选) LLM 可以实现 __eq__ 以便 Scoreboard 比对"""
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_EQ
        # --------------------------------------------------
        # 示例:
        # if not isinstance(other, MySeqItem):
        #     return False
        # return (self.addr == other.addr and
        #         self.data == other.data and
        #         self.rw == other.rw)
        return super().__eq__(other)
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_EQ
        # --------------------------------------------------
