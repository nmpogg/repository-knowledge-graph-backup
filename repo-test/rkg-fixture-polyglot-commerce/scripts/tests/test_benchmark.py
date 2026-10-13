import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "corpus", Path(__file__).parents[1] / "benchmark-corpus.py"
)
corpus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(corpus)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = corpus.OUTPUT
        corpus.OUTPUT = Path(self.tmp.name) / ".benchmark" / "corpus"

    def tearDown(self):
        corpus.OUTPUT = self.previous
        self.tmp.cleanup()

    def fingerprint(self):
        return [
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(corpus.OUTPUT.iterdir())
        ]

    def test_deterministic_and_cleanup_is_scoped(self):
        outside = Path(self.tmp.name) / "keep.txt"
        outside.write_text("keep")
        corpus.generate(100)
        first = self.fingerprint()
        self.assertEqual(len(list(corpus.OUTPUT.glob("*.ts"))), 100)
        with self.assertRaises(ValueError):
            corpus.generate(100)
        corpus.cleanup()
        corpus.generate(100)
        self.assertEqual(first, self.fingerprint())
        corpus.cleanup()
        self.assertTrue(outside.exists())

    def test_refuses_invalid_size_and_symlink_cleanup(self):
        with self.assertRaises(ValueError):
            corpus.generate(99)
        corpus.OUTPUT.parent.mkdir()
        target = Path(self.tmp.name) / "outside"
        target.mkdir()
        corpus.OUTPUT.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            corpus.cleanup()
        self.assertTrue(target.exists())

    def test_large_profile_is_not_executed(self):
        for count in (1000, 9000):
            corpus.generate(count, 42)
            self.assertEqual(len(list(corpus.OUTPUT.glob("*.ts"))), count)
            corpus.cleanup()
