# vpilot/skeletons/coverage.py
#
# UVM 功能覆盖率收集器
# 架构: uvm_subscriber
from pyuvm import uvm_subscriber
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db
from seq_item import MySeqItem

# --------------------------------------------------
# LLM_GENERATED_START: COVERAGE_DEFINITIONS
# --------------------------------------------------
# [!!] LLM 的任务:
# 根据<验证计划>的 'coverage_points' 部分,
# 在这里定义 *所有* 的 @CoverPoint 和 @CoverCross
#
# 示例:
#
# @CoverPoint("top.my_item.addr",
#     xf=lambda item: item.addr,          # 'xf' 定义了如何从 item 中提取值
#     bins=list(range(0, 256, 16))        # 'bins' 定义了关心的"桶"
# )
# @CoverPoint("top.my_item.rw",
#     xf=lambda item: item.rw,
#     bins=[0, 1],
#     bins_labels=['READ', 'WRITE']
# )
# @CoverCross("top.my_item.addr_x_rw",
#     items=["top.my_item.addr", "top.my_item.rw"] # 交叉覆盖
# )
# def sample_coverage(item: MySeqItem):
#     """
#     这个函数是一个 'hook' (钩子), cocotb-coverage
#     会自动将上面所有的 @CoverPoint "附加" 到这个函数上.
#     调用这个函数 = 采样所有附加的 @CoverPoint.
#     """
#     pass
#
# --------------------------------------------------
# LLM_GENERATED_END: COVERAGE_DEFINITIONS
# ----------------------------------


class Coverage(uvm_subscriber):
    """
    UVM 覆盖率收集器

    它继承自 uvm_subscriber, 'pyuvm' 框架会自动
    为我们创建 'self.analysis_export' 端口和 'self.write' 方法.
    """

    def build_phase(self):
        super().build_phase()
        # uvm_subscriber *自动* 创建 self.analysis_export
        # 我们不需要在 build_phase 中做任何事
        pass

    def write(self, item: MySeqItem):
        """
        [!!] 关键方法 (由 'analysis_export' 自动调用)
        每当 Monitor 广播一个 item, 此方法就会被触发
        """
        self.logger.debug(f"Coverage sampling item: {item}")

        # --------------------------------------------------
        # LLM_GENERATED_START: COVERAGE_SAMPLE_CALL
        # --------------------------------------------------
        # [!!] LLM的任务:
        # 调用在上面定义的 *采样函数*
        #
        # [!!] LLM生成示例:
        # try:
        #     sample_coverage(item)
        # except Exception as e:
        #     self.logger.error(f"Error during coverage sampling: {e}")
        #
        # --------------------------------------------------
        # LLM_GENERATED_END: COVERAGE_SAMPLE_CALL
        # ----------------------------------

    def report_phase(self):
        """打印覆盖率报告 (框架固定)"""
        self.logger.info("--- Coverage Report ---")
        try:
            # 调用 cocotb-coverage 的全局数据库来打印报告
            coverage_db.report_coverage(self.logger.info, bins=True)
        except Exception as e:
            self.logger.warning(f"Failed to generate coverage report: {e}")
        self.logger.info("-------------------------")
