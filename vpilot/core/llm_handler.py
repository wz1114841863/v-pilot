import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_text(prompt: str, model: str = "gpt-4-turbo") -> str:
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
