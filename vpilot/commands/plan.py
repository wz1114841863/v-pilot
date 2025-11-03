# vpilot/commands/plan.py

import typer
from pathlib import Path
import json
import yaml
import shutil
import os
from vpilot.core.llm_handler import execute_conversation_turn

app = typer.Typer(help="管理<验证计划>的生成和迭代")

# --- 模块常量定义 ---

# 目录和状态文件
VPILOT_RUN_DIR = Path("./vpilot_run")
STATE_FILE = VPILOT_RUN_DIR / ".vpilot.state.json"

# 'plan' 阶段专属的会话历史文件
PLAN_HISTORY_FILE = VPILOT_RUN_DIR / "verif_plan.history.json"

# 'plan' 阶段专属的系统提示 (System Prompt)
PLAN_SYSTEM_PROMPT = """
你是一个顶级的UVM验证策略专家和验证工程师.
你的任务是根据用户提供的<设计规范>,填充YAML格式的<验证计划>.
你需要思考周全,为'verification_points'中的每一个功能点,设计具体的'test_scenarios'和'corner_cases'.
同时,你需要初步定义实现这些测试所需的UVM组件 (agents, sequences) 和关键的'coverage_points'.
你必须只输出纯粹的YAML内容,不要包含任何"```yaml"标记或额外的解释.
在后续的迭代中,你将根据用户的反馈逐步完善这份YAML.
"""

# 'plan' 阶段专属的模板文件路径
PLAN_TEMPLATE_PATH = Path(__file__).parent.parent / "templates/plan/verif_plan.tpl.yml"


