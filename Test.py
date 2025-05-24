import time
import random
from collections import defaultdict
from LR1Item import LR1Item
from LL1Parser import LL1Parser
from LR0Item import  LR0Item
from LALR1Parser import LALR1Parser
from SLR1Parser import  SLR1Parser
from Grammar import Grammar as Grammar



class ParserTester:
    def __init__(self):
        self.results = defaultdict(dict)

    def create_grammars(self):
        """创建测试用的文法"""
        # 基本表达式文法
        self.expr_grammar = Grammar([
            ("E", ["E", "+", "T"]),
            ("E", ["T"]),
            ("T", ["T", "*", "F"]),
            ("T", ["F"]),
            ("F", ["(", "E", ")"]),
            ("F", ["id"])
        ], "E")

        # 增强文法用于LR分析
        self.augmented_expr_grammar = Grammar([
            ("E'", ["E"]),
            ("E", ["E", "+", "T"]),
            ("E", ["T"]),
            ("T", ["T", "*", "F"]),
            ("T", ["F"]),
            ("F", ["(", "E", ")"]),
            ("F", ["id"])
        ], "E'")

        # LL(1)适用的文法
        self.ll1_grammar = Grammar([
            ("E", ["T", "E'"]),
            ("E'", ["+", "T", "E'"]),
            ("E'", ["ε"]),
            ("T", ["F", "T'"]),
            ("T'", ["*", "F", "T'"]),
            ("T'", ["ε"]),
            ("F", ["(", "E", ")"]),
            ("F", ["id"])
        ], "E")

    def generate_test_cases(self, num_cases=10, max_depth=5):
        """生成随机测试用例"""
        self.test_cases = []
        for _ in range(num_cases):
            depth = random.randint(1, max_depth)
            self.test_cases.append(self._generate_expr(depth))
        return self.test_cases

    def _generate_expr(self, depth):
        if depth == 0:
            return ["id"]
        choice = random.randint(0, 3)
        if choice == 0:
            return ["(", *self._generate_expr(depth - 1), ")"]
        elif choice == 1:
            return [*self._generate_expr(depth - 1), "+", *self._generate_expr(depth - 1)]
        else:
            return [*self._generate_expr(depth - 1), "*", *self._generate_expr(depth - 1)]

    def test_parser(self, parser_class, grammar, test_cases):
        """测试单个解析器"""
        times = []
        for case in test_cases:
            try:
                start = time.time()
                parser = parser_class(grammar)
                parser.parse(case)
                end = time.time()
                times.append(end - start)
            except Exception as e:
                print(f"Parser {parser_class.__name__} failed on case {case}: {str(e)}")
                times.append(float('inf'))
        return times

    def run_comparison(self, num_cases=20, max_depth=6):
        """运行完整的比较测试"""
        self.create_grammars()
        test_cases = self.generate_test_cases(num_cases, max_depth)

        parsers = [
            ("LL(1)", LL1Parser, self.ll1_grammar),
            ("LR(0)", LR0Item, self.augmented_expr_grammar),
            ("SLR(1)", SLR1Parser, self.augmented_expr_grammar),
            ("LR(1)", LR1Item, self.augmented_expr_grammar),
            ("LALR(1)", LALR1Parser, self.augmented_expr_grammar)
        ]

        results = {}
        for name, parser_class, grammar in parsers:
            print(f"Testing {name} parser...")
            times = self.test_parser(parser_class, grammar, test_cases)
            avg_time = sum(t for t in times if t != float('inf')) / len(times)
            success_rate = sum(1 for t in times if t != float('inf')) / len(times)
            results[name] = {
                "average_time": avg_time,
                "success_rate": success_rate,
                "raw_times": times
            }

        return results

    def print_results(self, results):
        """打印比较结果"""
        print("\nParser Comparison Results:")
        print("{:<10} {:<15} {:<15}".format("Parser", "Avg Time (s)", "Success Rate"))
        print("-" * 40)
        for name, data in results.items():
            print("{:<10} {:<15.6f} {:<15.2%}".format(
                name,
                data["average_time"],
                data["success_rate"]
            ))

        # 打印详细数据
        print("\nDetailed Timing Data:")
        for name, data in results.items():
            print(f"\n{name} parser timings:")
            print(", ".join(f"{t:.6f}" for t in data["raw_times"]))

if __name__ == "__main__":
    tester = ParserTester()
    results = tester.run_comparison(num_cases=5, max_depth=3)  # 小规模测试
    tester.print_results(results)