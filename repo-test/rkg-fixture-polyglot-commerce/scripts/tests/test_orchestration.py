import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class OrchestrationTests(unittest.TestCase):
    def test_first_component_failure_preserves_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "npm"
            stub.write_text("#!/bin/sh\nexit 37\n")
            stub.chmod(0o755)
            env = dict(os.environ, PATH=tmp + os.pathsep + os.environ["PATH"])
            result = subprocess.run(
                ["sh", str(ROOT / "scripts/verify-all")],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 37)
            self.assertNotIn("All components", result.stdout)
