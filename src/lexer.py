"""词法分析：程序文本 -> token 列表。

token 类型：
- "(" / ")" / "'"     结构符号
- ("str", 内容)       字符串字面量（转义已解析）
- ("atom", 文本)      其他原子（数字、布尔、符号，由 parser 细分）
"""


from values import SchemeError

# 字符串里支持的转义序列
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def tokenize(source):
    """把源程序文本切成 token 列表，忽略空白和 ; 到行尾的注释。"""
    tokens = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch in " \t\r\n":
            i += 1
        elif ch == ";":  # 注释：跳到行尾
            while i < n and source[i] != "\n":
                i += 1
        elif ch in "()'":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            value, i = _read_string(source, i + 1)
            tokens.append(("str", value))
        else:  # 原子：读到空白或结构符号为止
            j = i
            while j < n and source[j] not in " \t\r\n()'\";":
                j += 1
            tokens.append(("atom", source[i:j]))
            i = j
    return tokens


def _read_string(source, i):
    """从开引号之后读字符串，返回 (内容, 下一个下标)。"""
    buf = []
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == '"':
            return "".join(buf), i + 1
        if ch == "\\":
            i += 1
            if i >= n:
                break
            esc = source[i]
            if esc not in _ESCAPES:
                raise SchemeError(f"不支持的转义: \\{esc}")
            buf.append(_ESCAPES[esc])
        else:
            buf.append(ch)
        i += 1
    raise SchemeError("字符串缺少结束引号")
