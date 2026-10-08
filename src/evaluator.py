"""求值器：表达式 -> 值。解释器的心脏。

核心是 evaluate 与 apply 的互相递归：
- evaluate(expr, env)：求值一个表达式。符号查环境；数字/布尔/字符串
  原样返回；括号表达式分特殊形式与函数调用两种处理。
- apply(proc, args)：调用一个过程。内置过程直接调；闭包新建一层环境
  绑实参（外层指向定义时环境），再回到 evaluate 求函数体。
"""

from environment import Environment
from values import NIL, Builtin, Closure, Pair, SchemeError, Symbol, list_to_pair


def evaluate(expr, env):
    """求值一个表达式。"""
    # 符号 -> 查环境
    if isinstance(expr, Symbol):
        return env.lookup(str(expr))
    # 自求值：数字、布尔、字符串
    if not isinstance(expr, list):
        return expr
    # 空括号表达式 () 不是函数调用
    if len(expr) == 0:
        raise SchemeError("() 不是可求值的表达式")

    first = expr[0]
    if isinstance(first, Symbol):
        handler = _SPECIAL_FORMS.get(str(first))
        if handler is not None:
            return handler(expr[1:], env)

    # 函数调用：先求值操作符和全部实参（应用序），再交给 apply
    proc = evaluate(first, env)
    args = [evaluate(arg, env) for arg in expr[1:]]
    return apply(proc, args)


def apply(proc, args):
    """调用一个过程。"""
    if isinstance(proc, Builtin):
        return proc.fn(args)
    if isinstance(proc, Closure):
        if len(args) != len(proc.params):
            raise SchemeError(
                f"参数个数不符：需要 {len(proc.params)} 个，实得 {len(args)} 个"
            )
        # 新环境的外层是闭包定义时的环境（词法作用域）
        call_env = Environment(parent=proc.env)
        for name, value in zip(proc.params, args):
            call_env.define(name, value)
        return _eval_body(proc.body, call_env)
    raise SchemeError(f"不是过程，无法调用: {proc!r}")


def _eval_body(body, env):
    """按 begin 语义依次求值，返回最后一个的结果。"""
    result = None
    for expr in body:
        result = evaluate(expr, env)
    return result


def _quote_to_pair(data):
    """把 quote 的数据（Python list 表示）转成与 cons 一致的 Pair 链。"""
    if isinstance(data, list):
        return list_to_pair([_quote_to_pair(item) for item in data])
    return data  # 原子（数字/布尔/字符串/符号）原样保留


# ---------- 特殊形式（各自决定求值顺序） ----------

def _sf_quote(args, env):
    """quote：原样返回，不求值；数据转成 Pair 链。"""
    if len(args) != 1:
        raise SchemeError("quote: 需要 1 个参数")
    return _quote_to_pair(args[0])


def _sf_if(args, env):
    """if：先求值测试，只走一个分支；假分支可省略。"""
    if len(args) not in (2, 3):
        raise SchemeError("if: 需要 2 或 3 个参数")
    test = evaluate(args[0], env)
    if test is not False:  # 只有 #f 是假
        return evaluate(args[1], env)
    if len(args) == 3:
        return evaluate(args[2], env)
    return None


def _sf_cond(args, env):
    """cond：依次求值测试，第一个非 #f 的子句按 begin 求值其余表达式。

    子句里没有表达式时返回测试值本身；else 是兜底；全部不匹配返回 None。
    """
    for clause in args:
        if not isinstance(clause, list) or len(clause) == 0:
            raise SchemeError("cond: 子句必须是 (测试 表达式...) 的形式")
        test_expr, *body = clause
        if isinstance(test_expr, Symbol) and str(test_expr) == "else":
            return _eval_body(body, env)
        test = evaluate(test_expr, env)
        if test is not False:
            if not body:  # 没有表达式时返回测试值本身
                return test
            return _eval_body(body, env)
    return None


def _sf_and(args, env):
    """and：短路——遇到第一个 #f 立刻返回；全真返回最后一个的值。"""
    result = True
    for expr in args:
        result = evaluate(expr, env)
        if result is False:
            return False
    return result


def _sf_or(args, env):
    """or：短路——遇到第一个非 #f 的值立刻返回它；全假返回 #f。"""
    for expr in args:
        result = evaluate(expr, env)
        if result is not False:
            return result
    return False


def _sf_define(args, env):
    """define：先求值右侧再绑定；函数简写展开成 lambda。结果是符号名。"""
    if len(args) < 2:
        raise SchemeError("define: 需要名字和表达式")
    target = args[0]
    if isinstance(target, list):
        # (define (函数名 参数...) 体...) 的简写形式
        if len(target) == 0 or not isinstance(target[0], Symbol):
            raise SchemeError("define: 函数名必须是符号")
        name = target[0]
        params = target[1:]
        value = Closure(params, args[1:], env)
    elif isinstance(target, Symbol):
        if len(args) != 2:
            raise SchemeError("define: 变量定义需要恰好 2 个参数")
        name = target
        value = evaluate(args[1], env)
    else:
        raise SchemeError("define: 第一个参数必须是符号或 (名 参数...)")
    env.define(name, value)
    return name  # define 的结果是被定义的符号名（顶层会打印）


def _sf_lambda(args, env):
    """lambda：制造闭包，记住定义时环境；函数体此时不求值。"""
    if len(args) < 2:
        raise SchemeError("lambda: 需要参数表和函数体")
    params = args[0]
    if not isinstance(params, list) or not all(isinstance(p, Symbol) for p in params):
        raise SchemeError("lambda: 参数表必须是符号列表")
    return Closure(params, args[1:], env)


def _sf_let(args, env):
    """let：绑定表达式先全部在外层环境求值（并行绑定），再在新环境求体。"""
    if len(args) < 2:
        raise SchemeError("let: 需要绑定表和函数体")
    bindings = args[0]
    if not isinstance(bindings, list):
        raise SchemeError("let: 绑定表必须是 ((名 表达式)...) 的形式")
    # 关键：所有绑定表达式都在外层 env 求值，绑定之间互不可见
    values = []
    for binding in bindings:
        if not isinstance(binding, list) or len(binding) != 2 or not isinstance(binding[0], Symbol):
            raise SchemeError("let: 每个绑定必须是 (名 表达式) 的形式")
        values.append((binding[0], evaluate(binding[1], env)))
    let_env = Environment(parent=env)
    for name, value in values:
        let_env.define(name, value)
    return _eval_body(args[1:], let_env)


def _sf_begin(args, env):
    """begin：从左到右依次求值，返回最后一个的结果。"""
    return _eval_body(args, env)


_SPECIAL_FORMS = {
    "quote": _sf_quote,
    "if": _sf_if,
    "cond": _sf_cond,
    "and": _sf_and,
    "or": _sf_or,
    "define": _sf_define,
    "lambda": _sf_lambda,
    "let": _sf_let,
    "begin": _sf_begin,
}
