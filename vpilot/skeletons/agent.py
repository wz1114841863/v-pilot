# vpilot/skeletons/agent.py
#
# UVM Agent
# 职责: 1. 封装 Driver, Monitor, Sequencer. 2. 基于 is_active 构建.
from pyuvm import (
    uvm_agent,
    uvm_sequencer,
    uvm_active_passive_enum,
    ConfigDB,
    error_classes,
    uvm_component,
)
from driver import Driver
from monitor import Monitor


class MyAgent(uvm_agent):
    """UVM Agent"""

    def build_phase(self):
        """UVM build_phase: 实例化子组件"""
        uvm_component.build_phase(self)
        self.is_active = uvm_active_passive_enum.UVM_ACTIVE

        try:
            # Env 将通过 ConfigDB 设置 "is_active" (1 或 0)
            is_active_int = ConfigDB().get(self, "", "is_active")
            self.is_active = uvm_active_passive_enum(is_active_int)
        except error_classes.UVMConfigItemNotFound:
            # (如果 Env 没有设置, 默认为 ACTIVE)
            self.is_active = uvm_active_passive_enum.UVM_ACTIVE

        # Monitor 总是被创建 (无论是 ACTIVE 还是 PASSIVE)
        self.monitor = Monitor.create("monitor", self)
        # 仅在 ACTIVE 模式下创建 Driver 和 Sequencer
        if self.get_is_active() == 1:
            self.driver = Driver.create("driver", self)
            self.sequencer = uvm_sequencer.create("sequencer", self)

    def connect_phase(self):
        """UVM connect_phase: 连接子组件"""
        super().connect_phase()

        # 仅在 ACTIVE 模式下连接 Driver 和 Sequencer
        if self.get_is_active() == 1:
            # 将 Driver 的 seq_item_port 连接到 Sequencer 的 seq_item_export
            # 这样 Driver 才能调用 self.seq_item_port.get_next_item()
            self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

    def get_is_active(self):
        """(从 pyuvm 源码复制)"""
        return self.is_active
