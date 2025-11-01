from pyuvm import *
import cocotb
from cocotb.triggers import RisingEdge, Timer


class Driver(UVMDriver):
    """
    Driver: 将 SeqItem 转换为物理信号时序
    """

    def build_phase(self):
        super().build_phase()
        self.vif = ConfigDB().get(self, "", "VIF")
        if self.vif is None:
            self.fail("Virtual Interface not found in ConfigDB")

    async def run_phase(self):
        self.logger.info("Driver run_phase started")
        await RisingEdge(self.vif.clk)

        while True:
            # 1. 从 Sequencer 获取下一个数据包
            seq_item = await self.seq_item_port.get_next_item()
            self.logger.debug(f"Driving item: {seq_item}")

            # --------------------------------------------------
            # LLM_GENERATED_START: DRIVER_LOGIC
            # --------------------------------------------------
            # LLM 将根据<验证计划>生成具体的信号驱动时序
            # 示例 (一个简单的 valid/ready 握手):
            # self.vif.valid_in.value = 1
            # self.vif.data_in.value = seq_item.data
            #
            # await RisingEdge(self.vif.clk)
            # while (self.vif.ready_in.value == 0):
            #     await RisingEdge(self.vif.clk)
            #
            # self.vif.valid_in.value = 0
            # --------------------------------------------------
            # LLM_GENERATED_END: DRIVER_LOGIC
            # --------------------------------------------------

            # 3. 通知 Sequencer,此数据包已处理完毕
            self.seq_item_port.item_done()
