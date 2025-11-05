# vpilot/skeletons/base_bfm.py
#
# Base Bus Functional Model (BFM)
# 职责: 封装所有 cocotb 信号时序, 提供对dut的高层次抽象访问.
# 架构: Singleton (单例) 模式.
import cocotb

from cocotb.triggers import RisingEdge, FallingEdge, Timer, ReadOnly
from pyuvm import utility_classes
from seq_item import MySeqItem


class BaseBfm(metaclass=utility_classes.Singleton):
    """基础 BFM 骨架"""

    def __init__(self):
        # 抓取 cocotb 的顶层 DUT 句柄
        self.dut = cocotb.top
        self.log = self.dut._log

        # --------------------------------------------------
        # LLM_GENERATED_START: BFM_HANDLES
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 根据<设计规范>的 'ports' 部分,
        # 提供 *正确* 的时钟, 复位信号句柄 和 其余数据端口句柄.
        # [!!] LLM 填充示例:
        self.clk = self.dut.clk
        self.rst_n = self.dut.rst_n
        self.data_in = self.dut.data_in
        # --------------------------------------------------
        # LLM_GENERATED_END: BFM_HANDLES
        # --------------------------------------------------

        self.log.info(
            f"BaseBfm Singleton created. "
            f"Clock: {self.clk._name}, "
            f"Reset: {self.rst_n._name}"
        )

    async def wait_clock(self, cycles=1):
        """框架提供的/可复用的时钟等待任务."""
        for _ in range(cycles):
            await RisingEdge(self.clk)

    # --------------------------------------------------
    # LLM_GENERATED_START: BFM_RESET_TASK
    # --------------------------------------------------
    # [!!] LLM 的任务:
    # 实现一个 *具体* 的复位任务, 使用 self.clk 和 self.rst_n
    #
    # [!!] LLM 填充示例:
    # async def reset(self):
    #     self.log.info("BFM: Starting DUT Reset...")
    #     await RisingEdge(self.clk)
    #     self.rst_n.value = 0
    #     await self.wait_clock(5)
    #     self.rst_n.value = 1
    #     await self.wait_clock(2)
    #     self.log.info("BFM: DUT Reset Complete.")
    #
    # --------------------------------------------------
    # LLM_GENERATED_END: BFM_RESET_TASK
    # --------------------------------------------------

    # --------------------------------------------------
    # LLM_GENERATED_START: BFM_DRIVER_TASKS
    # --------------------------------------------------
    # [!!] LLM 的任务:
    # 为 'Driver' 实现高层抽象的 *写入/驱动* 任务
    #
    # [!!] LLM 填充示例:
    # async def drive_input_transaction(self, item: MySeqItem):
    #     """
    #     根据 seq_item 驱动输入端口
    #     """
    #     await self.wait_clock()
    #     self.dut.valid_in.value = 1
    #     self.dut.data_in.value = item.data_in
    #     self.dut.enable.value = item.enable
    #
    #     await self.wait_clock()
    #     self.dut.valid_in.value = 0
    #
    # --------------------------------------------------
    # LLM_GENERATED_END: BFM_DRIVER_TASKS
    # --------------------------------------------------

    # --------------------------------------------------
    # LLM_GENERATED_START: BFM_MONITOR_TASKS_AND_GETTERS
    # --------------------------------------------------
    # [!!] LLM 的任务:
    # 为 'Monitor' 实现高层抽象的 *监视* 任务或 *getter* 方法
    # [!!] 关键: Monitor 需要采样 *输入* 和 *输出* 才能构建完整 Transaction
    #
    # [!!] LLM 填充示例:
    # async def wait_for_input_valid(self):
    #     """等待一个有效的输入"""
    #     await RisingEdge(self.clk)
    #     while (self.dut.valid_in.value == 0):
    #         await RisingEdge(self.clk)
    #     self.log.debug("BFM: Detected input valid")
    #
    # def get_input_data(self):
    #     """采样输入数据 (应在 valid 时调用)"""
    #     return int(self.dut.data_in.value)
    #
    # async def wait_for_output_valid(self):
    #     """等待一个有效的输出"""
    #     await RisingEdge(self.clk)
    #     while (self.dut.valid_out.value == 0):
    #         await RisingEdge(self.clk)
    #     self.log.debug("BFM: Detected output valid")
    #
    # def get_output_data(self):
    #     """采样输出数据 (应在 valid 时调用)"""
    #     return int(self.dut.data_out.value)
    #
    # --------------------------------------------------
    # LLM_GENERATED_END: BFM_MONITOR_TASKS_AND_GETTERS
    # --------------------------------------------------
