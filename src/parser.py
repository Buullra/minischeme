"""语法分析：token 列表 -> 表达式（嵌套数据结构）。

表达式的内部表示：
- 数字 / 布尔 / 字符串   -> int / float / bool / str
- 符号                   -> values.Symbol
- 括号表达式             -> Python list（元素为子表达式）
- 'x                     -> [Symbol("quote"), x]（引用简写展开）

注意：此时列表还只是 Python list；quote 的数据要到求值阶段
才转成与 cons 一致的 Pair 链（见 evaluator 的 quote 处理）。
"""

from values import SchemeError, Symbol


def parse(source):
    """解析整段程序文本，返回顶层表达式列表。"""
    from lexer import tokenize

    tokens = tokenize(source)
    exprs = []
    pos = 0
    while pos < len(tokens):
        expr, pos = _parse_expr(tokens, pos)
        exprs.append(expr)
    return exprs


def _parse_expr(tokens, pos):
    """解析一个表达式，返回 (表达式, 下一个 token 下标)。"""
    tok = tokens[pos]
    if tok == "(":
        items = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ")":
            item, pos = _parse_expr(tokens, pos)
            items.append(item)
        if pos >= len(tokens):
            raise SchemeError("括号不配对：缺少 )")
        return items, pos + 1
    if tok == ")":
        raise SchemeError("括号不配对：多余的 )")
    if tok == "'":
        quoted, pos = _parse_expr(tokens, pos + 1)
        return [Symbol("quote"), quoted], pos
    kind, text = tok
    if kind == "str":
        return text, pos + 1
    return _parse_atom(text), pos + 1


def _parse_atom(text):
    """把原子文本细分为布尔、整数、浮点或符号。"""
    if text == "#t":
        return True
    if text == "#f":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return Symbol(text)
