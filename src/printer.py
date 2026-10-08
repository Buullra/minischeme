"""打印：值 -> 文本。

两种打印形式：
- write   顶层结果用：字符串带引号、转义可见（"a\\nb"）
- display display 过程用：字符串不带引号、转义还原为真实字符
"""

from values import NIL, Builtin, Closure, Pair, Symbol

# write 形式下字符串需要转义回去的字符
_WRITE_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t"}


def scheme_write(value):
    """值的 write 形式（顶层打印结果用）。"""
    return _format(value, display=False)


def scheme_display(value):
    """值的 display 形式（display 过程用）。"""
    return _format(value, display=True)


def _format(value, display):
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is NIL:
        return "()"
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, str):  # 字符串（Symbol 是子类，须先判 Symbol）
        if display:
            return value
        escaped = "".join(_WRITE_ESCAPES.get(ch, ch) for ch in value)
        return f'"{escaped}"'
    if isinstance(value, Pair):
        return _format_pair(value, display)
    if isinstance(value, float):
        return _format_float(value)
    if isinstance(value, int):  # 注意 bool 已在上面处理
        return str(value)
    if isinstance(value, (Builtin, Closure)):
        return "#<procedure>"
    if value is None:
        return ""  # 无值，顶层不打印（main 会跳过）
    raise TypeError(f"无法打印的值: {value!r}")


def _format_float(value):
    """浮点打印：0.5 而不是 0.500000；整数值的浮点保留 .0。"""
    return repr(value)


def _format_pair(pair, display):
    """打印点对链：真列表 (1 2 3)，非真列表带点 (1 . 2)。"""
    parts = []
    cur = pair
    while isinstance(cur, Pair):
        parts.append(_format(cur.car, display))
        cur = cur.cdr
    if cur is not NIL:  # 链尾不是空表 -> 点对记法
        parts.append(".")
        parts.append(_format(cur, display))
    return "(" + " ".join(parts) + ")"
