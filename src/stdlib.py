"""内置过程库：spec §5 的全部内置函数，装进初始全局环境。

每个内置过程接收一个 Python 列表（已求值的实参），返回一个值。
参数个数与类型检查在这里完成，错误统一抛 SchemeError。
"""

from values import NIL, Builtin, Closure, Pair, SchemeError, Symbol, list_to_pair, pair_to_list
from printer import scheme_display


# ---------- 小工具 ----------

def _check_argc(name, args, lo, hi=None):
    """检查实参个数在 [lo, hi] 之间（hi 为 None 表示不限）。"""
    n = len(args)
    if n < lo or (hi is not None and n > hi):
        rng = str(lo) if hi == lo else f"{lo}+" if hi is None else f"{lo}-{hi}"
        raise SchemeError(f"{name}: 参数个数应为 {rng}，实得 {n}")


def _check_number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemeError(f"{name}: 需要数字参数，实得 {value!r}")
    return value


def _check_pair(name, value):
    if not isinstance(value, Pair):
        raise SchemeError(f"{name}: 需要点对参数，实得 {value!r}")
    return value


def _is_false(value):
    """只有 #f 是假，0、()、"" 都是真。"""
    return value is False


# ---------- 算术 ----------

def _div(a, b):
    """除法：整数相除得整数商，负数商向零截断；有浮点则按浮点除。"""
    if b == 0:
        raise SchemeError("除数为 0")
    if isinstance(a, int) and isinstance(b, int):
        q = abs(a) // abs(b)
        return q if (a < 0) == (b < 0) else -q
    return a / b


def _quotient(a, b):
    """整除商，负数商向零截断。"""
    _check_number("quotient", a)
    _check_number("quotient", b)
    if b == 0:
        raise SchemeError("除数为 0")
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _modulo(a, b):
    _check_number("modulo", a)
    _check_number("modulo", b)
    if b == 0:
        raise SchemeError("除数为 0")
    return a % b  # Python 取模结果符号跟随除数，与 Scheme modulo 一致


def _arith_add(args):
    total = 0
    for a in args:
        total += _check_number("+", a)
    return total


def _arith_sub(args):
    _check_argc("-", args, 1)
    first = _check_number("-", args[0])
    if len(args) == 1:  # 单参数取反
        return -first
    result = first
    for a in args[1:]:
        result -= _check_number("-", a)
    return result


def _arith_mul(args):
    result = 1
    for a in args:
        result *= _check_number("*", a)
    return result


def _arith_div(args):
    _check_argc("/", args, 1)
    first = _check_number("/", args[0])
    if len(args) == 1:  # 单参数求倒数，结果是浮点
        if first == 0:
            raise SchemeError("除数为 0")
        return 1 / first
    result = first
    for a in args[1:]:
        result = _div(result, _check_number("/", a))
    return result


def _wrap2(name, fn):
    def proc(args):
        _check_argc(name, args, 2, 2)
        return fn(args[0], args[1])

    return proc


# ---------- 比较 ----------

def _make_compare(name, op):
    """链式比较：相邻两两都成立才为真；支持数字与符号。"""

    def proc(args):
        _check_argc(name, args, 2)
        for a, b in zip(args, args[1:]):
            for v in (a, b):
                if isinstance(v, bool) or not isinstance(v, (int, float, Symbol)):
                    raise SchemeError(f"{name}: 需要数字或符号参数，实得 {v!r}")
            if not op(a, b):
                return False
        return True

    return proc


# ---------- 相等 ----------

def _eq(a, b):
    """eq?：符号/数字/布尔按值比较；复合数据按同一性（是否同一对象）。"""
    if a is NIL or b is NIL:
        return a is b
    simple = (bool, int, float, Symbol, str)
    if isinstance(a, simple) and isinstance(b, simple):
        if type(a) is not type(b) and not (
            isinstance(a, (int, float))
            and isinstance(b, (int, float))
            and not isinstance(a, bool)
            and not isinstance(b, bool)
        ):
            return False  # 类型不同（如 #t 与 1、符号与字符串）不相等
        return a == b
    return a is b


