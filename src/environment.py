"""环境：变量绑定表 + 指向外层环境的指针（词法作用域的关键）。

每层环境是一个 dict 加一个 parent 指针。查找变量时沿 parent
链向外找，实现词法作用域；闭包能记住定义处环境就靠这个结构。
"""

from values import SchemeError


class Environment:
    """一层环境：bindings 是本层绑定，parent 是外层环境。"""

    __slots__ = ("bindings", "parent")

    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def define(self, name, value):
        """在当前层绑定名字（重复 define 会覆盖本层旧值）。"""
        self.bindings[str(name)] = value

    def lookup(self, name):
        """沿 parent 链向外查找变量；找不到报错。"""
        env = self
        while env is not None:
            if name in env.bindings:
                return env.bindings[name]
            env = env.parent
        raise SchemeError(f"未定义的符号: {name}")
