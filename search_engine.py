"""
Everything 搜索引擎封装
仅支持精确匹配
"""
import ctypes
import os
import subprocess
from typing import List, Optional


EVERYTHING_REQUEST_FULL_PATH_AND_FILE_NAME = 0x00000004
SDK_RESULT_PATH_MAX = 32768
DEFAULT_MAX_RESULTS = 5000
QUERY_KEYWORD_CHUNK_SIZE = 24

_sdk_handle = None
_sdk_probed = False
_last_backend = "none"


def get_last_backend() -> str:
    return _last_backend


def get_backend_label() -> str:
    if _last_backend == "sdk":
        return "SDK"
    if _last_backend == "es":
        return "es.exe"
    return "未就绪"


def _normalize_keywords(keywords: List[str]) -> List[str]:
    seen = set()
    normalized = []
    for keyword in keywords:
        item = keyword.strip().lower()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _iter_keyword_chunks(keywords: List[str], chunk_size: int):
    size = max(1, int(chunk_size))
    for i in range(0, len(keywords), size):
        yield keywords[i:i + size]


def _append_paths_limited(paths: List[str], merged: List[str], seen: set, max_results: int) -> bool:
    for file_path in paths:
        normalized_path = os.path.normpath(file_path)
        if normalized_path in seen:
            continue
        seen.add(normalized_path)
        merged.append(normalized_path)
        if len(merged) >= max_results:
            return True
    return False


def _is_64bit_python() -> bool:
    return ctypes.sizeof(ctypes.c_void_p) == 8


