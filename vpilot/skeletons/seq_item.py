import random
from pyuvm import uvm_sequence_item


class MySeqItem(uvm_sequence_item):
    """
    [!!] LLM 的任务:
    填充下面的所有 'LLM_GENERATED' 区域
    """

    def __init__(self, name="MySeqItem"):
        super().__init__(name)
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_FIELDS
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 根据<设计规范>的 'ports' 部分,
        # 定义所有相关的 *数据* 字段 (不是信号)
        #
        # 示例 (累加器):
        # self.data_in = 0
        # self.enable = 0
        # self.data_out = 0 # (Monitor 用)
        #
        # 示例 (RAM):
        # self.addr = 0
        # self.data_in = 0
        # self.data_out = 0 # (Monitor 用)
        # self.rw = 0 # 0 for read, 1 for write
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_FIELDS
        # --------------------------------------------------

    def randomize(self):
        """
        (可选) LLM 可以实现一个基础的 randomize 方法
        """
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_RANDOMIZE
        # ----------------------------------
        # [!!] LLM 的任务:
        # 为 'Driver' 序列提供随机化
        #
        # 示例:
        # self.addr = random.randint(0, 255)
        # self.data_in = random.randint(0, 0xFFFFFFFF)
        # self.rw = random.randint(0, 1)
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_RANDOMIZE
        # --------------------------------------------------
        pass

    def __str__(self):
        """
        [!!] 关键方法: 实现 __str__ 以便在日志中清晰地打印 item
        """
        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_STR
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 返回一个包含所有重要字段的格式化字符串
        #
        # 示例:
        # return (f"{self.get_name()} "
        #         f"Addr: 0x{self.addr:X} Data: 0x{self.data_in:X} RW: {self.rw}")
        #
        return f"{self.get_name()} (LLM: 请实现 __str__ 以便调试)"
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_STR
        # --------------------------------------------------

    def __eq__(self, other):
        """
        [!!] 关键方法: 实现 __eq__ 以便 Scoreboard 进行比对 (item_a == item_b)
        """
        if not isinstance(other, MySeqItem):
            return False

        # --------------------------------------------------
        # LLM_GENERATED_START: SEQ_ITEM_EQ
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 比较 *所有* 应该被 Scoreboard 检查的字段
        #
        # 示例 (比较 data_out):
        # return (self.data_out == other.data_out)
        #
        # 示例 (比较 data_out 和 addr):
        # return (self.data_out == other.data_out and self.addr == other.addr)
        #
        # [!!] 这是一个"安全"的默认值,它会强制LLM实现此方法
        return False
        # --------------------------------------------------
        # LLM_GENERATED_END: SEQ_ITEM_EQ
        # --------------------------------------------------
