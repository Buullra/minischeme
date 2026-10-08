"""入口：读文件/标准输入，依次求值每个顶层表达式并逐行打印结果。

用法：
    python3 src/main.py file1.scm [file2.scm ...]   # 多个文件共享全局环境
    python3 src/main.py                             # 从标准输入读取
"""

import sys

from stdlib import make_global_env
from environment import Environment
from evaluator import evaluate
from parser import parse
from printer import scheme_write
from values import SchemeError


def run_source(source, env):
    """求值一段程序文本：每个顶层表达式独占一行打印；None（无值）不打印。"""
    for expr in parse(source):
        result = evaluate(expr, env)
        if result is not None:
            print(scheme_write(result))


def main(argv):
    # 递归程序需要更深的调用栈（解释器本身没有尾调用优化）
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))

    env = make_global_env(Environment)
    if argv:
        for path in argv:
            with open(path, "r", encoding="utf-8") as f:
                run_source(f.read(), env)
    else:
        run_source(sys.stdin.read(), env)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except SchemeError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
