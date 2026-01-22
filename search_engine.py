"""
Everything 搜索引擎封装
仅支持精确匹配
"""
import subprocess
import os
from typing import List, Optional

def find_es_exe() -> Optional[str]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_es = os.path.join(current_dir, "es.exe")
    if os.path.exists(local_es):
        return local_es
    possible_paths = [
        r"C:\Program Files\Everything\es.exe",
        r"C:\Program Files (x86)\Everything\es.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def search_images(
    keywords: List[str],
    source_path: str,
    extensions: List[str],
    exact_match: bool = True  # 保留参数但始终精确匹配
) -> List[str]:
    es_exe = find_es_exe()
    if not es_exe or not keywords or not source_path:
        return []

    source_path = os.path.normpath(source_path)
    results = []
    
    valid_exts = set(ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions)

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
            
        try:
            cmd = [es_exe, "-path", source_path, keyword]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    file_path = line.strip()
                    if not file_path:
                        continue
                    
                    # 扩展名过滤
                    _, ext = os.path.splitext(file_path)
                    if ext.lower() not in valid_exts:
                        continue
                    
                    # 精确匹配：文件名必须完全一致
                    filename = os.path.basename(file_path)
                    name_no_ext = os.path.splitext(filename)[0]
                    if name_no_ext.lower() != keyword.lower():
                        continue
                    
                    if file_path not in results:
                        results.append(file_path)
                        
        except Exception:
            pass
            
    return sorted(results)

def parse_keywords(text: str) -> List[str]:
    text = text.replace(",", " ")
    return [w.strip() for w in text.split() if w.strip()]