def _equal(a, b):
    """equal?：结构相等，逐层比较；先比类型再比值。"""
    if a is NIL or b is NIL:
        return a is b
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _equal(a.car, b.car) and _equal(a.cdr, b.cdr)
    if isinstance(a, Pair) or isinstance(b, Pair):
        return False
    return _eq(a, b)


# ---------- 列表 ----------

def _list_proc(args):
    return list_to_pair(args)


def _length(args):
    _check_argc("length", args, 1, 1)
    try:
        return len(pair_to_list(args[0]))
    except TypeError:
        raise SchemeError("length: 需要真列表参数")


def _append(args):
    result = NIL
    for lst in reversed(args):
        try:
            items = pair_to_list(lst)
        except TypeError:
            raise SchemeError("append: 需要真列表参数")
        result = list_to_pair(items, result)
    return result


# ---------- 输出 ----------

def _display(args):
    _check_argc("display", args, 1, 1)
    print(scheme_display(args[0]), end="")
    return None  # 无值，顶层不打印


def _newline(args):
    _check_argc("newline", args, 0, 0)
    print()
    return None


# ---------- 注册表 ----------

def make_global_env(env_class):
    """创建全局环境，装入全部内置过程。"""
    env = env_class()

    def add(name, fn):
        env.define(name, Builtin(name, fn))

    # 算术
    add("+", _arith_add)
    add("-", _arith_sub)
    add("*", _arith_mul)
    add("/", _arith_div)
    add("modulo", _wrap2("modulo", _modulo))
    add("quotient", _wrap2("quotient", _quotient))
    add("expt", _wrap2("expt", lambda a, b: _check_number("expt", a) ** _check_number("expt", b)))
    def _abs(args):
        _check_argc("abs", args, 1, 1)
        return abs(_check_number("abs", args[0]))

    add("abs", _abs)

    # 比较（链式）
    import operator

    add("=", _make_compare("=", operator.eq))
    add("<", _make_compare("<", operator.lt))
    add(">", _make_compare(">", operator.gt))
    add("<=", _make_compare("<=", operator.le))
    add(">=", _make_compare(">=", operator.ge))

    # 布尔
    add("not", lambda args: _check_argc("not", args, 1, 1) or _is_false(args[0]))

    # 列表
    add("cons", lambda args: _check_argc("cons", args, 2, 2) or Pair(args[0], args[1]))
    add("car", lambda args: _check_argc("car", args, 1, 1) or _check_pair("car", args[0]).car)
    add("cdr", lambda args: _check_argc("cdr", args, 1, 1) or _check_pair("cdr", args[0]).cdr)
    add("list", _list_proc)
    add("length", _length)
    add("append", _append)

    # 谓词
    def pred(name, fn):
        add(name, lambda args: _check_argc(name, args, 1, 1) or fn(args[0]))

    pred("null?", lambda v: v is NIL)
    pred("pair?", lambda v: isinstance(v, Pair))
    pred("list?", _is_proper_list)
    pred("number?", lambda v: isinstance(v, (int, float)) and not isinstance(v, bool))
    pred("boolean?", lambda v: isinstance(v, bool))
    pred("symbol?", lambda v: isinstance(v, Symbol))
    pred("string?", lambda v: isinstance(v, str) and not isinstance(v, Symbol))
    pred("procedure?", lambda v: isinstance(v, (Builtin, Closure)))
    pred("zero?", lambda v: _check_number("zero?", v) == 0)
    pred("even?", lambda v: _check_number("even?", v) % 2 == 0)
    pred("odd?", lambda v: _check_number("odd?", v) % 2 != 0)
    add("eq?", lambda args: _check_argc("eq?", args, 2, 2) or _eq(args[0], args[1]))
    add("equal?", lambda args: _check_argc("equal?", args, 2, 2) or _equal(args[0], args[1]))

    # 输出
    add("display", _display)
    add("newline", _newline)

    return env


def _is_proper_list(value):
    """是否真列表：Pair 链且以 NIL 结尾。"""
    while isinstance(value, Pair):
        value = value.cdr
    return value is NIL
