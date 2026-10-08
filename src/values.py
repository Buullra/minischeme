"""核心数据表示：符号、点对、空表、过程。

解释器内部统一的值表示约定：
- 整数 / 浮点      -> Python int / float
- 布尔             -> Python True / False
- 符号             -> Symbol（str 的子类，但与字符串严格区分）
- 字符串           -> Python str（plain str，不是 Symbol）
- 点对 / 列表      -> Pair 链，空表是单例 NIL
- 无值（None 值）  -> Python None（顶层不打印）
- 过程             -> Builtin / Closure
"""


class SchemeError(Exception):
    """解释器统一抛出的错误类型。"""


class Symbol(str):
    """Scheme 符号。继承 str 便于打印，但与字符串是不同的类型。"""

    __slots__ = ()

    def __repr__(self):
        return f"Symbol({str.__repr__(self)})"


class Nil:
    """空表 ()，全局唯一单例。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "()"


# 空表单例，所有模块统一引用它
NIL = Nil()


class Pair:
    """点对：(car . cdr)。列表就是 cdr 链以 NIL 结尾的 Pair。"""

    __slots__ = ("car", "cdr")

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __repr__(self):
        return f"Pair({self.car!r}, {self.cdr!r})"


def list_to_pair(items, tail=NIL):
    """把 Python 序列转成 Pair 链（tail 作为链尾，默认空表）。"""
    result = tail
    for item in reversed(items):
        result = Pair(item, result)
    return result


def pair_to_list(pair):
    """把真列表（cdr 链以 NIL 结尾的 Pair）转成 Python 列表。

    非真列表（如点对 (1 . 2)）抛出 TypeError，由调用方处理。
    """
    items = []
    while isinstance(pair, Pair):
        items.append(pair.car)
        pair = pair.cdr
    if pair is not NIL:
        raise TypeError("not a proper list")
    return items


class Builtin:
    """内置过程：包一层 Python 函数。"""

    __slots__ = ("name", "fn")

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"#<builtin:{self.name}>"


class Closure:
    """用户定义的过程（闭包）：参数表 + 函数体 + 定义时的环境。

    env 是词法作用域的关键：调用时以定义处环境为外层新建一层环境。
    """

    __slots__ = ("params", "body", "env")

    def __init__(self, params, body, env):
        self.params = params      # Symbol 列表
        self.body = body          # 表达式列表（按 begin 语义求值）
        self.env = env

    def __repr__(self):
        return "#<procedure>"
