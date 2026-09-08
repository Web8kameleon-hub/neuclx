"""Rule-based solving for simple arithmetic, syllogisms, and classification tasks."""

from __future__ import annotations

import ast
import math
import operator as op
import re
from typing import Any, Callable, Optional, Tuple


class _SafeMathEvaluator(ast.NodeVisitor):
    _operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
    }

    _functions: dict[str, Callable[..., Any]] = {
        "sqrt": math.sqrt,
        "pow": math.pow,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "abs": abs,
    }

    _constants = {"pi": math.pi, "e": math.e}

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("unsupported constant")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        operator = self._operators.get(type(node.op))
        if operator is None:
            raise ValueError("unsupported operator")
        return operator(left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError("unsupported unary operator")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("unsupported function call")
        function = self._functions.get(node.func.id)
        if function is None:
            raise ValueError("function not allowed")
        args = [self.visit(arg) for arg in node.args]
        return function(*args)

    def visit_Name(self, node: ast.Name):
        value = self._constants.get(node.id)
        if value is None:
            raise ValueError("name not allowed")
        return value

    def generic_visit(self, node):
        raise ValueError(f"unsupported syntax: {type(node).__name__}")


class SimpleLogicEngine:
    """Deterministic solver for small, formal tasks without model calls."""

    @staticmethod
    def detect_and_solve(task: str) -> Tuple[bool, Optional[str], float]:
        text = (task or "").strip()
        if not text:
            return False, None, 0.0

        result = SimpleLogicEngine._solve_arithmetic(text)
        if result is not None:
            return True, result, 1.0

        result = SimpleLogicEngine._solve_transfer_word_problem(text)
        if result is not None:
            return True, result, 0.99

        result = SimpleLogicEngine._solve_syllogism(text)
        if result is not None:
            return True, result, 0.95

        result = SimpleLogicEngine._solve_classification(text)
        if result is not None:
            return True, result, 0.9

        return False, None, 0.0

    @staticmethod
    def _solve_arithmetic(text: str) -> Optional[str]:
        normalized = (
            text.lower()
            .replace("plus", "+")
            .replace("minus", "-")
            .replace("times", "*")
            .replace("multiplied by", "*")
            .replace("divided by", "/")
            .replace("over", "/")
            .replace("to the power of", "**")
            .replace("sqrt", "sqrt")
            .replace("^", "**")
        )

        standalone_function = re.fullmatch(r"\s*(?:sqrt|pow|sin|cos|tan|log|abs)\s*\([^()]+\)\s*", normalized)
        if standalone_function:
            candidate = standalone_function.group(0).replace("^", "**")
            try:
                parsed = ast.parse(candidate, mode="eval")
                value = _SafeMathEvaluator().visit(parsed)
            except Exception:
                value = None
            if isinstance(value, (int, float)):
                if float(value).is_integer():
                    return str(int(round(float(value))))
                return f"{float(value):.10g}"

        candidates = re.findall(r"(?:sqrt|pow|sin|cos|tan|log|abs|pi|e|[\d\s\+\-\*/\(\)\.,\*\*]+)", normalized)
        candidates = [candidate.strip() for candidate in candidates if re.search(r"\d", candidate)]
        if not candidates:
            return None

        for candidate in sorted(candidates, key=len, reverse=True):
            if not re.search(r"[\+\-\*/\(\)]|sqrt|pow|sin|cos|tan|log|abs", candidate):
                continue
            cleaned = re.sub(r"[^0-9a-zA-Z\+\-\*/\(\)\.,\s\*]", "", candidate).strip()
            if not cleaned:
                continue
            try:
                parsed = ast.parse(cleaned, mode="eval")
                value = _SafeMathEvaluator().visit(parsed)
            except Exception:
                continue
            if isinstance(value, (int, float)):
                if float(value).is_integer():
                    return str(int(round(float(value))))
                return f"{float(value):.10g}"
        return None

    @staticmethod
    def _solve_transfer_word_problem(text: str) -> Optional[str]:
        lowered = text.casefold()
        if not any(token in lowered for token in ["student", "students", "studentë", "studente"]):
            return None
        if not any(token in lowered for token in ["book", "books", "libër", "libra"]):
            return None

        numbers = [int(value) for value in re.findall(r"\d+", text)]
        if len(numbers) < 2:
            return None

        quantity = numbers[0] * numbers[1]
        if any(token in lowered for token in ["give", "gives", "gave", "transfer", "transferred", "jep", "jepet", "dhuron", "dhuroi"]):
            return str(quantity)
        if any(token in lowered for token in ["each", "secili", "çdo"]):
            return str(quantity)
        return None

    @staticmethod
    def _solve_syllogism(text: str) -> Optional[str]:
        normalized = re.sub(r"\s+", " ", text.strip())
        patterns = [
            re.compile(r"(?:all|every|të gjithë)\s+(\w+)\s+(?:are|janë)\s+(\w+).+?(\w+)\s+(?:is|është)\s+\1", re.IGNORECASE),
            re.compile(r"(?:if|nëse)\s+(\w+)\s+(?:are|janë)\s+(\w+).+?(\w+)\s+(?:is|është)\s+\1", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(normalized)
            if match:
                subject = match.group(3)
                predicate = match.group(2)
                return f"{subject} është {predicate}."
        return None

    @staticmethod
    def _solve_classification(text: str) -> Optional[str]:
        prime_match = re.search(r"(\d+)\s*(?:është\s*numër\s*i\s*thjeshtë|is\s+prime)", text, re.IGNORECASE)
        if prime_match:
            value = int(prime_match.group(1))
            if value < 2:
                return f"Jo, {value} nuk është numër i thjeshtë."
            for divisor in range(2, int(math.sqrt(value)) + 1):
                if value % divisor == 0:
                    return f"Jo, {value} nuk është numër i thjeshtë (pjestues: {divisor})."
            return f"Po, {value} është numër i thjeshtë."

        parity_match = re.search(r"(\d+)\s*(?:është\s*(çift|tek)|is\s+(even|odd))", text, re.IGNORECASE)
        if parity_match:
            value = int(parity_match.group(1))
            expected = (parity_match.group(2) or parity_match.group(3) or "").casefold()
            is_even = value % 2 == 0
            if (is_even and expected in {"çift", "even"}) or (not is_even and expected in {"tek", "odd"}):
                return f"Po, {value} është {expected}."
            return f"Jo, {value} nuk është {expected}."

        return None


__all__ = ["SimpleLogicEngine"]