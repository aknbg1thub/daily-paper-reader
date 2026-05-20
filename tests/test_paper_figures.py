import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class PaperFiguresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        src_dir = root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        cls.mod = _load_module("paper_figures_mod", src_dir / "paper_figures.py")

    def _make_png_bytes(self, size, color):
        img = Image.new("RGB", size, color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_extract_figures_from_pdf(self):
        with tempfile.TemporaryDirectory() as d:
            pdf_path = Path(d) / "sample.pdf"
            out_dir = Path(d) / "assets"

            big_img = self._make_png_bytes((640, 480), (220, 80, 80))
            small_img = self._make_png_bytes((80, 80), (80, 80, 220))

            doc = fitz.open()
            page = doc.new_page()
            page.insert_image(fitz.Rect(40, 40, 400, 320), stream=big_img)
            page.insert_image(fitz.Rect(420, 40, 500, 120), stream=small_img)
            doc.save(pdf_path)
            doc.close()

            figures = self.mod.extract_figures_from_pdf(
                str(pdf_path),
                str(out_dir),
                "assets/figures/arxiv/test-paper",
            )

            self.assertEqual(len(figures), 1)
            self.assertTrue(figures[0]["url"].endswith("fig-001.webp"))
            self.assertTrue((out_dir / "fig-001.webp").exists())

            meta_path = out_dir / "meta.json"
            self.assertTrue(meta_path.exists())
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(len(meta["figures"]), 1)
            self.assertEqual(meta["version"], 4)

    def test_extract_figures_with_pdffigures2_payload(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            output_dir = tmp_dir / "out"

            render_img_2 = self._make_png_bytes((640, 480), (20, 180, 120))
            render_img_1 = self._make_png_bytes((640, 480), (180, 120, 20))

            original_resolve = self.mod._resolve_pdffigures2_jar
            original_which = self.mod.shutil.which
            original_run = self.mod.subprocess.run

            class DummyResult:
                def __init__(self):
                    self.returncode = 0
                    self.stdout = ""
                    self.stderr = ""

            def fake_run(cmd, stdout=None, stderr=None, text=None, check=None):
                input_dir = Path(cmd[4])
                data_dir = Path(cmd[6])
                image_dir = Path(cmd[8])
                base_name = next(input_dir.glob("*.pdf")).stem
                image_dir.mkdir(parents=True, exist_ok=True)
                data_dir.mkdir(parents=True, exist_ok=True)
                image_path_2 = image_dir / f"{base_name}-Figure2-1.png"
                image_path_1 = image_dir / f"{base_name}-Figure1-1.png"
                image_path_2.write_bytes(render_img_2)
                image_path_1.write_bytes(render_img_1)
                payload = {
                    "figures": [
                        {
                            "renderURL": str(image_path_2),
                            "caption": "Figure 2. Second caption",
                            "page": 0,
                        },
                        {
                            "renderURL": str(image_path_1),
                            "caption": "Figure 1. First caption",
                            "page": 1,
                        }
                    ],
                    "tables": [
                        {
                            "renderURL": str(image_path_1),
                            "caption": "Table I. Parameters",
                            "page": 2,
                        }
                    ],
                }
                (data_dir / f"{base_name}.json").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )
                return DummyResult()

            self.mod._resolve_pdffigures2_jar = lambda: "/tmp/pdffigures2.jar"
            self.mod.shutil.which = lambda name: "/usr/bin/java" if name == "java" else original_which(name)
            self.mod.subprocess.run = fake_run
            try:
                figures = self.mod._extract_figures_with_pdffigures2(
                    str(pdf_path),
                    str(output_dir),
                    "assets/figures/arxiv/sample",
                )
            finally:
                self.mod._resolve_pdffigures2_jar = original_resolve
                self.mod.shutil.which = original_which
                self.mod.subprocess.run = original_run

            self.assertEqual(len(figures), 2)
            self.assertEqual(figures[0]["caption"], "Figure 1. First caption")
            self.assertEqual(figures[0]["figure_number"], "1")
            self.assertEqual(figures[0]["page"], 2)
            self.assertEqual(figures[1]["caption"], "Figure 2. Second caption")
            self.assertEqual(figures[1]["figure_number"], "2")
            self.assertEqual(figures[1]["page"], 1)
            self.assertTrue((output_dir / "fig-001.webp").exists())
            meta = json.loads((output_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["extractor"], "pdffigures2")
            self.assertEqual(meta["figures"][0]["figure_number"], "1")
            self.assertEqual(meta["figures"][0]["item_type"], "figure")

    def test_extract_tables_with_pdffigures2_payload(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            output_dir = tmp_dir / "out"
            table_img = self._make_png_bytes((700, 360), (245, 245, 245))

            original_resolve = self.mod._resolve_pdffigures2_jar
            original_which = self.mod.shutil.which
            original_run = self.mod.subprocess.run

            class DummyResult:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(cmd, stdout=None, stderr=None, text=None, check=None):
                input_dir = Path(cmd[4])
                data_dir = Path(cmd[6])
                image_dir = Path(cmd[8])
                base_name = next(input_dir.glob("*.pdf")).stem
                image_dir.mkdir(parents=True, exist_ok=True)
                data_dir.mkdir(parents=True, exist_ok=True)
                image_path = image_dir / f"{base_name}-Table1-1.png"
                image_path.write_bytes(table_img)
                payload = {
                    "figures": [],
                    "tables": [
                        {
                            "renderURL": str(image_path),
                            "caption": "Table I. Hardware parameters.",
                            "page": 9,
                        }
                    ],
                }
                (data_dir / f"{base_name}.json").write_text(json.dumps(payload), encoding="utf-8")
                return DummyResult()

            self.mod._resolve_pdffigures2_jar = lambda: "/tmp/pdffigures2.jar"
            self.mod.shutil.which = lambda name: "/usr/bin/java" if name == "java" else original_which(name)
            self.mod.subprocess.run = fake_run
            try:
                figures = self.mod._extract_figures_with_pdffigures2(
                    str(pdf_path),
                    str(output_dir),
                    "assets/figures/arxiv/sample",
                )
            finally:
                self.mod._resolve_pdffigures2_jar = original_resolve
                self.mod.shutil.which = original_which
                self.mod.subprocess.run = original_run

            self.assertEqual(len(figures), 1)
            self.assertEqual(figures[0]["item_type"], "table")
            self.assertEqual(figures[0]["figure_number"], "I")

    def test_missing_caption_crop_is_added(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            output_dir = tmp_dir / "out"
            output_dir.mkdir()

            doc = fitz.open()
            page = doc.new_page(width=612, height=792)
            page.draw_rect(fitz.Rect(80, 120, 520, 420), color=(0, 0, 1), fill=(0.88, 0.95, 1))
            page.insert_textbox(fitz.Rect(72, 440, 540, 500), "Fig. 2. Missing vector-only schematic.", fontsize=12)
            doc.save(pdf_path)
            doc.close()

            merged = self.mod._merge_missing_caption_crops(
                str(pdf_path),
                [],
                str(output_dir),
            )

            self.assertEqual(len(merged), 1)
            self.assertEqual(merged[0]["figure_number"], "2")
            self.assertEqual(merged[0]["item_type"], "figure")
            self.assertTrue(Path(merged[0]["_source_path"]).exists())

    def test_duplicate_figure_label_is_disambiguated(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            output_dir = tmp_dir / "out"
            render_img = self._make_png_bytes((640, 480), (20, 180, 120))

            original_resolve = self.mod._resolve_pdffigures2_jar
            original_which = self.mod.shutil.which
            original_run = self.mod.subprocess.run

            class DummyResult:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(cmd, stdout=None, stderr=None, text=None, check=None):
                input_dir = Path(cmd[4])
                data_dir = Path(cmd[6])
                image_dir = Path(cmd[8])
                base_name = next(input_dir.glob("*.pdf")).stem
                image_dir.mkdir(parents=True, exist_ok=True)
                data_dir.mkdir(parents=True, exist_ok=True)
                img1 = image_dir / f"{base_name}-Figure7-1.png"
                img2 = image_dir / f"{base_name}-Figure7-2.png"
                img1.write_bytes(render_img)
                img2.write_bytes(self._make_png_bytes((640, 480), (120, 20, 180)))
                payload = {
                    "figures": [
                        {"renderURL": str(img1), "caption": "Fig. 7. Main result.", "page": 8},
                        {"renderURL": str(img2), "caption": "Fig. 7. Appendix result.", "page": 9},
                    ]
                }
                (data_dir / f"{base_name}.json").write_text(json.dumps(payload), encoding="utf-8")
                return DummyResult()

            self.mod._resolve_pdffigures2_jar = lambda: "/tmp/pdffigures2.jar"
            self.mod.shutil.which = lambda name: "/usr/bin/java" if name == "java" else original_which(name)
            self.mod.subprocess.run = fake_run
            try:
                figures = self.mod._extract_figures_with_pdffigures2(
                    str(pdf_path),
                    str(output_dir),
                    "assets/figures/arxiv/sample",
                )
            finally:
                self.mod._resolve_pdffigures2_jar = original_resolve
                self.mod.shutil.which = original_which
                self.mod.subprocess.run = original_run

            self.assertEqual(figures[0]["figure_number"], "7")
            self.assertEqual(figures[1]["figure_number"], "Appendix 7")

    def test_text_block_crop_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            image_path = Path(d) / "text-block.png"
            img = Image.new("RGB", (520, 420), "white")
            draw = ImageDraw.Draw(img)
            for y in range(8, 390, 10):
                draw.rectangle((4, y, 64, y + 6), fill="black")
                draw.rectangle((86, y, 136, y + 6), fill="black")
                draw.rectangle((160, y, 194, y + 6), fill="black")
            img.save(image_path)

            self.assertTrue(self.mod._looks_like_text_block(str(image_path)))

    def test_colored_plot_is_not_rejected_as_text_block(self):
        with tempfile.TemporaryDirectory() as d:
            image_path = Path(d) / "plot.png"
            img = Image.new("RGB", (560, 420), "white")
            draw = ImageDraw.Draw(img)
            draw.line((40, 340, 520, 340), fill="black", width=2)
            draw.line((40, 40, 40, 340), fill="black", width=2)
            for offset, color in [(0, "red"), (18, "steelblue"), (36, "goldenrod")]:
                points = [(40 + x * 8, 260 - ((x + offset) % 37) * 4) for x in range(60)]
                draw.line(points, fill=color, width=3)
            img.save(image_path)

            self.assertFalse(self.mod._looks_like_text_block(str(image_path)))

    def test_extract_figure_number(self):
        self.assertEqual(self.mod._extract_figure_number("Fig. 12b. Demo"), "12b")
        self.assertEqual(self.mod._extract_figure_number("Figure 3: Demo"), "3")
        self.assertEqual(self.mod._extract_figure_number("No numbered caption"), "")


if __name__ == "__main__":
    unittest.main()
