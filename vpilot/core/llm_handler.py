import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.deepseek.com"
)


def generate_text(prompt, model=os.getenv("CHAT_MODEL")):
    """
    发送一个Prompt给LLM并返回生成的文本.

    Args:
        prompt: 发送给LLM的完整提示.
        model: 使用的LLM模型.

    Returns:
        LLM生成的文本响应.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional RTL verification assistant. Your responses must be precise and follow the user's format instructions.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR: 调用LLM API失败: {e}")
        return ""


def execute_conversation_turn(
    history_file, system_prompt, user_prompt, model=os.getenv("CHAT_MODEL")
):
    """
    执行一个有状态的对话回合.
    加载对话历史, 追加新消息, 调用API, 并保存完整历史.
    """
    messages = []

    if history_file.exists():
        with open(history_file, "r", encoding="utf-8") as f:
            messages = json.load(f)
    else:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_prompt})

    try:
        response = client.chat.completions.create(model=model, messages=messages)
        assistant_response = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": assistant_response})
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        return assistant_response

    except Exception as e:
        print(f"ERROR: 调用LLM API失败: {e}")
        return None
