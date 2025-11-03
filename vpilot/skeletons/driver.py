from pyuvm import uvm_driver
from pyuvm.s14_15_python_sequences import uvm_seq_item_port
from base_bfm import BaseBfm  # 导入 BFM 单例


class Driver(uvm_driver):
    """
    UVM Driver
    """

    def build_phase(self):
        """
        UVM build_phase: 获取 BFM, 创建端口
        """
        super().build_phase()

        # 1. 获取 BFM 单例
        self.bfm = BaseBfm()
        if self.bfm is None:
            self.fail("BFM Singleton not found.")

        # 2. 创建 seq_item_port
        self.seq_item_port = uvm_seq_item_port("seq_item_port", self)

    async def run_phase(self):
        """
        UVM run_phase: 主执行循环
        """
        self.logger.info("Driver run_phase started (BFM mode)")

        while True:
            # 1. 从 Sequencer 获取下一个数据包 (transaction)
            #    'await' 会在此暂停, 直到 Sequencer 发送了一个 item
            seq_item = await self.seq_item_port.get_next_item()

            self.logger.debug(f"Driver got item: {seq_item}")

            # --------------------------------------------------
            # LLM_GENERATED_START: DRIVER_BFM_CALL
            # --------------------------------------------------
            # [!!] LLM 的任务:
            # 调用在 'base_bfm.py' 中由 LLM 定义的 *对应* BFM 方法
            #
            # 示例:
            # await self.bfm.drive_input_transaction(seq_item)
            #
            # 示例 (如果是读操作):
            # read_data = await self.bfm.sw_read(seq_item.addr)
            # seq_item.data_out = read_data # 将读到的数据写回 item
            #
            # --------------------------------------------------
            # LLM_GENERATED_END: DRIVER_BFM_CALL
            # --------------------------------------------------

            # 3. 通知 Sequencer,此数据包已处理完毕
            #    (如果 item 是读操作, 此时 item 已被 BFM 的返回值更新)
            self.seq_item_port.item_done()
