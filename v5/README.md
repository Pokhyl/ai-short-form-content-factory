# V5 clean core

This directory contains only the thin V5 product adapter around pinned mature editing tools.

It must not import `prototype.v4` or the old Studio V4 runtime.

The first executable is `preflight.py`. It verifies the exact upstream pin and the real editing/provider/timing capabilities before any V5 director or Studio service is built.
