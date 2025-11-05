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
你是一名顶级的 UVM 测试平台开发工程师 (Python - pyuvm).
你的任务是与我 (v-pilot 引擎) 一同协作,
根据我提供的设计描述文件(spec.yml)/验证计划文件(plan.yml)
以及 *当前正在编辑的骨架文件* 内容, 逐块填充 UVM 骨架.

我将按顺序给你下达任务, 比如 "填充 'base_bfm.py' 中的 BFM_HANDLES 块".

[!!] 您的响应 *必须* 严格遵守以下格式 [!!]

1.  **代码填充 (Code Filling):**
    你 *必须* 使用 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 格式
    作为 *每一个* 代码块的 *头部*.

2.  **多块响应 (Multiple Blocks):**
    如果一个任务要求你填充 *多个* 代码块 (例如 BFM_HANDLES 和 BFM_RESET_TASK),
    你 *必须* 在你的 *单个* 响应中, 提供 *多个* 'v-pilot:fill:[filename.py]:...' 块.

3.  **Python 缩进 (Indentation) - [!!] 关键规则 [!!]**
    我(v-pilot 引擎)会向你展示骨架文件的 *当前内容*.
    你 *必须* 仔细观察 'LLM_GENERATED_START:...' 标签 *本身* 的缩进.
    你返回的代码 *必须* 匹配那个缩进级别, 同时符合python的语法规则.

    例如: 如果骨架是:

        class MyClass:
            # --------------------------
            # LLM_GENERATED_START: MY_BLOCK
            # LLM_GENERATED_END: MY_BLOCK
            # --------------------------

    你的响应 *必须* 像这样包含相同的缩进:

    v-pilot:fill:myfile.py:MY_BLOCK
            # 你的代码从这里开始, 具有相同的缩进
            self.my_var = 10

4.  **导入 (Imports):**
    如果你的代码块需要 *额外* 的导入 (例如 'import cocotb'
    用于 fork/join 序列), 你 *必须* 将 'import' 语句放在
    'v-pilot:fill:...' 块 *内部* 的最上方.

5.  **响应顺序和纯净性 (Order & Purity):**
    你的响应 *必须* 仅由 'v-pilot:fill:...' 和 'v-pilot:context:...' 标签
    和它们的内容组成.

    * *首先*, 包含 *所有* 的 'v-pilot:fill:...' 代码块.
    * *最后*, (如果我要求了), 才包含 'v-pilot:context:...' 元数据块.
    * *绝对禁止* 包含任何额外的问候/解释或 Markdown 标记 (例如 '```python').

6.  **迭代修复 (Iteration):**
    在后续的迭代中, 我会为你提供 'make' 的失败日志.你 *必须*
    分析 *整个对话历史* 和错误日志, 并 *只* 提供
    *修正后* 的 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 代码块.
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


