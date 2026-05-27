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
            self.assertEqual(meta["version"], self.mod.FIGURE_META_VERSION)

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
                            "page": 1,
                        },
                        {
                            "renderURL": str(image_path_1),
                            "caption": "Figure 1. First caption",
                            "page": 0,
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
            self.assertEqual(figures[0]["page"], 1)
            self.assertEqual(figures[1]["caption"], "Figure 2. Second caption")
            self.assertEqual(figures[1]["figure_number"], "2")
            self.assertEqual(figures[1]["page"], 2)
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

    def test_pymupdf_fallback_adds_caption_crops(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            output_dir = tmp_dir / "out"

            doc = fitz.open()
            page = doc.new_page(width=612, height=792)
            page.draw_rect(fitz.Rect(80, 120, 520, 420), color=(0, 0, 1), fill=(0.88, 0.95, 1))
            page.insert_textbox(fitz.Rect(72, 440, 540, 500), "Fig. 2. Missing vector-only schematic.", fontsize=12)
            doc.save(pdf_path)
            doc.close()

            figures = self.mod.extract_figures_from_pdf(
                str(pdf_path),
                str(output_dir),
                "assets/figures/arxiv/sample",
            )

            labels = [item.get("figure_number") for item in figures]
            self.assertIn("2", labels)
            self.assertTrue((output_dir / "meta.json").exists())

    def test_caption_visual_crop_excludes_caption_below_body(self):
        doc = fitz.open()
        try:
            page = doc.new_page(width=612, height=792)
            body_rect = fitz.Rect(80, 120, 520, 420)
            caption_rect = fitz.Rect(72, 440, 540, 500)
            page.draw_rect(body_rect, color=(0, 0, 1), fill=(0.88, 0.95, 1))
            page.insert_textbox(caption_rect, "Fig. 2. Missing vector-only schematic.", fontsize=12)

            crop = self.mod._caption_visual_crop_rect(page, caption_rect)

            self.assertIsNotNone(crop)
            self.assertLessEqual(crop.y1, caption_rect.y0)
        finally:
            doc.close()

    def test_caption_visual_crop_excludes_caption_above_table(self):
        doc = fitz.open()
        try:
            page = doc.new_page(width=612, height=792)
            caption_rect = fitz.Rect(72, 80, 540, 130)
            body_rect = fitz.Rect(80, 160, 520, 420)
            page.insert_textbox(caption_rect, "Table I: Benchmark parameters.", fontsize=12)
            page.draw_rect(body_rect, color=(0, 0, 0), fill=(0.95, 0.95, 0.95))

            crop = self.mod._caption_visual_crop_rect(page, caption_rect)

            self.assertIsNotNone(crop)
            self.assertGreaterEqual(crop.y0, caption_rect.y1)
        finally:
            doc.close()

    def test_table_crop_tightening_stops_before_following_paragraph(self):
        doc = fitz.open()
        try:
            page = doc.new_page(width=612, height=792)
            caption_rect = fitz.Rect(72, 440, 540, 462)
            page.insert_textbox(caption_rect, "Table I: Benchmark parameters.", fontsize=12)
            for y in (468, 482, 560, 564):
                page.draw_line(fitz.Point(72, y), fitz.Point(540, y), color=(0, 0, 0), width=0.6)
            page.insert_textbox(
                fitz.Rect(74, 488, 536, 556),
                "Peak Leading monomial Number of source factors Broadband scaling\n"
                "-dw p- 0 not suppressed\n+dw s+ 1 not suppressed\n",
                fontsize=11,
            )
            page.insert_textbox(
                fitz.Rect(72, 590, 540, 680),
                "This following paragraph should not be included in the table crop.",
                fontsize=12,
            )

            crop = self.mod._caption_band_crop_rect(page, caption_rect, "table")
            tightened = self.mod._tighten_table_crop_rect(page, caption_rect, crop)

            self.assertGreater(crop.y1, 590)
            self.assertLess(tightened.y1, 575)
            self.assertGreaterEqual(tightened.y0, caption_rect.y1)
        finally:
            doc.close()

    def test_table_caption_below_body_crops_table_above_caption(self):
        doc = fitz.open()
        try:
            page = doc.new_page(width=612, height=792)
            caption_rect = fitz.Rect(72, 411, 330, 425)
            page.draw_line(fitz.Point(90, 337), fitz.Point(260, 337), color=(0, 0, 0), width=0.6)
            page.draw_line(fitz.Point(90, 352), fitz.Point(260, 352), color=(0, 0, 0), width=0.6)
            page.draw_line(fitz.Point(90, 409), fitz.Point(260, 409), color=(0, 0, 0), width=0.6)
            page.insert_textbox(fitz.Rect(92, 340, 258, 407), "Category Parameter q1 q0\nQubit EJ 28 42\nCoupler Eosc 6.9", fontsize=10)
            page.insert_textbox(caption_rect, "Table 1: System parameters used in the benchmarks.", fontsize=10)
            page.insert_textbox(
                fitz.Rect(72, 448, 330, 620),
                "In all benchmarks, this paragraph follows the table and must not be included.",
                fontsize=12,
            )

            crop = self.mod._caption_band_crop_rect(page, caption_rect, "table")
            tightened = self.mod._tighten_table_crop_rect(page, caption_rect, crop)

            self.assertLessEqual(tightened.y1, caption_rect.y0)
            self.assertLess(tightened.y1, 430)
            self.assertGreaterEqual(tightened.y0, 330)
        finally:
            doc.close()

    def test_caption_without_detected_visual_region_uses_caption_band_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_dir = Path(d)
            pdf_path = tmp_dir / "sample.pdf"
            output_dir = tmp_dir / "out"
            output_dir.mkdir()

            doc = fitz.open()
            page = doc.new_page(width=612, height=792)
            body = "\n".join(
                "This paragraph contains only article text and inline formulas."
                for _ in range(18)
            )
            page.insert_textbox(fitz.Rect(120, 80, 500, 620), body, fontsize=12)
            page.insert_textbox(
                fitz.Rect(72, 650, 540, 720),
                "Fig. 1. Waveguide-coupled qubit array and engineered dissipation.",
                fontsize=12,
            )
            doc.save(pdf_path)
            doc.close()

            merged = self.mod._merge_missing_caption_crops(
                str(pdf_path),
                [],
                str(output_dir),
            )

            self.assertEqual(len(merged), 1)
            self.assertEqual(merged[0]["figure_number"], "1")
            self.assertTrue(Path(merged[0]["_source_path"]).exists())

    def test_paper_order_precedes_label_order(self):
        figures = self.mod._finalize_figure_order(
            [
                {"figure_number": "4", "item_type": "figure", "page": 6, "_source_index": 1},
                {"figure_number": "3", "item_type": "figure", "page": 7, "_source_index": 2},
                {"figure_number": "5", "item_type": "figure", "page": 7, "_source_index": 3},
                {"figure_number": "1", "item_type": "table", "page": 5, "_source_index": 4},
            ]
        )

        self.assertEqual(
            [(item["item_type"], item["figure_number"]) for item in figures],
            [("table", "1"), ("figure", "4"), ("figure", "3"), ("figure", "5")],
        )

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

    def test_caption_start_label_rejects_body_references(self):
        self.assertEqual(self.mod._extract_caption_start_label("Fig. 2. Caption")["label"], "2")
        self.assertEqual(self.mod._extract_caption_start_label("TABLE C.1 NETWORK")["label"], "C.1")
        self.assertEqual(self.mod._extract_caption_start_label("Figure 5 shows a result")["label"], "")
        self.assertEqual(self.mod._extract_caption_start_label("Table C.1 reports settings")["label"], "")


if __name__ == "__main__":
    unittest.main()
