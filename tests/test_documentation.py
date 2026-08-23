from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_human_and_agent_entrypoints_exist(self) -> None:
        expected = [
            "README.md",
            "README.zh-CN.md",
            "AGENTS.md",
            "llms.txt",
            "docs/zh-CN/operations.md",
            "docs/zh-CN/authoring.md",
            "docs/zh-CN/metrics.md",
        ]
        for relative in expected:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_local_markdown_links_resolve(self) -> None:
        for document in [ROOT / "README.md", ROOT / "README.zh-CN.md"]:
            text = document.read_text(encoding="utf-8")
            for target in LINK.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path = target.split("#", 1)[0]
                self.assertTrue((document.parent / path).resolve().exists(), f"{document}: {target}")

    def test_ai_entrypoints_preserve_hidden_test_boundary(self) -> None:
        for relative in ("AGENTS.md", "llms.txt"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("private/hidden-tests", text)
            self.assertIn("harnessbench prepare", text)
            self.assertIn("ShipReady", text)


if __name__ == "__main__":
    unittest.main()
