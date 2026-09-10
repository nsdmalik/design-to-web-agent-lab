import json
from pathlib import Path
import tempfile
import unittest
from workflow import ReplayProvider, run, validate_page, parse_object, ValidationError

BRIEF = {
    "name": "Field Notes",
    "audience": "Makers",
    "goal": "Explain a prototype workshop",
}


class WorkflowTests(unittest.TestCase):
    def files(self):
        return json.loads(ReplayProvider()("build", {}))

    def test_valid_sample(self):
        self.assertEqual(validate_page(self.files()), [])

    def test_scripts_handlers_and_remote_resources_fail(self):
        for fragment in [
            "<script>alert(1)</script>",
            '<img src="https://example.com/x">',
            '<div onclick="x()">x</div>',
            "<iframe></iframe>",
            "<form></form>",
            '<meta http-equiv="refresh" content="0;https://example.com">',
        ]:
            files = self.files()
            files["index.html"] += fragment
            self.assertTrue(validate_page(files))

    def test_css_network_escapes_are_rejected(self):
        for css in [
            "a{background:url(https://example.com/x)}",
            '@import "x.css"',
            "a{color:\\72 ed}",
        ]:
            files = self.files()
            files["style.css"] = css
            self.assertTrue(validate_page(files))

    def test_arbitrary_paths_rejected(self):
        self.assertTrue(validate_page({"../secret": "x"}))

    def test_anchor_and_heading_requirements(self):
        files = self.files()
        files["index.html"] = files["index.html"].replace('id="program"', 'id="other"')
        self.assertTrue(validate_page(files))

    def test_offline_run_has_review_gate_and_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            result = run(BRIEF, ReplayProvider(), out, "replay")
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(result["provider"], "replay")
            self.assertTrue((out / "preview/index.html").exists())
            with self.assertRaises(FileExistsError):
                run(BRIEF, ReplayProvider(), out)

    def test_single_bounded_repair(self):
        calls = []

        def provider(stage, payload):
            calls.append(stage)
            if stage == "plan":
                return ReplayProvider()(stage, payload)
            if stage == "build":
                return json.dumps(
                    {"index.html": "<script>x</script>", "style.css": "a{}"}
                )
            return ReplayProvider()(stage, payload)

        with tempfile.TemporaryDirectory() as d:
            result = run(BRIEF, provider, Path(d) / "run")
        self.assertEqual(calls, ["plan", "build", "repair"])
        self.assertEqual(result["status"], "review_required")

    def test_failed_validation_never_writes_preview(self):
        def provider(stage, payload):
            return (
                ReplayProvider()(stage, payload)
                if stage == "plan"
                else '{"index.html":"bad","style.css":""}'
            )

        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            with self.assertRaises(ValidationError):
                run(BRIEF, provider, out)
            self.assertFalse((out / "preview").exists())
            self.assertEqual(
                json.loads((out / "run.json").read_text())["status"], "failed"
            )

    def test_invalid_json_and_plan_fail(self):
        for value in ["nope", "[]"]:
            with self.assertRaises(ValidationError):
                parse_object(value)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValidationError):
                run(BRIEF, lambda stage, payload: "{}", Path(d) / "run")

    def test_brief_validation(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValidationError):
                run({"name": "x"}, ReplayProvider(), Path(d) / "run")


if __name__ == "__main__":
    unittest.main()