def find_everything_dll() -> Optional[str]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dll_name = "Everything64.dll" if _is_64bit_python() else "Everything32.dll"

    possible_paths = [
        os.path.join(current_dir, dll_name),
        os.path.join(current_dir, "dll", dll_name),
        os.path.join(current_dir, "Everything-SDK", "dll", dll_name),
        os.path.join(current_dir, "Everything-SDK", dll_name),
        os.path.join(r"C:\Program Files\Everything", dll_name),
        os.path.join(r"C:\Program Files (x86)\Everything", dll_name),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def _bind_sdk_functions(sdk) -> None:
    sdk.Everything_Reset.argtypes = []
    sdk.Everything_Reset.restype = None

    sdk.Everything_SetSearchW.argtypes = [ctypes.c_wchar_p]
    sdk.Everything_SetSearchW.restype = None

    sdk.Everything_SetRequestFlags.argtypes = [ctypes.c_uint]
    sdk.Everything_SetRequestFlags.restype = None

    sdk.Everything_SetRegex.argtypes = [ctypes.c_bool]
    sdk.Everything_SetRegex.restype = None

    sdk.Everything_SetMatchPath.argtypes = [ctypes.c_bool]
    sdk.Everything_SetMatchPath.restype = None

    sdk.Everything_SetMatchCase.argtypes = [ctypes.c_bool]
    sdk.Everything_SetMatchCase.restype = None

    sdk.Everything_SetMatchWholeWord.argtypes = [ctypes.c_bool]
    sdk.Everything_SetMatchWholeWord.restype = None

    sdk.Everything_QueryW.argtypes = [ctypes.c_bool]
    sdk.Everything_QueryW.restype = ctypes.c_bool

    if hasattr(sdk, "Everything_SetMax"):
        sdk.Everything_SetMax.argtypes = [ctypes.c_uint]
        sdk.Everything_SetMax.restype = None

    sdk.Everything_GetNumResults.argtypes = []
    sdk.Everything_GetNumResults.restype = ctypes.c_uint

    sdk.Everything_GetLastError.argtypes = []
    sdk.Everything_GetLastError.restype = ctypes.c_uint

    sdk.Everything_GetResultFullPathNameW.argtypes = [ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint]
    sdk.Everything_GetResultFullPathNameW.restype = ctypes.c_uint


def _load_everything_sdk():
    global _sdk_handle, _sdk_probed

    if _sdk_probed:
        return _sdk_handle

    _sdk_probed = True
    dll_path = find_everything_dll()
    if not dll_path:
        return None

    try:
        sdk = ctypes.WinDLL(dll_path)
        _bind_sdk_functions(sdk)
        _sdk_handle = sdk
    except Exception:
        _sdk_handle = None

    return _sdk_handle


def _run_sdk_query(sdk, source_path: str, query: str, max_results: int) -> Optional[List[str]]:
    try:
        safe_source_path = source_path.replace('"', " ")
        search_text = f'path:"{safe_source_path}" {query}'.strip()

        sdk.Everything_Reset()
        sdk.Everything_SetRequestFlags(EVERYTHING_REQUEST_FULL_PATH_AND_FILE_NAME)
        sdk.Everything_SetRegex(False)
        sdk.Everything_SetMatchPath(False)
        sdk.Everything_SetMatchCase(False)
        sdk.Everything_SetMatchWholeWord(False)
        if hasattr(sdk, "Everything_SetMax"):
            sdk.Everything_SetMax(max(1, int(max_results)))
        sdk.Everything_SetSearchW(search_text)

        ok = bool(sdk.Everything_QueryW(True))
        last_error = int(sdk.Everything_GetLastError())
        if (not ok) or last_error != 0:
            return None

        result_count = int(sdk.Everything_GetNumResults())
        if result_count <= 0:
            return []

        buffer = ctypes.create_unicode_buffer(SDK_RESULT_PATH_MAX)
        paths = []
        for idx in range(min(result_count, max(1, int(max_results)))):
            buffer[0] = "\0"
            sdk.Everything_GetResultFullPathNameW(idx, buffer, SDK_RESULT_PATH_MAX)
            file_path = buffer.value.strip()
            if file_path:
                paths.append(file_path)
        return paths
    except Exception:
        return None


def _run_es_query(es_exe: str, source_path: str, query: str, max_results: int) -> Optional[List[str]]:
    try:
        limit = max(1, int(max_results))
        cmd = [es_exe, "-n", str(limit), "-path", source_path, query]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    if not result.stdout:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _search_with_sdk(normalized_keywords: List[str], source_path: str, max_results: int) -> Optional[List[str]]:
    sdk = _load_everything_sdk()
    if not sdk:
        return None

    merged_paths = []
    seen_paths = set()

    for chunk in _iter_keyword_chunks(normalized_keywords, QUERY_KEYWORD_CHUNK_SIZE):
        chunk_query = "|".join(keyword.replace('"', " ") for keyword in chunk)
        chunk_paths = _run_sdk_query(sdk, source_path, chunk_query, max_results)
        if chunk_paths is None:
            return None

        if _append_paths_limited(chunk_paths, merged_paths, seen_paths, max_results):
            break

    return merged_paths


def _search_with_es(es_exe: str, normalized_keywords: List[str], source_path: str, max_results: int) -> List[str]:
    merged_paths = []
    seen_paths = set()

    for chunk in _iter_keyword_chunks(normalized_keywords, QUERY_KEYWORD_CHUNK_SIZE):
        chunk_query = "|".join(keyword.replace('"', " ") for keyword in chunk)
        chunk_paths = _run_es_query(es_exe, source_path, chunk_query, max_results)
        if chunk_paths is None:
            continue

        if _append_paths_limited(chunk_paths, merged_paths, seen_paths, max_results):
            break

    return merged_paths

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
    exact_match: bool = True,  # 保留参数但始终精确匹配
    max_results: int = DEFAULT_MAX_RESULTS,
) -> List[str]:
    global _last_backend

    if not keywords or not source_path:
        return []

    source_path = os.path.normpath(source_path)
    normalized_keywords = _normalize_keywords(keywords)
    if not normalized_keywords:
        return []

    max_results = max(1, int(max_results))

    raw_paths = _search_with_sdk(normalized_keywords, source_path, max_results)
    if raw_paths is not None:
        _last_backend = "sdk"
    else:
        es_exe = find_es_exe()
        if not es_exe:
            _last_backend = "none"
            return []
        _last_backend = "es"
        raw_paths = _search_with_es(es_exe, normalized_keywords, source_path, max_results)

    valid_exts = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in extensions
    }
    keyword_set = set(normalized_keywords)

    results = []
    seen_paths = set()

    for file_path in raw_paths:
        normalized_path = os.path.normpath(file_path)
        if normalized_path in seen_paths:
            continue

        _, ext = os.path.splitext(normalized_path)
        if ext.lower() not in valid_exts:
            continue

        filename = os.path.basename(normalized_path)
        name_no_ext = os.path.splitext(filename)[0].lower()
        if name_no_ext not in keyword_set:
            continue

        seen_paths.add(normalized_path)
        results.append(normalized_path)
        if len(results) >= max_results:
            break

    return results

def parse_keywords(text: str) -> List[str]:
    text = text.replace(",", " ")
    return [w.strip() for w in text.split() if w.strip()]
