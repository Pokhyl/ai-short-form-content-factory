"""The image builder refuses to start without safe host disk headroom."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_factory_v3_image", ROOT / "scripts" / "build_factory_v3_image.py"
)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class BuildDiskGuardTests(unittest.TestCase):
    def test_refuses_low_disk_before_git_tempdir_or_docker(self):
        with patch.object(BUILDER.shutil, "disk_usage",
                          return_value=SimpleNamespace(free=BUILDER.MINIMUM_FREE_BYTES - 1)):
            with patch.object(BUILDER.subprocess, "check_output") as git:
                with patch.object(BUILDER.tempfile, "TemporaryDirectory") as tempdir:
                    with self.assertRaisesRegex(RuntimeError, "refusing image build"):
                        BUILDER.main(["--tag", "unused:test"])
                    git.assert_not_called()
                    tempdir.assert_not_called()

    def test_exact_minimum_headroom_is_allowed(self):
        with patch.object(BUILDER.shutil, "disk_usage",
                          return_value=SimpleNamespace(free=BUILDER.MINIMUM_FREE_BYTES)):
            self.assertEqual(
                BUILDER.require_disk_headroom(ROOT), BUILDER.MINIMUM_FREE_BYTES
            )


if __name__ == "__main__":
    unittest.main()
