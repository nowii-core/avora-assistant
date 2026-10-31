import unittest
from clara_core.math_tools import solve_simple_arithmetic


class MathToolsTests(unittest.TestCase):
    def test_common_arithmetic(self):
        cases = {
            '2+2': '**4**',
            'quanto fa 3*(4+2)': '**18**',
            'quanto fa 5-3': '**2**',
            'calcola 2^5': '**32**',
            'quanto fa 3 più 5': '**8**',
            'quanto fa 12 diviso 3': '**4**',
            'quanto fa 4 per 7': '**28**',
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                self.assertIn(expected, solve_simple_arithmetic(prompt))

    def test_percentages(self):
        result = solve_simple_arithmetic('quanto fa 20% di 150')
        self.assertIn('**30**', result)

    def test_rejects_ambiguous_or_unsafe_input(self):
        self.assertIsNone(solve_simple_arithmetic('risolvi x+2=5'))
        self.assertIsNone(solve_simple_arithmetic('calcola 9 / 0'))
        self.assertIsNone(solve_simple_arithmetic('__import__("os")'))
        self.assertIsNone(solve_simple_arithmetic('spiegami la matematica'))


if __name__ == '__main__':
    unittest.main()
