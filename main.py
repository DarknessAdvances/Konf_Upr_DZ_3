import argparse
import re
import toml
import sys


class ConfigParser:
    def __init__(self, text):
        self.text = text
        self.variables = {}
        self.result = {}

    def parse(self):
        lines = self.text.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "<-" in line:
                self._parse_assignment(line)
            else:
                raise SyntaxError(f"Invalid syntax: {line}")
        return self.result

    def _parse_assignment(self, line):
        match = re.match(r"^([A-Z]+)\s*<-\s*(.+)$", line)
        # match = re.match(r"^([A-Z]+)\s*<-\s*(\|.+\||-?\d+|\(list .+\)|.+)$", line)
        #print(line)
        #print(match)
        if not match:
            raise SyntaxError(f"Invalid assignment syntax: {line}")
        name, value = match.groups()
        value = self._evaluate_value(value.strip())
        self.variables[name] = value
        self.result[name] = value

    def _evaluate_value(self, value):
        # Проверка на положительные и отрицательные числа
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)
        elif value.startswith("(list") and value.endswith(")"):
            return self._parse_list(value)
        elif value.startswith("|") and value.endswith("|"):
            return self._evaluate_expression(value[1:-1])
        else:
            raise SyntaxError(f"Invalid value: {value}")

    def _parse_list(self, value):
        # Убираем обертку "(list" и ")" и разбиваем элементы по пробелам
        items = value[5:-1].strip()
        elements = []
        current_item = ""
        depth = 0

        # Обрабатываем вложенные списки
        for char in items:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1

            if depth > 0 or (depth == 0 and char not in " \t"):
                current_item += char
            elif depth == 0 and char in " \t":
                if current_item:
                    elements.append(current_item.strip())
                    current_item = ""
            else:
                current_item += char

        # Добавляем последний элемент, если есть
        if current_item:
            elements.append(current_item.strip())

        # Рекурсивно обрабатываем каждый элемент
        return [self._evaluate_value(item) for item in elements]

    def _evaluate_expression(self, expr):
        # Простая обработка выражений: поддержка `+`, `concat()`, `abs()`.
        expr = expr.strip()
        if "+" in expr:
            left, right = map(str.strip, expr.split("+"))

            # Получаем значения переменных или преобразуем их в числа
            left_val = self.variables.get(left, left)
            right_val = self.variables.get(right, right)

            # Преобразуем в числа, если это возможно
            if isinstance(left_val, str) and left_val.isdigit():
                left_val = int(left_val)
            if isinstance(right_val, str) and right_val.isdigit():
                right_val = int(right_val)

            # Проверяем, являются ли оба значения числовыми
            if isinstance(left_val, int) and isinstance(right_val, int):
                return left_val + right_val
            else:
                raise TypeError(f"Cannot add non-numeric values: {left_val}, {right_val}")
            # left, right = map(str.strip, expr.split("+"))
            # left_val = self.variables.get(left, int(left))
            # right_val = self.variables.get(right, int(right))
            # return left_val + right_val
        elif expr.startswith("concat(") and expr.endswith(")"):
            args = expr[7:-1].split(",")
            return "".join(arg.strip() for arg in args)
        # elif expr.startswith("abs(") and expr.endswith(")"):
        #     arg = expr[4:-1].strip()
        #     value = self.variables.get(arg, int(arg))
        #     return abs(value)
        elif expr.startswith("abs(") and expr.endswith(")"):
            arg = expr[4:-1].strip()
            # Проверка, является ли аргумент переменной или числом
            if arg in self.variables:
                value = self.variables[arg]
            elif arg.lstrip("-").isdigit():  # Проверка на отрицательное число
                value = int(arg)
            else:
                raise SyntaxError(f"Invalid argument for abs(): {arg}")
            return abs(value)
        else:
            raise SyntaxError(f"Unsupported expression: {expr}")


def main():
    parser = argparse.ArgumentParser(description="Educational config language to TOML converter.")
    parser.add_argument("output", help="Path to the output TOML file.")
    args = parser.parse_args()

    try:
        # Считывание текста конфигурации из stdin
        input_text = sys.stdin.read()
        config_parser = ConfigParser(input_text)
        parsed_config = config_parser.parse()
        with open(args.output, "w") as toml_file:
            toml.dump(parsed_config, toml_file)
        print(f"TOML output written to {args.output}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

# python main.py output.toml
