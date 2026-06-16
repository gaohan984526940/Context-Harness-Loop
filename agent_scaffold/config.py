"""全局配置：从环境变量 / .env 读取，统一在这里收口。

只做一件事——把外部配置加载成一个不可变的 Config 对象。
任何一层需要配置都从这里拿，不在别处散落读 os.environ。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 显式加载本包目录下的 .env（而非当前工作目录），保证从任意位置以 -m 启动都能找到。
# 幂等，重复调用无副作用。
load_dotenv(Path(__file__).resolve().parent / ".env")


@dataclass(frozen=True)
class Config:
    """运行所需的全部外部配置。frozen=True 保证不可变。"""

    api_key: str
    base_url: str
    model: str
    max_steps: int          # Loop 层：单个任务最多迭代多少步，防死循环
    temperature: float
    request_timeout: float   # 单次 LLM 请求超时（秒）

    @staticmethod
    def load() -> "Config":
        """从环境变量装配 Config，并在边界处做校验（fail fast）。"""
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "未配置 DEEPSEEK_API_KEY。请复制 .env.example 为 .env 并填入你的 key。"
            )

        return Config(
            api_key=api_key,
            # DeepSeek 是 OpenAI 兼容接口，默认指向官方地址。
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip(),
            # deepseek-chat 支持 function calling；deepseek-reasoner(R1) 不支持工具调用。
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip(),
            max_steps=int(os.environ.get("AGENT_MAX_STEPS", "10")),
            temperature=float(os.environ.get("AGENT_TEMPERATURE", "0.7")),
            request_timeout=float(os.environ.get("AGENT_TIMEOUT", "60")),
        )
