import re
from pathlib import Path
import typer
import textwrap


class CodeManager:

    def __init__(self, uvm_tb_path: Path):
        self.uvm_tb_path = uvm_tb_path
        if not self.uvm_tb_path.is_dir():
            typer.secho(
                f"CodeManager Error: 找不到工作目录: {uvm_tb_path}", fg=typer.colors.RED
            )
            raise FileNotFoundError(f"指定的 uvm_tb 路径不存在: {uvm_tb_path}")

    def _get_file_path(self, relative_file: str) -> Path:
        return (self.uvm_tb_path / relative_file).resolve()

    def _get_block_pattern(self, block_id: str) -> re.Pattern:
        """
        使用一个更健壮的/非锚定 (^) 的正则表达式
        来捕获 START 和 END 标签行的缩进.
        """
        # 1. 定义 START/END 标签 (不变)
        start_marker = f"# LLM_GENERATED_START: {re.escape(block_id)}"
        end_marker = f"# LLM_GENERATED_END: {re.escape(block_id)}"

        # [!!] 关键修复:
        # 我们匹配 (START 标签行) + (内容) + (END 标签行)

        # (组 1: (\s*)) - 捕获 START 标签 *行* 的缩进
        # (组 2: ({start_marker})) - 捕获 START 标签 (不含 #)
        start_line_re = r"(\s*)(" + re.escape(start_marker) + r")"

        # (组 4: (\s*)) - 捕获 END 标签 *行* 的缩进
        # (组 5: ({end_marker})) - 捕获 END 标签 (不含 #)
        end_line_re = r"(\s*)(" + re.escape(end_marker) + r")"

        # 3. 组合: (Start Line)(Content)(End Line)
        #    re.DOTALL 使得 (.*?) (组 3) 可以匹配换行符
        pattern = re.compile(
            f"{start_line_re}"  # (Group 1: Indent_Start), (Group 2: Tag_Start)
            r"(.*?)"  # (Group 3: Content)
            f"{end_line_re}",  # (Group 4: Indent_End), (Group 5: Tag_End)
            re.DOTALL,
        )
        return pattern

    def _sanitize_llm_code(self, raw_response: str) -> str:
        """
        清理 LLM 的原始响应.
        """
        code = raw_response

        # 1. 尝试去除 Markdown 代码块 (```python ... ```)
        match = re.search(r"```(?:python)?\s*\n(.*?)\n```", code, re.DOTALL)
        if match:
            code = match.group(1)

        # 2. 去除 'v-pilot:fill:[...]' 头部
        code = re.sub(r"^v-pilot:fill:.*?\n", "", code, flags=re.MULTILINE)

        code = re.sub(r"(\n\s*){2,}", "\n", code)

        return code  # (V5 已修复: 不使用 .strip())

    def update_block(self, relative_file: str, block_id: str, new_code: str) -> bool:
        """
        [!!] V5 修复:
        替换逻辑现在 *必须* 使用 V5 正则表达式捕获的组
        """
        file_path = self._get_file_path(relative_file)

        if not file_path.exists():
            # ... (错误处理)
            return False

        try:
            original_content = file_path.read_text(encoding="utf-8")
            pattern = self._get_block_pattern(block_id)

            match = pattern.search(original_content)

            if not match:
                typer.secho(
                    f"CodeManager Error: 找不到标记 '{block_id}' "
                    f"在文件 {relative_file} 中 (V5 Regex)",
                    fg=typer.colors.RED,
                )
                return False

            # [!!] 关键修复:
            # 1. 捕获 START 标签的缩进 (来自组 1)
            indent_str = match.group(1)

            # 2. 捕获 START 标签 (来自组 2)
            start_tag = match.group(2)

            # 3. 捕获 END 标签的缩进 (来自组 4)
            end_ws = match.group(4)

            # 4. 捕获 END 标签 (来自组 5)
            end_tag = match.group(5)

            # 5. 清理 LLM 的代码 (不变)
            clean_code = self._sanitize_llm_code(new_code)

            # 6. [!!] 将捕获的缩进 'indent_str' 应用到
            #    'clean_code' 的 *每一行*
            indented_code = textwrap.indent(clean_code, indent_str)

            # 7. 构建新的替换字符串
            #    [!!] 关键:
            #    Start 标签 *后* 的换行符是 '\n'
            #    Content *后* 的换行符 *已经包含* 在 'end_ws' 中
            #    (因为 (.*?) (组 3) 匹配到它, 且 (\s*) (组 4) 会匹配 END 标签前的换行和缩进)
            replacement = f"{indent_str}{start_tag}\n{indented_code}\n{end_ws}{end_tag}"

            # 8. 执行替换
            #    [!!] 关键: 我们必须替换 'match.group(0)' (整个匹配)
            new_content = original_content.replace(match.group(0), replacement)

            file_path.write_text(new_content, encoding="utf-8")

            typer.secho(
                f"  > [CodeManager] 已更新 '{block_id}' " f"在 {relative_file}",
                fg=typer.colors.CYAN,
            )
            return True

        except Exception as e:
            typer.secho(
                f"CodeManager Error: 写入文件 {file_path} 失败: {e}",
                fg=typer.colors.RED,
            )
            return False

    def read_block(self, relative_file: str, block_id: str) -> str | None:
        """
        (读取也需要 V5 修复, 以确保它能 *找到* 块)
        """
        file_path = self._get_file_path(relative_file)

        if not file_path.exists():
            # ... (错误处理)
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            pattern = self._get_block_pattern(block_id)  # (使用 V5 正则)

            match = pattern.search(content)

            if match:
                # 返回组 3 (内容), 并去除首尾空白
                return match.group(3).strip()
            else:
                typer.secho(
                    f"CodeManager Error: 找不到标记 '{block_id}' "
                    f"在文件 {relative_file} 中 (V5 Read)",
                    fg=typer.colors.RED,
                )
                return None

        except Exception as e:
            typer.secho(
                f"CodeManager Error: 读取文件 {file_path} 失败: {e}",
                fg=typer.colors.RED,
            )
            return None
