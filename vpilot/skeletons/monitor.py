from pyuvm import *
import cocotb
from cocotb.triggers import RisingEdge, Timer
from seq_item import MySeqItem  # 导入我们要创建的数据包


class Monitor(UVMMonitor):
    """
    Monitor: 将物理信号时序转换回 SeqItem
    """

    def build_phase(self):
        super().build_phase()
        self.vif = ConfigDB().get(self, "", "VIF")
        if self.vif is None:
            self.fail("Virtual Interface not found in ConfigDB")

        # 实例化分析端口 (Analysis Port),用于将数据包广播出去
        self.ap = UVMAnalysisPort("ap", self)

    async def run_phase(self):
        self.logger.info("Monitor run_phase started")

        while True:
            # --------------------------------------------------
            # LLM_GENERATED_START: MONITOR_LOGIC
            # --------------------------------------------------
            # LLM 将根据<验证计划>生成具体的信号采样逻辑
            # 示例 (一个简单的 valid 握手):
            #
            # await RisingEdge(self.vif.clk)
            # if self.vif.valid_out.value == 1:
            #     # 采样到有效数据
            #     mon_item = MySeqItem()
            #     mon_item.data = self.vif.data_out.value.integer
            #
            #     # 广播这个数据包
            #     self.logger.debug(f"Monitored item: {mon_item}")
            #     self.ap.write(mon_item)
            #
            # (如果需要更复杂的逻辑,比如等待握手完成,LLM需要实现它)
            await RisingEdge(self.vif.clk)  # 保证循环总会释放
            # --------------------------------------------------
            # LLM_GENERATED_END: MONITOR_LOGIC
            # --------------------------------------------------
