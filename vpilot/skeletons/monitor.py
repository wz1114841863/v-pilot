from pyuvm import uvm_component, uvm_analysis_port

from base_bfm import BaseBfm
from seq_item import MySeqItem


class Monitor(uvm_component):
    """
    UVM Monitor
    """

    def build_phase(self):
        """
        UVM build_phase: 获取 BFM, 创建分析端口
        """
        super().build_phase()

        # 1. 获取 BFM 单例
        self.bfm = BaseBfm()
        if self.bfm is None:
            self.fail("BFM Singleton not found.")

        # 2. 创建分析端口 (ap)
        #    这是 Monitor 用来 "广播" 数据的标准端口
        #    'env.py' 将连接到这个端口
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        """
        UVM run_phase: 主执行循环
        """
        self.logger.info("Monitor run_phase started (BFM mode)")

        while True:
            # --------------------------------------------------
            # LLM_GENERATED_START: MONITOR_BFM_CALL
            # --------------------------------------------------
            # [!!] LLM 的任务:
            # 1. 调用在 'base_bfm.py' 中定义的 *监视* 任务(们)
            # 2. 将返回的数据组装成一个 'MySeqItem'
            # 3. (可选) 将组装好的 item 赋值给 'mon_item'
            # 4. [!!] 循环中必须至少有一个 'await'
            #
            # 示例 (BFM 提供了 'getter' 方法):
            #
            # await self.bfm.wait_for_input_valid()
            # mon_item = MySeqItem()
            # mon_item.data_in = self.bfm.get_input_data()
            #
            # await self.bfm.wait_for_output_valid()
            # mon_item.data_out = self.bfm.get_output_data()
            #
            # 示例 (BFM 提供了高层 'transaction' 任务):
            #
            # mon_item = await self.bfm.monitor_full_transaction()
            #
            # --------------------------------------------------
            # (LLM 必须在下面 'self.ap.write' 之前,
            #  创建并填充一个名为 'mon_item' 的 MySeqItem)
            mon_item = MySeqItem()  # 占位符, LLM 必须正确填充
            # --------------------------------------------------
            # LLM_GENERATED_END: MONITOR_BFM_CALL
            # --------------------------------------------------

            # 3. 将采集到的数据包广播给所有订阅者 (Scoreboard, Coverage)
            self.logger.debug(f"Monitor broadcasting item: {mon_item}")
            self.ap.write(mon_item)
