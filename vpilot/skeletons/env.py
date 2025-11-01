from pyuvm import uvm_env, ConfigDB

# --- 导入子组件 (LLM将需要它们) ---
# 注意: 我们将 *假定* agent.py 定义了 MyAgent, scoreboard.py 定义了 Scoreboard
from agent import MyAgent
from scoreboard import Scoreboard


class TestEnv(uvm_env):
    """
    顶层测试环境

    职责:
    1. 实例化所有 Agents, Scoreboards, Coverage Collectors 等.
    2. 连接所有组件的分析端口 (Analysis Ports).
    """

    def build_phase(self):
        super().build_phase()

        # --------------------------------------------------
        # LLM_GENERATED_START: ENV_INSTANTIATION
        # --------------------------------------------------
        # LLM 将根据<验证计划>的 'uvm_components' 部分来实例化 Agents 和 Scoreboards
        #
        # 示例 (单Agent, 单Scoreboard):
        self.agent = MyAgent.create("agent", self)
        self.scoreboard = Scoreboard.create("scoreboard", self)

        # 示例 (双Agent, In/Out):
        # self.in_agent = MyAgent.create("in_agent", self)
        # self.in_agent.set_is_active(UVM_ACTIVE) # 设为 Active
        #
        # self.out_agent = MyAgent.create("out_agent", self)
        # self.out_agent.set_is_active(UVM_PASSIVE) # 设为 Passive
        #
        # self.scoreboard = Scoreboard.create("scoreboard", self)
        # --------------------------------------------------
        # LLM_GENERATED_END: ENV_INSTANTIATION
        # --------------------------------------------------

    def connect_phase(self):
        super().connect_phase()

        # --------------------------------------------------
        # LLM_GENERATED_START: ENV_CONNECTIONS
        # --------------------------------------------------
        # LLM 将根据 'uvm_components' 建立连接
        #
        # 示例 (单Agent):
        # 将 monitor 的分析端口 (ap) 连接到 scoreboard 的分析入口 (actual_imp)
        self.agent.monitor.ap.connect(self.scoreboard.actual_imp)

        # 示例 (双Agent, In/Out):
        # self.in_agent.monitor.ap.connect(self.scoreboard.expected_imp)
        # self.out_agent.monitor.ap.connect(self.scoreboard.actual_imp)
        # --------------------------------------------------
        # LLM_GENERATED_END: ENV_CONNECTIONS
        # --------------------------------------------------
