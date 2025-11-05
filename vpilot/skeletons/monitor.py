# vpilot/skeletons/monitor.py
#
# UVM Monitor (BFM 模式)
# 职责: 1. 调用 BFM 采集数据. 2. 组装 SeqItem. 3. 广播 (ap.write).
from pyuvm import uvm_component, uvm_analysis_port

from base_bfm import BaseBfm
from seq_item import MySeqItem


class Monitor(uvm_component):
    """UVM Monitor"""

    def build_phase(self):
        """获取 BFM, 创建分析端口"""
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
        """主执行循环"""
        self.logger.info("Monitor run_phase started (BFM mode)")

        while True:
            # --------------------------------------------------
            # LLM_GENERATED_START: MONITOR_BFM_CALL
            # --------------------------------------------------
            # (LLM 填充示例:)
            # # (调用在 base_bfm.py 中定义的 BFM 方法)
            # # 1. 等待并采集
            # monitored_data = await self.bfm.monitor_output_transaction()
            #
            # # 2. 组装
            # mon_item = MySeqItem()
            # mon_item.data_out = monitored_data
            #
            # # 3. 广播
            # self.ap.write(mon_item)
            #
            # (LLM 必须确保此块中至少有一个 'await')
            # (如果 BFM 只有 getter, LLM 必须 await self.bfm.wait_clock())
            await self.bfm.wait_clock(1)  # (一个安全的占位符)
            # --------------------------------------------------
            # LLM_GENERATED_END: MONITOR_BFM_CALL
            # --------------------------------------------------
