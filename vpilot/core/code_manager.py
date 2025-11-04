import re
import typer
from pathlib import Path


class CodeManager:

    def __init__(self, uvm_tb_path):
        self.uvm_tb_path = uvm_tb_path
        if not self.uvm_tb_path.is_dir():
            typer.secho(
                f"CodeManager Error: 找不到工作目录: {uvm_tb_path}", fg=typer.colors.RED
            )
            raise FileNotFoundError(f"指定的 uvm_tb 路径不存在: {uvm_tb_path}")

    def _get_file_path(self, relative_file):
        return (self.uvm_tb_path / relative_file).resolve()

    def _get_block_pattern(self, block_id):
        """
        它匹配 (START 标签) + (内容) + (END 标签前的空白) + (END 标签)
        不关心 START 标签行的缩进.
        """
        start_marker = f"# LLM_GENERATED_START: {re.escape(block_id)}"
        end_marker = f"# LLM_GENERATED_END: {re.escape(block_id)}"

        # (组 1: START 标签)
        # (组 2: 内容)
        # (组 3: END 标签前的空白)
        # (组 4: END 标签)
        pattern = re.compile(
            f"({re.escape(start_marker)})(.*?)(\\s*)({re.escape(end_marker)})",
            re.DOTALL,
        )
        return pattern

    def _sanitize_llm_code(self, raw_response):
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

        # 移除 LLM 倾向于添加的多余空行
        code = re.sub(r"(\n\s*){2,}", "\n", code)

        return code

    def update_block(self, relative_file, block_id, new_code):
        """
        假设 LLM 返回的代码 *已包含* 正确的缩进.
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
                    f"在文件 {relative_file} 中 (V7 Regex)",
                    fg=typer.colors.RED,
                )
                return False

            # 1. 清理 LLM 的代码 (移除 Markdown 和多余空行)
            clean_code = self._sanitize_llm_code(new_code)

            # 3. 构建替换:
            # (组 1: START 标签)
            # (组 3: END 标签前的空白)
            # (组 4: END 标签)
            #
            # [!!] 关键:
            # clean_code (LLM 的响应) *必须*
            # 1. 以 '\n' + '缩进' 开头
            # 2. 以 '缩进' + '\n' 结尾
            #
            # 让我们强制执行这一点:

            # (从 'match.group(3)' 中提取 END 标签的缩进)
            end_ws_match = re.search(r"(\s*)$", match.group(3))
            indent_str = end_ws_match.group(1) if end_ws_match else ""

            # 确保代码以换行+缩进开头 (如果它还不是的话)
            if not clean_code.startswith("\n"):
                clean_code = f"\n{indent_str}{clean_code}"

            # 确保代码以换行+缩进结尾
            if not clean_code.endswith(f"\n{indent_str}"):
                clean_code = f"{clean_code}\n{indent_str}"

            replacement = f"\\1{clean_code}\\4"
            new_content = pattern.sub(replacement, original_content, count=1)
            file_path.write_text(new_content, encoding="utf-8")

            typer.secho(
                f"  > [CodeManager] 已更新 '{block_id}' " f"在 {relative_file}",
                fg=typer.colors.CYAN,
            )
            return True

        except Exception as e:
            # ... (错误处理)
            return False

    def read_block(self, relative_file, block_id):
        file_path = self._get_file_path(relative_file)

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            pattern = self._get_block_pattern(block_id)
            match = pattern.search(content)
            if match:
                return match.group(3).strip()
            else:
                typer.secho(
                    f"CodeManager Error: 找不到标记 '{block_id}' "
                    f"在文件 {relative_file} 中 ",
                    fg=typer.colors.RED,
                )
                return None

        except Exception as e:
            typer.secho(
                f"CodeManager Error: 读取文件 {file_path} 失败: {e}",
                fg=typer.colors.RED,
            )
            return None
