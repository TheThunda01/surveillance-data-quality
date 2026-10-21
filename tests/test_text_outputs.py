"""Generated reports must retain portable UTF-8 bytes and valid SVG XML."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class TextOutputTests(unittest.TestCase):
    def test_public_cli_emits_utf8_report_and_parseable_svg(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'public'
            result = subprocess.run(
                [sys.executable, str(ROOT / 'src/public_audit.py'), '--output', str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            svg_bytes = (output / 'weekly_positivity.svg').read_bytes()
            svg_text = svg_bytes.decode('utf-8')
            self.assertIn('positivity · pinned CDC extract', svg_text)
            root = ET.fromstring(svg_bytes)
            self.assertEqual(root.tag, '{http://www.w3.org/2000/svg}svg')
            report = (output / 'report.md').read_bytes().decode('utf-8')
            self.assertIn('2026-01-03–2026-10-10', report)
            for filename in ('report.md', 'weekly_positivity.svg', 'audit.json'):
                self.assertNotIn(b'\r\n', (output / filename).read_bytes())
            audit = json.loads((output / 'audit.json').read_text(encoding='utf-8'))
            self.assertEqual(audit['input_rows'], 123)

    def test_chart_uses_supplied_capture_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / 'synthetic-later-capture'
            output = Path(directory) / 'output'
            shutil.copytree(ROOT / 'data/public', snapshot)
            path = snapshot / 'manifest.json'
            manifest = json.loads(path.read_text(encoding='utf-8'))
            # Synthetic metadata change tests formatting; it is not a new CDC capture.
            manifest['retrieved_at_utc'] = '2026-10-21T12:00:00+00:00'
            path.write_text(json.dumps(manifest), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(ROOT / 'src/public_audit.py'), '--snapshot', str(snapshot), '--output', str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            chart = (output / 'weekly_positivity.svg').read_text(encoding='utf-8')
            self.assertIn('2026-01-03–2026-10-10. Retrieved 2026-10-21.', chart)
            self.assertNotIn('Retrieved Oct 20, 2026', chart)


if __name__ == '__main__':
    unittest.main()
