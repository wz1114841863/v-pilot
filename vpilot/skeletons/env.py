# vpilot/skeletons/env.py
#
# UVM 顶层环境
# 职责: 1. 实例化 UVM 子组件. 2. 连接 UVM 子组件.
from pyuvm import uvm_env, ConfigDB

from agent import MyAgent
from scoreboard import Scoreboard
from coverage import Coverage


class TestEnv(uvm_env):
    """顶层测试环境"""

    def build_phase(self):
        """实例化所有子组件"""
        super().build_phase()

        # --------------------------------------------------
        # LLM_GENERATED_START: ENV_INSTANTIATION
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 根据plan.yml的 'uvm_components' 部分来实例化 Agents 和 Scoreboards
        #
        # [!!] LLM 填充示例:
        # ConfigDB().set(self, "input_agent", "is_active", 1) # 1 = ACTIVE
        # self.input_agent = MyAgent.create("input_agent", self)
        #
        # ConfigDB().set(self, "output_agent", "is_active", 0) # 0 = PASSIVE
        # self.output_agent = MyAgent.create("output_agent", self)
        #
        # self.scoreboard = Scoreboard.create("scoreboard", self)
        # self.coverage = Coverage.create("coverage", self)
        #
        # --------------------------------------------------
        # LLM_GENERATED_END: ENV_INSTANTIATION
        # --------------------------------------------------

    def connect_phase(self):
        """
        UVM connect_phase: 连接组件的端口
        """
        super().connect_phase()

        # --------------------------------------------------
        # LLM_GENERATED_START: ENV_CONNECTIONS
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 将 'Monitor(s)' 的分析端口 (ap) 连接到
        # 'Scoreboard(s)' 的实现端口 (imp)
        # (LLM 填充示例:)
        # # (连接: Input Monitor -> Scoreboard Expected)
        # self.input_agent.monitor.ap.connect(self.scoreboard.expected_fifo.analysis_export)
        # # (连接: Output Monitor -> Scoreboard Actual)
        # self.output_agent.monitor.ap.connect(self.scoreboard.actual_fifo.analysis_export)
        #
        # # (连接: Monitors -> Coverage)
        # self.input_agent.monitor.ap.connect(self.coverage.analysis_export)
        # self.output_agent.monitor.ap.connect(self.coverage.analysis_export)
        # --------------------------------------------------
        # LLM_GENERATED_END: ENV_CONNECTIONS
        # --------------------------------------------------
