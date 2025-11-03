import typer
from pathlib import Path
import yaml
import shutil
import json
import subprocess
import re

from vpilot.core.code_manager import CodeManager
from vpilot.core.llm_handler import execute_conversation_turn

app = typer.Typer(help="管理 UVM 测试平台的构建和迭代")

# 定义工作目录和状态文件
VPILOT_RUN_DIR = Path("./vpilot_run")
STATE_FILE = VPILOT_RUN_DIR / ".vpilot.state.json"
UVM_TB_DIR = Path("./uvm_tb")
SKELETON_DIR = Path(__file__).parent.parent / "skeletons"
UVM_BUILD_HISTORY = VPILOT_RUN_DIR / "uvm_build.history.json"

# UVM会话
UVM_BUILD_SYSTEM_PROMPT = """
你是 'UVM 构建领航员' (UVM Build Navigator).
你的任务是与我 (v-pilot 引擎) 协作, 逐块填充 UVM 骨架文件.
该骨架由cocotb 和 pyuvm 编写, 均为 Python 语言.
我将为你提供 'spec.yml' 和 'plan.yml'.
我将按顺序给你下达任务, 比如 "填充 BFM_HANDLES".

[!!] 您的响应 *必须* 严格遵守以下格式 [!!]

1.  **对于代码填充 (Code Filling):**
    您 *必须* 使用 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 格式作为代码块的 *头部*.
    例如:
    v-pilot:fill:env.py:ENV_INSTANTIATION
    self.input_agent = MyAgent.create("input_agent", self)
    self.output_agent = MyAgent.create("output_agent", self)

2.  **对于上下文提取 (Context Extraction):**
    当我要求您提供上下文时 (例如, 您刚刚生成的方法名列表),
    您 *必须* 使用 'v-pilot:context:[key]:[value]' 格式.
    例如:
    v-pilot:context:bfm_methods:[reset, drive_input]

3.  **对于多块响应 (Multiple Blocks):**
    如果一个任务要求您填充 *多个* 代码块, 您必须在您的 *单个* 响应中
    提供 *多个* 'v-pilot:fill:...' 块.

4.  **纯净性 (Purity):**
    *绝对禁止* 在您的响应中包含任何额外的问候/解释或 Markdown
    标记 (例如 '```python').
    您的响应 *必须* 仅由 'v-pilot:fill:...' 和 'v-pilot:context:...'
    标签和它们的内容组成.

在后续的迭代中, 我会为你提供 'make' 的失败日志, 你必须分析 *整个对话历史*
和错误日志, 找出并提供 *修正后* 的 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 代码块.
"""


