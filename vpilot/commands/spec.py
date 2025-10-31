import typer
import yaml

from pathlib import Path
from vpilot.core.llm_handler import generate_text

app = typer.Typer(help="管理<设计规范>的生成和迭代")

# 定义工作目录,这是我们约定的"工坊"
VPILOT_RUN_DIR = Path("./vpilot_run")


@app.command("init", help="根据RTL和自然语言描述,初始化一份<设计规范>初稿.")
def init(
    rtl_file: Path = typer.Option(..., "--rtl", "-r", help="RTL源文件路径"),
    desc: str = typer.Option(..., "--desc", "-d", help="设计的核心自然语言描述"),
):
    """
    初始化设计规范流程
    """
    typer.echo(f"🚀 开始初始化<设计规范>...")

    # 1. 检查输入和创建工作目录
    if not rtl_file.exists():
        typer.secho(f"错误: RTL文件 '{rtl_file}' 不存在.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    VPILOT_RUN_DIR.mkdir(exist_ok=True)

    # 2. 读取RTL内容和设计规范模板
    try:
        rtl_code = rtl_file.read_text()
        # 注意: 这里的模板路径需要根据实际安装位置调整,暂时先用相对路径
        template_path = (
            Path(__file__).parent.parent / "templates/spec/design_spec.tpl.yml"
        )
        spec_template = template_path.read_text()
    except Exception as e:
        typer.secho(f"错误:读取文件失败: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 3. 构建Prompt
    prompt = f"""
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
    typer.echo("🧠 正在调用LLM生成规范初稿,请稍候...")
    generated_spec_str = generate_text(prompt)

    if not generated_spec_str:
        typer.secho("生成失败,请检查LLM API的错误信息.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 5. 保存结果
    output_path = VPILOT_RUN_DIR / "design_spec.v1.yml"
    try:
        # 尝试加载以验证YAML格式是否正确
        yaml.safe_load(generated_spec_str)
        output_path.write_text(generated_spec_str, encoding="utf-8")
        typer.secho(f"✅ 成功生成<设计规范>初稿: {output_path}", fg=typer.colors.GREEN)
    except yaml.YAMLError as e:
        typer.secho(f"错误: LLM返回的不是有效的YAML格式. {e}", fg=typer.colors.RED)
        # 可以选择保存错误文件供调试
        error_path = VPILOT_RUN_DIR / "design_spec.v1.error.txt"
        error_path.write_text(generated_spec_str)
        typer.secho(f"原始输出已保存至: {error_path}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
