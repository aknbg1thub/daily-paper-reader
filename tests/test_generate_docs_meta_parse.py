import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


class GenerateDocsMetaParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        if "fitz" not in sys.modules:
            import types

            fitz_stub = types.ModuleType("fitz")
            fitz_stub.open = lambda *args, **kwargs: None
            sys.modules["fitz"] = fitz_stub
        if "llm" not in sys.modules:
            import types

            llm_stub = types.ModuleType("llm")

            class DummyBltClient:
                def __init__(self, *args, **kwargs):
                    pass

            llm_stub.BltClient = DummyBltClient
            sys.modules["llm"] = llm_stub

        src_path = root / "src" / "6.generate_docs.py"
        spec = importlib.util.spec_from_file_location("gen6_mod", src_path)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cls.mod)

    def test_parse_meta_from_front_matter(self):
        with tempfile.TemporaryDirectory() as d:
            md_path = Path(d) / "paper.md"
            md_path.write_text(
                "\n".join(
                    [
                        "---",
                        "title: Attention Is All You Need",
                        "authors: \"Ashish Vaswani, Noam Shazeer\"",
                        "date: 20170612",
                        "pdf: \"https://arxiv.org/pdf/1706.03762v1\"",
                        "tags: [\"query:transformer\", \"query:attention\"]",
                        "selection_source: fresh_fetch",
                        "---",
                        "## Abstract",
                        "abstract body",
                    ]
                ),
                encoding="utf-8",
            )
            item = self.mod._parse_generated_md_to_meta(str(md_path), "pid", "quick")
            self.assertEqual(item["title_en"], "Attention Is All You Need")
            self.assertTrue(item["authors"].startswith("Ashish Vaswani"))
            self.assertIn("query:transformer", item["tags"])
            self.assertEqual(item["date"], "20170612")
            self.assertIn("https://arxiv.org/pdf", item["pdf"])
            self.assertEqual(item["selection_source"], "fresh_fetch")

    def test_parse_fallback_to_legacy_meta_lines(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "paper.md"
            path.write_text(
                "\n".join(
                    [
                        "---",
                        "selection_source: fresh_fetch",
                        "title: Legacy title",
                        "---",
                        "**Authors**: Legacy A, Legacy B",
                        "**Date**: 20260301",
                        "**PDF**: https://example.com/paper.pdf",
                        "**TLDR**: legacy tldr text",
                        "",
                        "## Abstract",
                        "abstract body",
                    ]
                ),
                encoding="utf-8",
            )
            item = self.mod._parse_generated_md_to_meta(
                str(path),
                "legacy",
                "deep",
                "cache_hint",
            )
            self.assertEqual(item["authors"], "Legacy A, Legacy B")
            self.assertEqual(item["date"], "20260301")
            self.assertEqual(item["pdf"], "https://example.com/paper.pdf")
            self.assertEqual(item["tldr"], "legacy tldr text")
            self.assertEqual(item["selection_source"], "cache_hint")

    def test_parse_source_from_front_matter(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "paper.md"
            path.write_text(
                "\n".join(
                    [
                        "---",
                        "title: Test title",
                        "source: biorxiv",
                        "selection_source: fresh_fetch",
                        "---",
                        "## Abstract",
                        "abstract body",
                    ]
                ),
                encoding="utf-8",
            )
            item = self.mod._parse_generated_md_to_meta(str(path), "pid", "quick")
            self.assertEqual(item["source"], "biorxiv")
            self.assertEqual(item["selection_source"], "fresh_fetch")

    def test_extract_sidebar_tags_hides_composite_suffix(self):
        paper = {
            "llm_score": 8.0,
            "llm_tags": [
                "query:sr:composite",
                "query:sr",
                "keyword:equation-discovery",
            ],
        }
        tags = self.mod.extract_sidebar_tags(paper)
        self.assertEqual(tags[0], ("score", "8.0"))
        self.assertIn(("query", "sr"), tags)
        self.assertIn(("query", "equation-discovery"), tags)
        self.assertNotIn(("query", "sr:composite"), tags)
        self.assertEqual(tags.count(("query", "sr")), 1)

    def test_update_sidebar_writes_chinese_title_payload(self):
        with tempfile.TemporaryDirectory() as d:
            sidebar_path = Path(d) / "_sidebar.md"
            sidebar_path.write_text("* Daily Papers\n", encoding="utf-8")

            self.mod.update_sidebar(
                str(sidebar_path),
                "20260525-20260525",
                [("20260525-20260525/paper-id", "English Paper Title", [("score", "8.6")])],
                [],
                {"20260525-20260525/paper-id": "一句中文入选理由。"},
                paper_title_zh_by_id={"20260525-20260525/paper-id": "中文论文标题"},
            )

            content = sidebar_path.read_text(encoding="utf-8")
            self.assertIn("data-sidebar-item=", content)
            self.assertIn("&quot;title_zh&quot;: &quot;中文论文标题&quot;", content)
            self.assertIn("&quot;evidence&quot;: &quot;一句中文入选理由。&quot;", content)

    def test_build_markdown_content_writes_figures_json_front_matter(self):
        paper = {
            "title": "Figure Test",
            "authors": ["Ada Lovelace"],
            "published": "2026-03-26T00:00:00+00:00",
            "link": "https://arxiv.org/pdf/1234.5678",
            "abstract": "abstract body",
            "source": "arxiv",
            "_figure_assets": [
                {
                    "url": "assets/figures/arxiv/1234.5678/fig-001.webp",
                    "caption": "",
                    "page": 2,
                    "index": 1,
                    "width": 1280,
                    "height": 720,
                }
            ],
        }
        md = self.mod.build_markdown_content(paper, "quick", "", "", [])
        meta = self.mod._parse_front_matter(md)
        self.assertIn("figures_json", meta)
        figures = json.loads(meta["figures_json"])
        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0]["url"], "assets/figures/arxiv/1234.5678/fig-001.webp")

    def test_glance_only_new_page_writes_chinese_title(self):
        with tempfile.TemporaryDirectory() as d:
            original_translate = self.mod.translate_title_and_abstract_to_zh
            original_glance = self.mod.generate_glance_overview
            original_figures = self.mod.maybe_generate_paper_figures
            original_text = self.mod.ensure_text_content
            try:
                self.mod.translate_title_and_abstract_to_zh = lambda title, abstract: ("中文标题", "中文摘要")
                self.mod.generate_glance_overview = lambda title, abstract: (
                    "**TLDR**: 这是一句简短总结。\n"
                    "**Motivation**: 这是一句简短动机。\n"
                    "**Method**: 这是一句简短方法。\n"
                    "**Result**: 这是一句简短结果。\n"
                    "**Conclusion**: 这是一句简短结论。"
                )
                self.mod.maybe_generate_paper_figures = lambda *args, **kwargs: []
                self.mod.ensure_text_content = lambda *args, **kwargs: "text"

                paper_id, _ = self.mod.process_paper(
                    {
                        "id": "2605.99999v1",
                        "title": "English Title",
                        "authors": ["Ada Lovelace"],
                        "published": "2026-05-25T00:00:00+00:00",
                        "link": "https://arxiv.org/pdf/2605.99999v1",
                        "abstract": "This paper studies superconducting qubits.",
                        "source": "arxiv",
                    },
                    "quick",
                    "20260525-20260525",
                    d,
                    glance_only=True,
                )
            finally:
                self.mod.translate_title_and_abstract_to_zh = original_translate
                self.mod.generate_glance_overview = original_glance
                self.mod.maybe_generate_paper_figures = original_figures
                self.mod.ensure_text_content = original_text

            md_path = Path(d) / paper_id.split("/", 1)[0] / (paper_id.split("/", 1)[1] + ".md")
            meta = self.mod._parse_front_matter(md_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["title_zh"], "中文标题")
            self.assertLessEqual(len(meta["evidence"]), 42)
            self.assertIn("## 摘要", md_path.read_text(encoding="utf-8"))

    def test_normalize_figure_assets_orders_by_paper_position(self):
        figures = self.mod.normalize_figure_assets(
            [
                {"figure_number": "4", "item_type": "figure", "page": 6, "index": 1},
                {"figure_number": "3", "item_type": "figure", "page": 7, "index": 2},
                {"figure_number": "5", "item_type": "figure", "page": 7, "index": 3},
                {"figure_number": "I", "item_type": "table", "page": 7, "index": 4},
            ]
        )

        self.assertEqual(
            [(item["item_type"], item["figure_number"]) for item in figures],
            [("figure", "4"), ("figure", "3"), ("figure", "5"), ("table", "I")],
        )

    def test_normalize_latex_escapes_repairs_double_backslashes_in_math(self):
        text = (
            r"fixed $\\theta=60^\\circ$ and "
            r"$w_{\\text{narrow}}=w_{\\text{open}}-\\frac{h\\sin\\phi}{\\tan\\theta}$"
        )

        fixed = self.mod.normalize_latex_escapes(text)

        self.assertIn(r"$\theta=60^\circ$", fixed)
        self.assertIn(r"\text{narrow}", fixed)
        self.assertIn(r"\frac{h\sin\phi}{\tan\theta}", fixed)
        self.assertNotIn(r"\\theta", fixed)

    def test_build_markdown_content_repairs_latex_escapes(self):
        paper = {
            "title": "Latex Test",
            "authors": ["Ada Lovelace"],
            "published": "2026-03-26T00:00:00+00:00",
            "abstract": r"uses $\\theta=60^\\circ$ in text",
            "source": "arxiv",
        }

        md = self.mod.build_markdown_content(
            paper,
            "quick",
            "",
            r"中文摘要 $w_{\\text{narrow}}$",
            [],
        )

        self.assertIn(r"$\theta=60^\circ$", md)
        self.assertIn(r"$w_{\text{narrow}}$", md)
        self.assertNotIn(r"\\theta", md)

    def test_maybe_generate_paper_figures_accepts_biorxiv(self):
        calls = []

        def fake_ensure_paper_figures(**kwargs):
            calls.append(kwargs)
            return [{"url": "assets/figures/biorxiv/pid/fig-001.webp"}]

        original = self.mod.ensure_paper_figures
        self.mod.ensure_paper_figures = fake_ensure_paper_figures
        try:
            figures = self.mod.maybe_generate_paper_figures(
                {
                    "id": "biorxiv-abc",
                    "source": "biorxiv",
                },
                docs_dir="docs",
                paper_id="202603/26/biorxiv-abc",
                pdf_url="https://www.biorxiv.org/content/test.full.pdf",
            )
        finally:
            self.mod.ensure_paper_figures = original

        self.assertEqual(len(figures), 1)
        self.assertEqual(calls[0]["source_key"], "biorxiv")


if __name__ == "__main__":
    unittest.main()
