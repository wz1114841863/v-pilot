from pyuvm import *
from cocotb_coverage.coverage import CoverPoint, CoverCross, coverage_db

# --------------------------------------------------
# LLM_GENERATED_START: COVERAGE_DEFINITIONS
# --------------------------------------------------
# LLM 将根据<验证计划>的 'coverage_points' 部分定义覆盖点
#
# 示例:
#
# @CoverPoint("top.port_x",
#     xf=lambda item: item.x,
#     bins=list(range(16))
# )
# def cp_port_x(item):
#     pass # 覆盖点函数体不需要内容
#
# @CoverPoint("top.port_y",
#     xf=lambda item: item.y,
#     bins=list(range(16))
# )
# def cp_port_y(item):
#     pass
#
# @CoverCross("top.cross_x_y",
#     items=["top.port_x", "top.port_y"]
# )
# def cp_cross_x_y(item):
#     pass
#
# --------------------------------------------------
# LLM_GENERATED_END: COVERAGE_DEFINITIONS
# ----------------------------------


class Coverage(UVMSubscriber):
    """
    功能覆盖率收集器
    """

    def build_phase(self):
        super().build_phase()
        # --------------------------------------------------
        # LLM_GENERATED_START: COVERAGE_SUBSCRIBER_IMP
        # --------------------------------------------------
        # LLM 将决定订阅哪个分析端口
        # 示例 (订阅 Monitor):
        # self.imp = UVMAnalysisImp("imp", self)
        # self.imp.connect(self.write)
        # --------------------------------------------------
        # LLM_GENERATED_END: COVERAGE_SUBSCRIBER_IMP
        # --------------------------------------------------
        pass

    def write(self, item):
        """
        接收来自 Monitor 的数据包并采样
        """
        self.logger.debug(f"Sampling item: {item}")
        # --------------------------------------------------
        # LLM_GENERATED_START: COVERAGE_SAMPLE_CALLS
        # --------------------------------------------------
        # LLM 调用所有已定义的覆盖点
        # 示例:
        # cp_port_x(item)
        # cp_port_y(item)
        # cp_cross_x_y(item)
        # --------------------------------------------------
        # LLM_GENERATED_END: COVERAGE_SAMPLE_CALLS
        # --------------------------------------------------
        pass

    def report_phase(self):
        # 在仿真结束时打印覆盖率报告
        coverage_db.report_coverage(self.logger.info, bins=True)
        # (可选) 导出 XML 报告
        coverage_db.export_to_xml(filename="coverage.xml")
