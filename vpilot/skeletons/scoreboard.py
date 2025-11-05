# vpilot/skeletons/scoreboard.py
#
# UVM Scoreboard (BFM 模式)
# 架构: FIFO 异步拉取模式 (基于 TinyALU 示例)
import cocotb
from collections import deque
from pyuvm import uvm_component, uvm_tlm_analysis_fifo
from seq_item import MySeqItem


class Scoreboard(uvm_component):
    """UVM Scoreboard, 采用 FIFO 异步拉取模式"""

    def build_phase(self):
        super().build_phase()

        # --- 1. 实例化 FIFO (订阅) 端口 ---
        # 'expected_fifo' 将连接到 Input Monitor
        self.expected_fifo = uvm_tlm_analysis_fifo("expected_fifo", self)

        # 'actual_fifo' 将连接到 Output Monitor
        self.actual_fifo = uvm_tlm_analysis_fifo("actual_fifo", self)

        # --- 2. 实例化比对队列 (用于解耦) ---
        self.expected_q = deque()
        self.actual_q = deque()

        # --- 3. 实例化统计计数器 (框架固定) ---
        self.pass_count = 0
        self.fail_count = 0

        # --------------------------------------------------
        # LLM_GENERATED_START: REFERENCE_MODEL_INIT
        # --------------------------------------------------
        # [!!] LLM 的任务:
        # 在这里初始化参考模型 (RM) 的 *状态*
        #
        # 示例 (一个累加器 RM 的状态):
        # self.rm_current_sum = 0
        # --------------------------------------------------
        # LLM_GENERATED_END: REFERENCE_MODEL_INIT
        # --------------------------------------------------

    # --------------------------------------------------
    # LLM_GENERATED_START: REFERENCE_MODEL_LOGIC
    # --------------------------------------------------
    # [!!] LLM 的任务:
    # 在这里使用python实现参考模型 (RM) 的 *逻辑*
    #
    # 示例 (累加器 RM 逻辑):
    # def _run_rm_accumulator(self, input_item: MySeqItem):
    #     if input_item.enable:
    #         self.rm_current_sum += input_item.data_in
    #     pred_item = MySeqItem()
    #     pred_item.data_out = self.rm_current_sum
    #     return pred_item
    #
    # --------------------------------------------------
    # LLM_GENERATED_END: REFERENCE_MODEL_LOGIC
    # --------------------------------------------------

    async def run_phase(self):
        """
        UVM run_phase: 启动两个并行的 "listener" 任务
        """
        # 启动两个并行的协程 (coroutine)
        # 一个用于处理 "预期" (input)
        # 一个用于处理 "实际" (output)
        cocotb.start_soon(self._expected_listener())
        cocotb.start_soon(self._actual_listener())

    async def _expected_listener(self):
        """
        (私有) 异步任务:
        从 Input Monitor 拉取数据, 运行 RM, 存入预期队列
        """
        while True:
            # 1. 异步等待 Input Monitor 广播一个 item
            input_item = await self.expected_fifo.get()
            self.logger.debug(f"Scoreboard got EXPECTED (input) item: {input_item}")

            # --------------------------------------------------
            # LLM_GENERATED_START: SB_RUN_RM
            # --------------------------------------------------
            # [!!] LLM 的任务:
            # 1. 调用 RM 逻辑 (在上面定义)
            # 2. 将 RM *预测的输出* 存入 'self.expected_q'
            #
            # 示例 (累加器):
            # predicted_output = self._run_rm_accumulator(input_item)
            # self.expected_q.append(predicted_output)
            #
            # --------------------------------------------------
            # LLM_GENERATED_END: SB_RUN_RM
            # --------------------------------------------------

    async def _actual_listener(self):
        """
        (私有) 异步任务:
        从 Output Monitor 拉取数据, 存入实际队列
        """
        while True:
            # 1. 异步等待 Output Monitor 广播一个 item
            actual_item = await self.actual_fifo.get()
            self.logger.debug(f"Scoreboard got ACTUAL (output) item: {actual_item}")

            # 2. 存入 'actual_q' (框架固定)
            self.actual_q.append(actual_item)

    def check_phase(self):
        self.logger.info("Scoreboard check_phase starting...")

        while self.expected_q and self.actual_q:
            expected_item = self.expected_q.popleft()
            actual_item = self.actual_q.popleft()

            if expected_item == actual_item:
                self.logger.info(
                    f"PASS: Expected={expected_item}, Actual={actual_item}"
                )
                self.pass_count += 1
            else:
                self.logger.error(
                    f"FAIL: Expected={expected_item}, Actual={actual_item}"
                )
                self.fail_count += 1

        while self.expected_q:
            self.logger.error(
                f"FAIL: Extra expected item (DUT did not send): {self.expected_q.popleft()}"
            )
            self.fail_count += 1

        while self.actual_q:
            self.logger.error(
                f"FAIL: Extra actual item (unexpected from DUT): {self.actual_q.popleft()}"
            )
            self.fail_count += 1

    def report_phase(self):
        self.logger.info(
            f"Scoreboard Report: PASS={self.pass_count}, FAIL={self.fail_count}"
        )
        if self.fail_count > 0:
            msg = f"Scoreboard failed with {self.fail_count} mismatches."
            self.logger.error(msg)

            # [关键] 抛出异常以通知 cocotb 测试失败
            #    否则 cocotb 会错误地报告 PASS
            raise AssertionError(msg)
        elif self.pass_count == 0:
            self.logger.warning(
                "Scoreboard finished with PASS=0. No transactions were checked."
            )
        else:
            self.logger.info(f"Scoreboard PASSED with {self.pass_count} items checked.")
