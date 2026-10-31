import unittest
import xml.dom.minidom as minidom
from clara_core.svg_art import detect_geometric_shape, geometric_svg


class GeometryTests(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(detect_geometric_shape("mi fai lo schema di un cubo"), "cube")
        self.assertEqual(detect_geometric_shape("disegna un quadrato"), "square")
        self.assertEqual(detect_geometric_shape("ricetta della carbonara"), "")

    def test_valid_svg_without_scripts(self):
        for shape in ("cube", "box", "square", "rectangle", "triangle", "circle", "pyramid"):
            data = geometric_svg(shape)
            minidom.parseString(data)
            self.assertNotIn(b"<script", data)


if __name__ == "__main__":
    unittest.main()
