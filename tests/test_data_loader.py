"""Tests for dataio.data_loader.

Pins the benchmark schema so that if the underlying parquet ever changes
(or the wrong file gets loaded), the suite fails loudly instead of silently
producing wrong eval numbers.
"""
from pathlib import Path

import pytest
from PIL import Image

from dataio.data_loader import load_closed, decode_image

# Resolve data relative to the repo root, not the current working directory,
# so the tests pass no matter where pytest is invoked from.
REPO_ROOT = Path(__file__).resolve().parent.parent
CLOSED_PARQUET = REPO_ROOT / "data" / "closed_ended.parquet"

EXPECTED_COLUMNS = [
    "index", "image_id", "file_name", "question", "category",
    "image", "type", "option1", "option2", "option3", "option4", "answer",
]
OPTION_COLUMNS = ["option1", "option2", "option3", "option4"]
EXPECTED_ROWS = 491


@pytest.fixture(scope="function")
def closed_df():
    """Load the 113 MB parquet once per module instead of once per test."""
    return load_closed(CLOSED_PARQUET)


def test_columns_match_expected_schema(closed_df):
    assert list(closed_df.columns) == EXPECTED_COLUMNS


def test_row_count_is_full_benchmark(closed_df):
    assert len(closed_df) == EXPECTED_ROWS


def test_option_columns_have_no_nan(closed_df):
    """Blank options must be the literal string "None", never NaN.

    A NaN here would be rendered to the model as the answer choice "nan",
    which corrupts results without raising anything.
    """
    n_nan = int(closed_df[OPTION_COLUMNS].isna().sum().sum())
    assert n_nan == 0, f"{n_nan} NaN option cell(s) — wrong (non-normalized) parquet?"


def test_decode_image_returns_usable_image(closed_df):
    img = decode_image(closed_df.iloc[0]["image"])
    assert isinstance(img, Image.Image)
    width, height = img.size
    assert width > 0 and height > 0



