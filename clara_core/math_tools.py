"""Safe, deterministic arithmetic shortcuts for obvious numeric requests."""
from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any

_ALLOWED_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_PREFIX = re.compile(r"^(?:(?:quanto\s+(?:fa|è|e)|calcola(?:mi)?|esegui|risolvi)\s+)+", re.I)


def _eval_node(node: ast.AST, count: list[int]) -> float | int:
    count[0] += 1
    if count[0] > 60:
        raise ValueError("Espressione troppo complessa")
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        value = node.value
        if abs(value) > 1e100:
            raise ValueError("Numero troppo grande")
        return value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_node(node.operand, count))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY:
        left = _eval_node(node.left, count)
        right = _eval_node(node.right, count)
        if isinstance(node.op, ast.Pow) and (abs(float(right)) > 12 or abs(float(left)) > 1e8):
            raise ValueError("Potenza fuori dai limiti supportati")
        result = _ALLOWED_BINARY[type(node.op)](left, right)
        if isinstance(result, complex) or not math.isfinite(float(result)) or abs(result) > 1e100:
            raise ValueError("Risultato fuori dai limiti supportati")
        return result
    raise ValueError("Espressione non supportata")


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return f"{value:.10g}".replace(".", ",")


def solve_simple_arithmetic(text: str) -> str | None:
    """Answer only unambiguous arithmetic/percentage expressions; never evaluates Python code."""
    original = " ".join(str(text or "").split()).strip()
    if not original or len(original) > 160:
        return None
    value = original.casefold().rstrip("?.! ")
    value = re.sub(r"^(?:per favore\s+)?", "", value)

    percent = re.fullmatch(
        r"(?:(?:quanto\s+(?:fa|è|e)|calcola(?:mi)?|esegui)\s+)?"
        r"(\d+(?:[.,]\d+)?)\s*%\s*(?:di|del|della)\s*(\d+(?:[.,]\d+)?)",
        value,
    )
    if percent:
        rate = float(percent.group(1).replace(",", "."))
        base = float(percent.group(2).replace(",", "."))
        answer = (rate / 100) * base
        if not math.isfinite(answer):
            return None
        formatted = _format_number(answer)
        return f"Il {percent.group(1)}% di {percent.group(2)} è **{formatted}**.\n\nCalcolo: `{percent.group(1)} ÷ 100 × {percent.group(2)} = {formatted}`."

    expression = _PREFIX.sub("", value).strip().rstrip("=").strip()
    # Natural Italian operator words are convenient for short arithmetic prompts.
    expression = re.sub(r"\b(?:moltiplicato|moltiplicata)\s+per\b", "*", expression)
    expression = re.sub(r"\bdiviso(?:\s+per)?\b", "/", expression)
    expression = re.sub(r"\bpiù\b", "+", expression)
    expression = re.sub(r"\bmeno\b", "-", expression)
    expression = re.sub(r"\bper\b", "*", expression)
    expression = expression.replace("×", "*").replace("÷", "/").replace("−", "-")
    expression = re.sub(r"(?<=\d)\s*[x]\s*(?=\d)", "*", expression, flags=re.I)
    expression = re.sub(r"(?<!\*)\^(?!\*)", "**", expression)
    expression = re.sub(r"(?<=\d),(?=\d)", ".", expression)
    if len(expression) > 100 or not re.fullmatch(r"[0-9\s().+*/%\-]+(?:\*\*)?[0-9\s().+*/%\-]*", expression):
        return None
    if not re.search(r"[+*/%\-]", expression) and "**" not in expression:
        return None
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body, [0])
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None
    formatted = _format_number(result)
    display = expression.replace("**", "^")
    return f"Il risultato è **{formatted}**.\n\nCalcolo eseguito: `{display} = {formatted}`."
