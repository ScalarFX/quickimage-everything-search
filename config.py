"""
配置管理模块
负责读取和保存用户配置（源路径、输出路径等）
"""
import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".image_search_config.json"

DEFAULT_CONFIG = {
    "source_path": "",
    "output_path": "",
    "language": "zh",
    "exact_match": True,
    "window_geometry": "",
    "image_extensions": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"]
}


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置，确保新增字段也存在
                return {**DEFAULT_CONFIG, **config}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")