def _execute_task_with_context(
    relative_file_to_edit: str,
    dependent_files: list[str],
    task_prompt: str,
) -> str:
    """
    1. 读取 'relative_file_to_edit' (要编辑的文件).
    2. [!!] 读取 *所有* 'dependent_files' (依赖文件).
    3. 将 *全部* 内容组合成一个 "超级 Prompt".
    4. 调用 LLM.
    """
    try:
        title = [line for line in task_prompt.splitlines() if line.strip()][1]
        typer.echo(f"  > 正在执行: {relative_file_to_edit} ({title.strip()})")
    except IndexError:
        typer.echo(f"  > 正在执行: {relative_file_to_edit}")

    # 1. 构建 "依赖文件" 上下文
    dependency_context = ""
    for dep_file in dependent_files:
        try:
            dep_content = (UVM_TB_DIR / dep_file).read_text(encoding="utf-8")
            dependency_context += f"""
                [!!] 依赖文件: {dep_file}
                --- (内容开始) ---
                {dep_content}
                --- (内容结束) ---
            """
        except Exception:
            # (忽略无法读取的文件, 例如在任务 7 之前 scoreboard.py 还没有被创建)
            pass

    # 2. 读取 "正在编辑的文件"
    try:
        current_file_content = (UVM_TB_DIR / relative_file_to_edit).read_text(
            encoding="utf-8"
        )
    except Exception as e:
        typer.secho(
            f"  > [!!] 错误: 无法读取骨架文件: {relative_file_to_edit}: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # 3. 构建 V-Final 完整 Prompt
    full_prompt = f"""
    {task_prompt}
    # (↑ 'task_prompt' 现在包含 v-pilot 提供的 *关键字*)

    {dependency_context}

    [!!] 核心上下文: 正在编辑的文件
    --- {relative_file_to_edit} ---
    {current_file_content}
    --- (文件结束) ---

    请分析 *所有* 上下文 (任务指令, 依赖文件, 正在编辑的文件),
    并回忆 (从我们的对话历史最开始) 'spec.yml' 和 'plan.yml' 的完整内容,
    来完成此任务. 提供的注释代码仅用来提供参考, 你需要根据实际情况进行调整.

    请严格按照 'v-pilot:fill:...' 格式响应.
    """

    response = execute_conversation_turn(UVM_BUILD_HISTORY, "", full_prompt)
    return response


def _parse_and_inject(response, code_manager):
    build_context = {}

    for block in response.split("v-pilot:"):
        if not block.strip():
            continue

        try:
            block_lines = block.strip().split("\n", 1)
            header = block_lines[0].strip()
            content = block_lines[1] if len(block_lines) > 1 else ""

            header_parts = header.strip().split(":")
            cmd_type = header_parts[0]

            if cmd_type == "fill":
                if len(header_parts) != 3:
                    raise ValueError(f"Fill 头部格式错误: {header}")
                if not content:
                    raise ValueError(f"Fill 块内容为空: {header}")

                file_to_fix = header_parts[1].strip()
                block_to_fix = header_parts[2].strip()

                # CodeManager会自动清理 content
                code_manager.update_block(file_to_fix, block_to_fix, content)

            elif cmd_type == "context":
                if len(header_parts) != 3:
                    raise ValueError(f"Context 头部格式错误: {header}")

                key = header_parts[1].strip()
                value_str = header_parts[2].strip()

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
    'uvm build', 一个有状态的会话
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
    spec_data = yaml.safe_load(spec_text)
    plan_data = yaml.safe_load(plan_text)

    if spec_data.get("design_type") != "sequential":
        typer.secho(
            f"错误: design_type '{spec_data.get('design_type')}' 尚不支持."
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
    build_context = {
        "module_name": spec_data.get("module_name", "UNKNOWN_MODULE"),
        "key_signals": spec_data.get("key_signals", {}),
        "ports": spec_data.get("ports", []),
        "spec_description": spec_data.get("description", ""),
        "uvm_topology": plan_data.get("uvm_topology", {}),
        "sequence_library": plan_data.get("sequence_library", []),
        "coverage_points": plan_data.get("coverage_points", []),
        "generated_bfm_methods": [],
        "generated_sequencers": [],
    }

    # --- 4. [!!] 启动"总调度循环" [!!] ---
    # 任务 0: 发送系统提示
    initial_prompt = f"""
    {UVM_BUILD_SYSTEM_PROMPT}
    --- 蓝图 1: design_spec.final.yml ---
    {spec_text}
    --- 蓝图 2: verif_plan.final.yml ---
    {plan_text}
    你现在拥有了完整的上下文.请确认你已准备好, 等待我的第一个任务.
    """
    execute_conversation_turn(UVM_BUILD_HISTORY, "", initial_prompt)

    # ---
    # 任务 1: Makefile (无依赖文件)
    # ---
    prompt = """
    任务 1: 填充 'Makefile' 的 'COCOTB_TOPLEVEL' 块.
    (根据 'spec.module_name')

    [!!] 响应格式:
    v-pilot:fill:Makefile:COCOTB_TOPLEVEL
    """
    response = _execute_task_with_context("Makefile", [], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 2: seq_item.py (必须在 BFM 之前)
    # ---
    prompt = """
    任务 2: 填充 'seq_item.py' 中的 *所有* 4 个 LLM 块.
    (SEQ_ITEM_FIELDS, SEQ_ITEM_RANDOMIZE, SEQ_ITEM_STR, SEQ_ITEM_EQ)

    [!!] 关键:
    查看 'seq_item.py' 的文件内容, 确保你的代码
    填充在 `class MySeqItem(uvm_sequence_item):` 内部.

    [!!] 响应格式: (所有 4 个 'v-pilot:fill:seq_item.py:[BLOCK_ID]' 块)
    """
    response = _execute_task_with_context("seq_item.py", [], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 3: base_bfm.py (依赖 'seq_item.py')
    # ---
    prompt = """
    任务 3: 填充 'base_bfm.py' 中的 *所有* 4 个 LLM 块.
    (BFM_HANDLES, BFM_RESET_TASK, BFM_DRIVER_TASKS, BFM_MONITOR_TASKS_AND_GETTERS)

    [!!] 关键:
    你 *必须* 查看 'base_bfm.py' (正在编辑) 和 'seq_item.py' (依赖文件).
    你的 BFM 任务 (例如 'drive_input') *必须* 能够处理
    在 'seq_item.py' 中定义的 *所有* 字段 (例如 'item.data_in', 'item.addr').

    [!!] 响应格式:
    1. v-pilot:context:bfm_methods:[...] (您生成的方法列表)
    2. v-pilot:fill:base_bfm.py:[BLOCK_ID] (所有 4 个块)
    """
    response = _execute_task_with_context("base_bfm.py", ["seq_item.py"], prompt)
    ctx = _parse_and_inject(response, code_manager)
    build_context.update(ctx)

    # ---
    # 任务 4: driver.py (依赖 BFM)
    # ---
    prompt = f"""
    任务 4: 填充 'driver.py' 的 'DRIVER_BFM_CALL' 块.

    [!!] v-pilot 上下文 (来自 任务 3):
    - BFM 方法: {build_context.get('bfm_methods', '[]')}

    [!!] 关键:
    查看 'driver.py' 的文件内容, 你的代码将位于 'run_phase'
    的 'while True' 循环内部.
    你 *必须* 从上面的列表中选择 'drive'/'write' 相关的方法来调用.

    [!!] 响应格式: v-pilot:fill:driver.py:DRIVER_BFM_CALL
    """
    response = _execute_task_with_context("driver.py", ["base_bfm.py"], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 5: monitor.py (依赖 BFM, SeqItem)
    # ---
    prompt = f"""
    任务 5: 填充 'monitor.py' 的 'MONITOR_BFM_CALL' 块.

    [!!] v-pilot 上下文 (来自 任务 2):
    - BFM 方法: {build_context.get('bfm_methods', '[]')}

    [!!] v-pilot 规则 (来自框架):
    - 你 *必须* `create` 一个 'MySeqItem' 实例
    - 你 *必须* `write` 到 'self.ap'

    [!!] 响应格式: v-pilot:fill:monitor.py:MONITOR_BFM_CALL
    """
    response = _execute_task_with_context(
        "monitor.py", ["base_bfm.py", "seq_item.py"], prompt
    )
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 6: scoreboard.py (依赖 SeqItem)
    # ---
    prompt = f"""
    任务 6: 填充 'scoreboard.py' 的 3 个 LLM 块.

    [!!] v-pilot 上下文 (来自 spec):
    - 设计描述: {build_context["spec_description"]}

    [!!] 响应格式: (所有 3 个 'v-pilot:fill:scoreboard.py:[BLOCK_ID]' 块)
    """
    response = _execute_task_with_context("scoreboard.py", ["seq_item.py"], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 7: env.py (依赖 Agent, Scoreboard, Coverage)
    # ---
    prompt = f"""
    任务 7: 填充 'env.py' 的 2 个 LLM 块.

    [!!] v-pilot 上下文 (来自 plan):
    - 拓扑: {build_context["uvm_topology"]}

    [!!] v-pilot 规则 (来自框架):
    - Agent 类名: 'MyAgent'
    - Scoreboard 类名: 'Scoreboard'
    - Coverage 类名: 'Coverage'
    - Monitor 端口: 'ap'
    - Scoreboard 端口: 'expected_fifo.analysis_export', 'actual_fifo.analysis_export'
    - Coverage 端口: 'analysis_export'

    [!!] 响应格式:
    1. v-pilot:context:sequencers:[...] (您实例化的 *所有* sequencer 路径)
    2. v-pilot:fill:env.py:ENV_INSTANTIATION
    3. v-pilot:fill:env.py:ENV_CONNECTIONS
    """
    response = _execute_task_with_context(
        "env.py", ["agent.py", "scoreboard.py", "coverage.py"], prompt
    )
    ctx = _parse_and_inject(response, code_manager)
    build_context.update(ctx)

    # ---
    # 任务 8: coverage.py (依赖 SeqItem)
    # ---
    prompt = f"""
    任务 8: 填充 'coverage.py' 的 'COVERAGE_DEFINITIONS' 和 'COVERAGE_SAMPLE_CALL' 块.

    [!!] v-pilot 上下文 (来自 plan):
    - 覆盖点: {build_context["coverage_points"]}

    [!!] 关键规则:
    `@CoverPoint` 装饰器 的参数请你回顾cocotb-coverage的文档, 以及根据示例生成
    不存在 'description' 或 'item_field' 等关键字参数.

    [!!] 响应格式: (所有 2 个 'v-pilot:fill:coverage.py:[BLOCK_ID]' 块)
    """
    response = _execute_task_with_context("coverage.py", ["seq_item.py"], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 9: sequence_lib.py (依赖 SeqItem)
    # ---
    prompt = f"""
    任务 9: 填充 'sequence_lib.py' 的 'SEQUENCES' 块.

    [!!] v-pilot 上下文 (来自 plan):
    - 序列库: {plan_data.get('sequence_library', [])}

    [!!] v-pilot 规则 (来自框架):
    - 你 *必须* 继承 'MyBaseSeq'
    - 你 *必须* 使用 'MySeqItem'
    - 你 *禁止* 访问 'self.dut', 'self.bfm'
    - [例外] 仅在 'plan' 明确要求 'fork/join' 时才可导入 'cocotb'

    [!!] 响应格式: v-pilot:fill:sequence_lib.py:SEQUENCES
    """
    response = _execute_task_with_context("sequence_lib.py", ["seq_item.py"], prompt)
    _parse_and_inject(response, code_manager)

    # ---
    # 任务 10: test_lib.py (依赖 BaseTest, SeqLib, Env)
    # ---
    prompt = f"""
    任务 10: 填充 'test_lib.py' 的 'TESTS' 块.

    [!!] v-pilot 上下文 (来自 plan):
    - 序列库: {plan_data.get('sequence_library', [])}

    [!!] v-pilot 上下文 (来自 任务 7):
    - Sequencers: {build_context.get('sequencers', '[]')}

    [!!] v-pilot 规则 (来自框架):
    - 你 *必须* 继承 'MyBaseTest' (来自 'base_test.py')
    - 你 *必须* 重写 'async def main_phase(self)'
    - 你 *必须* 使用 `seq_lib.` 命名空间
    - 你 *必须* `start` 在一个正确的 Sequencer 路径上

    [!!] 响应格式: v-pilot:fill:test_lib.py:TESTS
    """
    response = _execute_task_with_context(
        "test_lib.py",
        ["base_test.py", "sequence_lib.py", "env.py"],
        prompt,
    )
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
    typer.echo(f"正在提交 'make' 失败日志, 请求 LLM 修复...")

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
    (注意: 'spec.yml' 和 'plan.yml' 也在历史记录的 *最开头*)

    你需要:
    1. 诊断问题 (e.g., "NameError: 'InputAgent' is not defined").
    2. 找出是 *哪一个* 代码块 (e.g., 'env.py' 的 'ENV_INSTANTIATION') 导致的.
    3. 提供 *修正后的完整代码块*.

    [!!] 响应格式:
    请 *只* 使用 'v-pilot:fill:[filename.py]:[BLOCK_ID]' 格式来响应.
    """

    response_fix = execute_conversation_turn(UVM_BUILD_HISTORY, "", prompt_task_fix)
    try:
        code_manager = CodeManager(UVM_TB_DIR)
        _parse_and_inject(response_fix, code_manager)
        typer.secho("✅ 代码已自动修复! 请重新运行 'make'.", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"错误: 自动修复失败: {e}", fg=typer.colors.RED)
        typer.echo("LLM 原始响应:")
        typer.echo(response_fix)
