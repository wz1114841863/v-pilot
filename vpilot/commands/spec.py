import typer
import yaml
import json
import shutil
import os

from pathlib import Path
from vpilot.core.llm_handler import execute_conversation_turn

app = typer.Typer(help="管理<设计规范>的生成和迭代")

# 定义工作目录,
VPILOT_RUN_DIR = Path("./vpilot_run")
SPEC_HISTORY_FILE = VPILOT_RUN_DIR / "design_spec.history.json"
STATE_FILE = VPILOT_RUN_DIR / ".vpilot.state.json"

# 定义这个"聊天页"的专属系统提示
SPEC_SYSTEM_PROMPT = """
你是一个顶级的RTL设计规范专家.
你的任务是根据用户提供的RTL代码和描述,填充YAML格式的<设计规范>.
你必须只输出纯粹的YAML内容,不要包含任何"```yaml"标记或额外的解释.
在后续的迭代中,你将根据用户的反馈逐步完善这份YAML.
"""


def get_module_name_from_spec(spec_file: Path) -> str:
    """辅助函数:从YAML文件中解析出 'module_name'"""
    try:
        with open(spec_file, "r", encoding="utf-8") as f:
            spec_data = yaml.safe_load(f)
            if "module_name" in spec_data and spec_data["module_name"]:
                return spec_data["module_name"]
            else:
                typer.secho(
                    f"错误: 规范文件 {spec_file} 中未找到 'module_name' 字段.",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"错误: 解析规范文件 {spec_file} 失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("init", help="根据RTL和自然语言描述,初始化一份<设计规范>初稿.")
def init(
    rtl_file: Path = typer.Option(..., "--rtl", "-r", help="RTL源文件路径"),
    desc: str = typer.Option(..., "--desc", "-d", help="设计的核心自然语言描述"),
):
    """
    初始化设计规范流程
    """
    typer.echo(f"(会话: 规范) 开始初始化<设计规范>...")

    # 检查输入和创建工作目录
    if not rtl_file.exists():
        typer.secho(f"错误: RTL文件 '{rtl_file}' 不存在.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    VPILOT_RUN_DIR.mkdir(exist_ok=True)
    if SPEC_HISTORY_FILE.exists():
        typer.secho(
            f"错误: 发现一个未批准的规范会话 ({SPEC_HISTORY_FILE}).",
            fg=typer.colors.RED,
        )
        typer.echo("  > 请使用 'vpilot spec iterate' 继续该会话.")
        typer.echo("  > 或使用 'vpilot spec approve' 批准一个版本.")
        typer.echo("  > 如果您确定要放弃旧会话并强制重启,请手动删除以下文件: ")
        typer.echo(f"    - {SPEC_HISTORY_FILE}")
        typer.echo(f"    - {VPILOT_RUN_DIR / 'design_spec.v*.yml'}")
        raise typer.Exit(code=1)

    if not STATE_FILE.exists():
        state = {
            "current_stage": "spec",
            "spec_approved": False,
            "final_spec_file": None,
            "module_name": None,
            "plan_approved": False,
            "final_plan_file": None,
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    # 读取RTL内容和设计规范模板
    try:
        rtl_code = rtl_file.read_text()
        template_path = (
            Path(__file__).parent.parent / "templates/spec/design_spec.tpl.yml"
        )
        spec_template = template_path.read_text()
    except Exception as e:
        typer.secho(f"错误:读取文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 3. 构建Prompt
    user_prompt = f"""
    请基于以下RTL代码和设计描述,填充所提供的YAML模板.
    只输出填充后的YAML内容,不要包含任何额外的解释或代码块标记.

    --- 设计描述 ---
    {desc}

    --- RTL代码 (`{rtl_file.name}`) ---
    ```verilog
    {rtl_code}
    ```

    --- YAML模板 ---
    {spec_template}
    """

    # 4. 调用LLM
    typer.echo("正在调用LLM生成规范初稿(V1), 请稍候...")
    generated_spec_str = execute_conversation_turn(
        history_file=SPEC_HISTORY_FILE,
        system_prompt=SPEC_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    if not generated_spec_str:
        typer.secho("生成失败,请检查LLM API的错误信息.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 5. 保存结果
    output_path = VPILOT_RUN_DIR / "design_spec.v1.yml"
    try:
        # 尝试加载以验证YAML格式是否正确
        yaml.safe_load(generated_spec_str)
        output_path.write_text(generated_spec_str, encoding="utf-8")
        typer.secho(f"成功生成<设计规范>初稿: {output_path}", fg=typer.colors.GREEN)
        typer.secho(f"会话历史已保存至: {SPEC_HISTORY_FILE}", fg=typer.colors.CYAN)
    except yaml.YAMLError as e:
        typer.secho(f"错误: LLM返回的不是有效的YAML格式. {e}", fg=typer.colors.RED)
        # 可以选择保存错误文件供调试
        error_path = VPILOT_RUN_DIR / "design_spec.v1.error.txt"
        error_path.write_text(generated_spec_str)
        typer.secho(f"原始输出已保存至: {error_path}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@app.command("iterate", help="根据反馈描述或文件,对<设计规范>进行迭代.")
def iterate(
    feedback_file: Path = typer.Option(
        None,
        "--feedback",
        "-f",
        help="包含工程师反馈的纯文本文件路径.",
    ),
    feedback_message: str = typer.Option(
        None,
        "--message",
        "-m",
        help="直接从命令行传入的反馈字符串.",
    ),
    version: int = typer.Option(
        ...,  # 强制要求用户输入版本号,防止覆盖
        "--version",
        "-v",
        help="要生成的新版本号 (例如: 2)",
    ),
):
    """
    读取反馈,将其作为新的user_prompt,继续对话.
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

    if not SPEC_HISTORY_FILE.exists():
        typer.secho("错误: 找不到对话历史,请先运行 'init' 命令.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"🚀 (会话: 规范) 正在根据反馈生成 V{version}...")

    # 构建 *新一轮* 的User Prompt
    user_prompt = f"""
    这是我对上一版本的反馈,请仔细阅读并生成V{version}版本的YAML规范.

    --- 反馈 ---
    {feedback_text}
    ---

    请只输出更新后的完整YAML内容.
    """

    # 3. 调用 *完全相同* 的对话处理器
    typer.echo("🧠 正在调用LLM进行迭代...")
    generated_spec_str = execute_conversation_turn(
        history_file=SPEC_HISTORY_FILE,
        system_prompt=SPEC_SYSTEM_PROMPT,  # 处理器会自动忽略这个,因为历史文件已存在
        user_prompt=user_prompt,
    )

    if not generated_spec_str:
        typer.secho("迭代失败.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    output_path = VPILOT_RUN_DIR / f"design_spec.v{version}.yml"
    try:
        # 尝试加载以验证YAML格式是否正确
        yaml.safe_load(generated_spec_str)
        output_path.write_text(generated_spec_str, encoding="utf-8")
        typer.secho(f"成功生成<设计规范>初稿: {output_path}", fg=typer.colors.GREEN)
        typer.secho(f"会话历史已保存至: {SPEC_HISTORY_FILE}", fg=typer.colors.CYAN)
    except yaml.YAMLError as e:
        typer.secho(f"错误: LLM返回的不是有效的YAML格式. {e}", fg=typer.colors.RED)
        # 可以选择保存错误文件供调试
        error_path = VPILOT_RUN_DIR / "design_spec.v1.error.txt"
        error_path.write_text(generated_spec_str)
        typer.secho(f"原始输出已保存至: {error_path}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)


@app.command("approve", help="批准一个<设计规范>版本,将其归档并解锁下一阶段.")
def approve(
    version: int = typer.Option(
        ..., "--version", "-v", help="您要批准的规范版本号 (例如: 3)"
    )
):
    """
    1. 验证版本文件存在.
    2. 从该文件中解析出 module_name.
    3. 重命名该文件和历史文件.
    4. 更新状态文件.
    """
    typer.echo(f"🚀 正在批准<设计规范> V{version} ...")

    # 1. 找到要批准的文件
    spec_file_to_approve = VPILOT_RUN_DIR / f"design_spec.v{version}.yml"
    if not spec_file_to_approve.exists():
        typer.secho(
            f"错误: 找不到版本 {version} ({spec_file_to_approve})", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    if not SPEC_HISTORY_FILE.exists():
        typer.secho(
            f"错误: 找不到对应的会话历史文件 ({SPEC_HISTORY_FILE})", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    # 2. 获取模块名
    module_name = get_module_name_from_spec(spec_file_to_approve)
    typer.echo(f"  > 识别到模块名: {module_name}")

    # 3. 定义归档路径
    archive_spec_file = VPILOT_RUN_DIR / f"{module_name}.design_spec.final.yml"
    archive_history_file = VPILOT_RUN_DIR / f"{module_name}.design_spec.history.json"

    # 4. 执行归档 (重命名)
    try:
        shutil.move(str(spec_file_to_approve), str(archive_spec_file))
        shutil.move(str(SPEC_HISTORY_FILE), str(archive_history_file))
        typer.echo(f"  > 归档规范: {archive_spec_file}")
        typer.echo(f"  > 归档日志: {archive_history_file}")
    except Exception as e:
        typer.secho(f"错误: 归档文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 5. (可选) 清理其他未被批准的版本
    for f in VPILOT_RUN_DIR.glob("design_spec.v*.yml"):
        os.remove(f)

    # 6. 更新状态文件 (解锁下一阶段)
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

        state["current_stage"] = "plan"
        state["spec_approved"] = True
        state["final_spec_file"] = str(archive_spec_file)
        state["module_name"] = module_name

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        typer.secho(f"警告: 归档已完成,但更新状态文件失败: {e}", fg=typer.colors.YELLOW)

    typer.secho(f"✅ <设计规范>已批准并成功归档!", fg=typer.colors.GREEN)
    typer.echo("  > 您现在可以运行 'vpilot plan init' 来生成验证计划了.")