def load_state():
    """加载并返回中央状态文件内容"""
    if not STATE_FILE.exists():
        typer.secho(
            "错误: 找不到项目状态文件.请先运行 'vpilot spec init'.", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        typer.secho(f"错误: 读取状态文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def write_state(state_data: dict):
    """将更新后的状态写回文件"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        typer.secho(f"警告: 归档已完成,但更新状态文件失败: {e}", fg=typer.colors.YELLOW)


@app.command("init", help="基于已批准的<设计规范>,生成<验证计划>初稿.")
def init():
    """
    1. 检查 'spec' 阶段是否已批准 (门控).
    2. 检查 'plan' 会话是否已存在 (安全).
    3. 加载已批准的规范和计划模板.
    4. 构建Prompt,调用LLM生成 V1.
    5. 保存 V1 和会话历史.
    """
    typer.echo("🚀 (会话: 计划) 正在初始化<验证计划>...")

    # --- 1. 门控检查 ---
    state = load_state()
    if not state.get("spec_approved"):
        typer.secho("错误: <设计规范>尚未批准.", fg=typer.colors.RED)
        typer.echo("  > 请先运行 'vpilot spec approve --version <v>' 批准一个版本.")
        raise typer.Exit(code=1)

    final_spec_file_path = state.get("final_spec_file")
    if not final_spec_file_path:
        typer.secho("错误: 状态文件中未指明 'final_spec_file'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    final_spec_file = Path(final_spec_file_path)
    if not final_spec_file.exists():
        typer.secho(
            f"错误: 找不到已批准的规范文件: {final_spec_file}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    typer.echo(f"  > 正在使用已批准的规范: {final_spec_file.name}")

    # --- 2. 安全检查 ---
    if PLAN_HISTORY_FILE.exists():
        typer.secho(
            f"错误: 发现一个未批准的计划会话 ({PLAN_HISTORY_FILE}).",
            fg=typer.colors.RED,
        )
        typer.echo("  > 请使用 'vpilot plan iterate' 继续该会话.")
        typer.echo("  > 或使用 'vpilot plan approve' 批准一个版本.")
        typer.echo(
            f"  > 如需强制重启,请手动删除: {PLAN_HISTORY_FILE} 和 verif_plan.v*.yml"
        )
        raise typer.Exit(code=1)

    # --- 3. 加载输入文件 ---
    try:
        spec_content = final_spec_file.read_text(encoding="utf-8")
        if not PLAN_TEMPLATE_PATH.exists():
            typer.secho(
                f"错误: 找不到计划模板文件: {PLAN_TEMPLATE_PATH}", fg=typer.colors.RED
            )
            raise typer.Exit(code=1)
        plan_template = PLAN_TEMPLATE_PATH.read_text(encoding="utf-8")
    except Exception as e:
        typer.secho(f"错误: 读取文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- 4. 构建Prompt并调用LLM ---
    user_prompt = f"""
    请基于以下已批准的<设计规范>,为我生成<验证计划>V1版本.
    请严格按照所提供的YAML模板进行填充.

    --- 已批准的<设计规范> ({final_spec_file.name}) ---
    {spec_content}

    --- <验证计划>YAML模板 ---
    {plan_template}
    """

    typer.echo("🧠 正在调用LLM生成计划初稿 (V1)...")
    generated_plan_str = execute_conversation_turn(
        history_file=PLAN_HISTORY_FILE,
        system_prompt=PLAN_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    if not generated_plan_str:
        typer.secho("生成失败.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- 5. 保存 V1 ---
    output_path = VPILOT_RUN_DIR / "verif_plan.v1.yml"
    try:
        yaml.safe_load(generated_plan_str)  # 校验YAML格式
        output_path.write_text(generated_plan_str, encoding="utf-8")
        typer.secho(f"✅ 成功生成<验证计划>初稿: {output_path}", fg=typer.colors.GREEN)
        typer.secho(f"📝 会话历史已保存至: {PLAN_HISTORY_FILE}", fg=typer.colors.CYAN)
    except yaml.YAMLError as e:
        typer.secho(f"错误: LLM返回的不是有效的YAML格式. {e}", fg=typer.colors.RED)
        error_path = VPILOT_RUN_DIR / "verif_plan.v1.error.txt"
        error_path.write_text(generated_plan_str)
        typer.secho(f"原始输出已保存至: {error_path}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@app.command("iterate", help="根据反馈文件,对<验证计划>进行迭代.")
def iterate(
    feedback_file: Path = typer.Option(
        None,
        "--feedback",
        "-f",
        help="包含工程师反馈的纯文本文件",
    ),
    feedback_message: str = typer.Option(
        None,
        "--message",
        "-m",
        help="直接从命令行传入的反馈字符串.",
    ),
    version: int = typer.Option(2, "--version", "-v", help="要生成的新版本号"),
):
    """
    1. 检查会话历史是否存在.
    2. 加载反馈,构建Prompt.
    3. 调用LLM继续对话.
    4. 保存 V(n) 版本.
    """
    feedback_text = ""
    if feedback_message:
        typer.echo("  > 正在使用来自命令行 '--message' 的反馈字符串...")
        feedback_text = feedback_message
    elif feedback_file:
        typer.echo(f"  > 正在使用来自文件 '--feedback' 的反馈: {feedback_file}")
        if not feedback_file.exists():
            typer.secho(
                f"错误: 反馈文件 '{feedback_file}' 不存在.", fg=typer.colors.RED
            )
            raise typer.Exit(code=1)
        try:
            feedback_text = feedback_file.read_text(encoding="utf-8")
        except Exception as e:
            typer.secho(f"错误: 读取反馈文件失败: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    else:
        typer.secho("错误: 必须提供反馈.", fg=typer.colors.RED)
        typer.echo("  > 请使用 '--message \"您的反馈\"'")
        typer.echo("  > 或使用 '--feedback <文件路径>'.")
        raise typer.Exit(code=1)

    # 构建新一轮的User Prompt
    user_prompt = f"""
    这是我对上一版本的反馈,请仔细阅读并生成V{version}版本的YAML验证计划.

    --- 反馈 ---
    {feedback_text}
    ---

    请只输出更新后的完整YAML内容.
    """

    typer.echo("🧠 正在调用LLM进行迭代...")
    generated_plan_str = execute_conversation_turn(
        history_file=PLAN_HISTORY_FILE,
        system_prompt=PLAN_SYSTEM_PROMPT,  # 处理器会自动忽略
        user_prompt=user_prompt,
    )

    if not generated_plan_str:
        typer.secho("迭代失败.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 保存新版本
    output_path = VPILOT_RUN_DIR / f"verif_plan.v{version}.yml"
    try:
        yaml.safe_load(generated_plan_str)  # 校验YAML
        output_path.write_text(generated_plan_str, encoding="utf-8")
        typer.secho(
            f"✅ 成功生成<验证计划>V{version}: {output_path}", fg=typer.colors.GREEN
        )
    except yaml.YAMLError as e:
        typer.secho(f"错误: LLM返回的不是有效的YAML格式. {e}", fg=typer.colors.RED)
        error_path = VPILOT_RUN_DIR / f"verif_plan.v{version}.error.txt"
        error_path.write_text(generated_plan_str)
        typer.secho(f"原始输出已保存至: {error_path}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@app.command("approve", help="批准一个<验证计划>版本,将其归档并解锁UVM生成.")
def approve(
    version: int = typer.Option(
        ..., "--version", "-v", help="您要批准的计划版本号 (例如: 2)"
    )
):
    """
    1. 加载状态,获取 module_name.
    2. 检查 V(n) 和历史文件是否存在.
    3. 重命名文件,进行归档.
    4. 清理临时的 V(n) 文件.
    5. 更新状态文件,解锁 'uvm_gen' 阶段.
    """
    typer.echo(f"🚀 正在批准<验证计划> V{version} ...")

    # --- 1. 加载状态,获取 module_name ---
    state = load_state()
    module_name = state.get("module_name")
    if not module_name:
        typer.secho(
            "错误: 状态文件中未找到 'module_name'.批准失败.", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)
    typer.echo(f"  > 归档模块: {module_name}")

    # --- 2. 检查待批准文件 ---
    plan_file_to_approve = VPILOT_RUN_DIR / f"verif_plan.v{version}.yml"
    if not plan_file_to_approve.exists():
        typer.secho(
            f"错误: 找不到版本 {version} ({plan_file_to_approve})", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    if not PLAN_HISTORY_FILE.exists():
        typer.secho(
            f"错误: 找不到对应的会话历史文件 ({PLAN_HISTORY_FILE})", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    # --- 3. 执行归档 (重命名) ---
    archive_plan_file = VPILOT_RUN_DIR / f"{module_name}.verif_plan.final.yml"
    archive_history_file = VPILOT_RUN_DIR / f"{module_name}.verif_plan.history.json"

    try:
        shutil.move(str(plan_file_to_approve), str(archive_plan_file))
        shutil.move(str(PLAN_HISTORY_FILE), str(archive_history_file))
        typer.echo(f"  > 归档计划: {archive_plan_file}")
        typer.echo(f"  > 归档日志: {archive_history_file}")
    except Exception as e:
        typer.secho(f"错误: 归档文件失败: {e}", fg=typer.colors.RED)
        # 严重错误,退出前尝试恢复状态
        if not PLAN_HISTORY_FILE.exists() and archive_history_file.exists():
            shutil.move(str(archive_history_file), str(PLAN_HISTORY_FILE))
        if not plan_file_to_approve.exists() and archive_plan_file.exists():
            shutil.move(str(archive_plan_file), str(plan_file_to_approve))
        typer.secho("  > 已尝试回滚操作.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    # --- 4. 清理临时文件 ---
    for f in VPILOT_RUN_DIR.glob("verif_plan.v*.yml"):
        os.remove(f)

    # --- 5. 更新状态文件 (解锁UVM Gen) ---
    state["current_stage"] = "uvm_build"
    state["plan_approved"] = True
    state["final_plan_file"] = str(archive_plan_file)
    write_state(state)

    typer.secho(f"✅ <验证计划>已批准并成功归档!", fg=typer.colors.GREEN)
    typer.echo("  > 准备就绪!您现在可以运行 'vpilot uvm build' 来生成代码了.")
