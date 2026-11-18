#!/usr/bin/env python3
"""news-image-20261118 entry.

Copies the committed entry.png (a code-drawn one-image summary of
18 November 2026 world news) to /output/entry.png. Pure stdlib,
fully deterministic: the same input file always yields identical
output bytes.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = "/output"
DST = os.path.join(DST_DIR, "entry.png")


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    shutil.copyfile(SRC, DST)


if __name__ == "__main__":
    main()