def load_state():
    """辅助函数: 加载并验证状态文件"""
    if not STATE_FILE.exists():
        typer.secho("错误: 找不到项目状态文件 .vpilot.state.json.", fg=typer.colors.RED)
        typer.echo("  > 请先运行 'vpilot spec init'.")
        raise typer.Exit(code=1)
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        typer.secho(f"错误: 状态文件 .vpilot.state.json 损坏: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def _execute_task(prompt: str) -> str:
    """
    一个包装器, 封装了调用 LLM 并打印状态的逻辑
    """
    # 打印任务标题 (假设 Prompt 的第二行是标题)
    # try:
    #     title = [line for line in prompt.splitlines() if line.strip()][1]
    #     typer.echo(f"  > 正在执行: {title.strip()}")
    # except IndexError:
    #     typer.echo(f"  > 正在执行新任务...")
    typer.echo(f"  > 正在执行新任务...")
    response = execute_conversation_turn(UVM_BUILD_HISTORY, "", prompt)
    return response


def _parse_and_inject(response: str, code_manager: CodeManager) -> dict:
    """
    解析 LLM 的响应, 提取 'fill' 和 'context' 块.
    """
    build_context = {}

    # 我们将响应按 'v-pilot:' 标签分割
    for block in response.split("v-pilot:"):
        if not block.strip():
            continue

        try:
            # [!!] 关键修复:
            # 我们不再假设 *所有* 块都有换行符
            #
            block_lines = block.strip().split("\n", 1)
            header = block_lines[0].strip()
            content = (
                block_lines[1] if len(block_lines) > 1 else ""
            )  # (如果单行, content 为空)

            header_parts = header.strip().split(":")
            cmd_type = header_parts[0]  # "fill" or "context"

            if cmd_type == "fill":
                # 格式: fill:[filename.py]:[BLOCK_ID]
                if len(header_parts) != 3:
                    raise ValueError(f"Fill 头部格式错误: {header}")
                if not content:
                    # 'fill' 块不应该为空
                    raise ValueError(f"Fill 块内容为空: {header}")

                file_to_fix = header_parts[1].strip()
                block_to_fix = header_parts[2].strip()

                code_manager.update_block(file_to_fix, block_to_fix, content)

            elif cmd_type == "context":
                # 格式: context:[key]:[value_or_list_str]
                # [!!] 关键修复:
                # 'context' 是一个 *单行* 命令, content 应该是空的
                if len(header_parts) != 3:
                    raise ValueError(f"Context 头部格式错误: {header}")

                key = header_parts[1].strip()
                value_str = header_parts[2].strip()

                # (解析上下文值的逻辑保持不变)
                if value_str.startswith("[") and value_str.endswith("]"):
                    build_context[key] = [
                        m.strip().strip("'\"")
                        for m in value_str[1:-1].split(",")
                        if m.strip()
                    ]
                else:
                    build_context[key] = value_str

        except Exception as e:
            typer.secho(
                f"  > [!!] 警告: 无法解析 LLM 响应块: {e}", fg=typer.colors.YELLOW
            )
            typer.echo(f"  > 块内容 (前100字符): {block[:100]}...")

    return build_context


@app.command("build", help="[!!] 启动一个交互式会话来构建 UVM 脚手架")
def build():
    """
    'uvm build', 这是一个有状态的会话
    """
    typer.echo("启动 UVM 构建会话...")
    # --- 1. 门控检查和加载 ---
    state = load_state()
    if not state.get("plan_approved"):
        typer.secho("错误: <验证计划> (plan) 尚未批准.", fg=typer.colors.RED)
        typer.echo("  > 请先运行 'vpilot plan approve --version <v>' 批准一个计划.")
        raise typer.Exit(code=1)

    if state.get("current_stage") != "uvm_build":
        typer.secho(
            f"警告: 状态文件中的 'current_stage' "
            f"({state.get('current_stage')}) 不是 'uvm_build'.",
            fg=typer.colors.YELLOW,
        )
        typer.echo("  > 但 'plan_approved' 为 true, 将继续执行...")

    spec_file_path = Path(state.get("final_spec_file"))
    plan_file_path = Path(state.get("final_plan_file"))
    if not spec_file_path.exists() or not plan_file_path.exists():
        typer.secho(
            f"错误: 状态文件指向的 spec ({spec_file_path}) "
            f"或 plan ({plan_file_path}) 文件不存在.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    spec_text = spec_file_path.read_text(encoding="utf-8")
    plan_text = plan_file_path.read_text(encoding="utf-8")
    spec = yaml.safe_load(spec_text)
    plan = yaml.safe_load(plan_text)

    if spec.get("design_type") != "sequential":
        typer.secho(
            f"错误: design_type '{spec.get('design_type')}' 尚不支持."
            "v-pilot 目前仅支持 'sequential'.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # --- 2. 复制骨架 ---
    if UVM_TB_DIR.exists():
        typer.secho("警告: 'uvm_tb/' 目录已存在, 将被覆盖.", fg=typer.colors.YELLOW)
        shutil.rmtree(UVM_TB_DIR)
    shutil.copytree(SKELETON_DIR, UVM_TB_DIR)
    typer.echo(f"  > 已将骨架文件复制到 {UVM_TB_DIR}/")

    # --- 3. 初始化 CodeManager ---
    code_manager = CodeManager(UVM_TB_DIR)
    if UVM_BUILD_HISTORY.exists():
        UVM_BUILD_HISTORY.unlink()
    # 维护一个内部状态, 用来存储 LLM 在上一步生成的 *关键信息*
    build_context = {}

    # --- 4. [!!] 启动"总调度循环" [!!] ---

    # 任务 0: 发送系统提示和蓝图
    initial_prompt = f"""
    {UVM_BUILD_SYSTEM_PROMPT}
    --- 蓝图 1: design_spec.final.yml ---
    {spec_text}
    --- 蓝图 2: verif_plan.final.yml ---
    {plan_text}
    请确认你已准备好, 等待我的第一个任务.
    """
    execute_conversation_turn(UVM_BUILD_HISTORY, "", initial_prompt)

    # ---
    # 任务 1: Makefile (顶层模块)
    # ---
    prompt = """
    任务 1: 填充 'Makefile' 的 'COCOTB_TOPLEVEL' 块.
    根据 'design_spec.yml' 中的 'module_name' 字段.

    [!!] 响应格式:
    v-pilot:fill:Makefile:COCOTB_TOPLEVEL
    COCOTB_TOPLEVEL := (你的模块名)
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 2: base_bfm.py (所有 BFM 逻辑)
    # ---
    prompt = """
    任务 2: 填充 'base_bfm.py' 中的 *所有* 4 个 LLM 块:
    1. 'BFM_HANDLES' (根据 'spec.key_signals')
    2. 'BFM_RESET_TASK' (根据 'spec.key_signals')
    3. 'BFM_DRIVER_TASKS' (根据 'spec.ports' 中所有 'input' 端口)
    4. 'BFM_MONITOR_TASKS_AND_GETTERS' (根据 'spec.ports' 中所有 'input' 和 'output' 端口)

    [!!] 响应格式:
    请在响应中包含你生成的 *所有* BFM 方法 (包括 'reset') 的名称列表:
    'v-pilot:context:bfm_methods:[reset, drive_input, wait_for_output, get_output_data]'

    并为所有 4 个代码块使用 'v-pilot:fill:base_bfm.py:[BLOCK_ID]'.
    """
    response = _execute_task(prompt)
    ctx = _parse_and_inject(response, code_manager)
    build_context.update(ctx)  # (保存 'bfm_methods' 列表)

    # ---
    # 任务 3: seq_item.py (所有字段)
    # ---
    prompt = """
    任务 3: 填充 'seq_item.py' 中的 *所有* 4 个 LLM 块:
    1. 'SEQ_ITEM_FIELDS' (根据 'spec.ports' 中所有相关的数据/控制端口)
    2. 'SEQ_ITEM_RANDOMIZE'
    3. 'SEQ_ITEM_STR'
    4. 'SEQ_ITEM_EQ' (必须比较所有 *输出* 字段)

    [!!] 响应格式:
    请使用 'v-pilot:fill:seq_item.py:[BLOCK_ID]'.
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 4: driver.py (BFM 调用)
    # ---
    prompt = f"""
    任务 4: 填充 'driver.py' 的 'DRIVER_BFM_CALL' 块.

    [!!] 关键上下文:
    你在任务 2 中 (在 'base_bfm.py' 中) 生成了以下可用 BFM 方法:
    {build_context.get('bfm_methods', '[]')}

    你 *必须* 从该列表中选择 'drive'/'write' 相关的方法来调用.
    (e.g., 'await self.bfm.drive_input_transaction(seq_item)')

    [!!] 严格规则: 你 *禁止* 在此块中导入 'cocotb'.

    [!!] 响应格式:
    v-pilot:fill:driver.py:DRIVER_BFM_CALL
    ... (你的代码) ...
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 5: monitor.py (BFM 调用)
    # ---
    prompt = f"""
    任务 5: 填充 'monitor.py' 的 'MONITOR_BFM_CALL' 块.

    [!!] 关键上下文:
    1. 你在 BFM 中生成的可用方法: {build_context.get('bfm_methods', '[]')}
    2. 你 *必须* 创建一个 'MySeqItem' 实例: `mon_item = MySeqItem()`

    你的任务是:
    1. 调用你在 BFM 中生成的 'monitor' 或 'getter' 方法.
    2. 将 BFM 返回的数据填充到 'mon_item' 中.
    3. 确保 'self.ap.write(mon_item)' 在最后被调用.

    [!!] 响应格式:
    v-pilot:fill:monitor.py:MONITOR_BFM_CALL
    ... (你的代码) ...
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 6: scoreboard.py (RM, RM 调用)
    # ---
    prompt = """
    任务 6: 填充 'scoreboard.py' 中的 *所有* 3 个 LLM 块:
    1. 'REFERENCE_MODEL_INIT'
    2. 'REFERENCE_MODEL_LOGIC' (定义 RM 的 'def _run_rm_...' 方法)
    3. 'SB_RUN_RM' (在 _expected_listener 中调用 RM, 并存入 'self.expected_q')

    [!!] 响应格式:
    请使用 'v-pilot:fill:scoreboard.py:[BLOCK_ID]'.
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 7: env.py (拓扑)
    # ---
    prompt = """
    任务 7: 填充 'env.py' 中的 *所有* 2 个 LLM 块:
    1. 'ENV_INSTANTIATION' (根据 'plan.uvm_topology.agents' 和 'scoreboards')
    2. 'ENV_CONNECTIONS' (根据 'plan.uvm_topology' 中的连接信息)

    [!!] 响应格式:
    请在响应中包含你实例化的 *所有* sequencer 的 *完整访问路径*
    (e.g., 'v-pilot:context:sequencers:[self.env.input_agent.sequencer]')

    请使用 'v-pilot:fill:env.py:[BLOCK_ID]'.
    """
    response = _execute_task(prompt)
    ctx = _parse_and_inject(response, code_manager)
    build_context.update(ctx)  # (保存 'sequencers' 列表)

    # ---
    # 任务 8: coverage.py (覆盖点)
    # ---
    prompt = """
    任务 8: 填充 'coverage.py' 中的 *所有* 2 个 LLM 块:
    1. 'COVERAGE_DEFINITIONS' (根据 'plan.coverage_points' 列表,
       生成 '@CoverPoint' 定义, 和 'sample_coverage' 函数)
    2. 'COVERAGE_SAMPLE_CALL' (在 'write' 方法中, 调用 'sample_coverage(item)')

    [!!] 响应格式:
    请使用 'v-pilot:fill:coverage.py:[BLOCK_ID]'.
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 9: sequence_lib.py (序列)
    # ---
    prompt = f"""
    任务 9: 填充 'sequence_lib.py' 的 'SEQUENCES' 块.

    [!!] 关键上下文:
    你 *必须* 使用的 Sequence Item (数据包) 类名是 'MySeqItem'.

    [!!] 严格规则: (我们之前讨论过的)
    'Sequence' *只* 允许做 UVM 序列的工作:
    'self.item.randomize()', 'await self.start_item(self.item)', 等.

    你 *绝对禁止* 访问 'self.dut', 'self.bfm', 或 'self.agent'.

    [!!] 例外 (来自您的反馈):
    *只有* 在 'plan.sequence_library' 描述中 *明确* 要求
    'fork/join' 或 'parallel' 时, 你才 *被允许* 导入 'cocotb'
    并使用 'cocotb.start_soon()'.

    [!!] 响应格式:
    v-pilot:fill:sequence_lib.py:SEQUENCES
    ... (你的代码, 如果需要导入, import 语句在代码块 *内部*) ...
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 10: test_lib.py (测试注册)
    # ---
    prompt = f"""
    任务 10: 填充 'test_lib.py' 的 'TESTS' 块.

    [!!] 关键上下文 (Sequencers):
    你在任务 7 (Env) 中创建的 Sequencer 路径有:
    {build_context.get('sequencers', '[]')}

    [!!] 关键上下文 (Imports):
    'test_lib.py' 骨架文件已经包含了:
    `import sequence_lib as seq_lib`

    你的任务是:
    1. 根据 'plan.sequence_library' 列表, 为 *每一项* 生成一个 '@pyuvm.test()' 类.
    2. 每一个类都 *必须* 继承自 'MyBaseTest'.
    3. 每一个类都 *必须* 重写 'async def main_phase(self)'.
    4. 在 'main_phase' 中, 你 *必须* 使用 `seq_lib.` **命名空间**
       来 `create` 对应的序列.

       [!!] 正确示例:
       `seq = seq_lib.BasicDataTestSeq.create("seq")`
       `await seq.start(...)`

       [!!] 错误示例 (将导致 NameError):
       `seq = BasicDataTestSeq.create("seq")`

    5. 你 *必须* 使用一个 *正确* 的 Sequencer 路径 (来自上面的上下文).

    [!!] 响应格式:
    v-pilot:fill:test_lib.py:TESTS
    ... (你的代码) ...
    """
    response = _execute_task(prompt)
    _parse_and_inject(response, code_manager)

    typer.secho("✅ UVM 脚手架已初步生成完毕!", fg=typer.colors.GREEN)
    typer.echo("-----------------------------------------------------")
    typer.secho("下一步:", bold=True)
    typer.echo("1. 'cd uvm_tb'")
    typer.echo("2. 'make' (运行冒烟测试)")
    typer.echo("3. 如果失败, 复制 'make' 的错误日志到 'make_fail.log'")
    typer.echo("4. 运行 'vpilot uvm iterate-build --feedback-file make_fail.log'")


@app.command("iterate-build", help="提交 'make' 失败日志, 让 LLM 修复")
def iterate_build(
    feedback_file: Path = typer.Option(
        ..., "--feedback", "-f", help="包含 'make' 失败日志的 .log 文件"
    )
):
    typer.echo(f"🚀 正在提交 'make' 失败日志, 请求 LLM 修复...")

    if not UVM_BUILD_HISTORY.exists():
        typer.secho("错误: 找不到 'uvm_build.history.json'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    feedback_log = feedback_file.read_text(encoding="utf-8")

    prompt_task_fix = f"""
    [!!] 迭代修复任务:

    'make' (冒烟测试) 失败了.这是完整的失败日志:
    --- MAKE LOG START ---
    {feedback_log}
    --- MAKE LOG END ---

    请仔细分析 *你之前生成的代码* (在我们的对话历史中) 和这个错误日志.

    你需要:
    1. 诊断问题 (e.g., "AttributeError: 'Env' object has no 'input_agent'").
    2. 找出是 *哪一个* 代码块 (e.g., 'env.py' 的 'ENV_INSTANTIATION') 导致的.
    3. 提供 *修正后的完整代码块*.

    [!!] 响应格式:
    请 *只* 使用 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 格式来响应,
    例如:
    v-pilot:fill:env.py:ENV_INSTANTIATION
    self.input_agent = MyAgent.create("input_agent", self) # (修正后的代码)
    ...
    """

    response_fix = execute_conversation_turn(UVM_BUILD_HISTORY, "", prompt_task_fix)

    # --- 自动修复 (使用 V2 解析器) ---
    try:
        code_manager = CodeManager(UVM_TB_DIR)
        # V2 解析器现在可以正确处理这种格式
        _parse_and_inject(response_fix, code_manager)

        typer.secho("✅ 代码已自动修复! 请重新运行 'make'.", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"错误: 自动修复失败: {e}", fg=typer.colors.RED)
        typer.echo("LLM 原始响应:")
        typer.echo(response_fix)
