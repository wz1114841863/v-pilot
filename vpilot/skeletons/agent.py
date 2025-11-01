from pyuvm import *
from driver import Driver
from monitor import Monitor
from seq_item import MySeqItem  # 导入我们将使用的数据包


class MyAgent(UVMAgent):
    """
    UVM Agent (100% 可复用骨架)
    """

    def build_phase(self):
        super().build_phase()
        self.monitor = Monitor.create("monitor", self)

        # 根据 is_active 标志决定是否创建 Driver 和 Sequencer
        if self.is_active == UVM_ACTIVE:
            self.driver = Driver.create("driver", self)
            self.sequencer = UVMSequencer.create("sequencer", self)
            # 设置 Sequencer 使用的数据包类型
            ConfigDB().set(self, "sequencer", "item_type", MySeqItem)

    def connect_phase(self):
        super().connect_phase()
        if self.is_active == UVM_ACTIVE:
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
