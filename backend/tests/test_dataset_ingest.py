from __future__ import annotations

import pandas as pd
import pytest

from app.services.dataset_ingest_service import DatasetIngestService


@pytest.mark.parametrize("encoding", ["utf-8", "gbk"])
def test_parse_file_with_csv(tmp_path, encoding):
    df = pd.DataFrame({"num": [1, 2], "txt": ["hello", "world"]})
    file_path = tmp_path / f"data_{encoding}.csv"
    df.to_csv(file_path, index=False, encoding=encoding)

    parsed = DatasetIngestService.parse_file(file_path, "csv")
    pd.testing.assert_frame_equal(parsed, df)


def test_parse_file_with_xlsx(tmp_path):
    df = pd.DataFrame({"num": [1, 2], "txt": ["a", "b"]})
    file_path = tmp_path / "data.xlsx"
    df.to_excel(file_path, index=False)

    parsed = DatasetIngestService.parse_file(file_path, "xlsx")
    pd.testing.assert_frame_equal(parsed, df, check_dtype=False)


def test_materialize_canonical_csv_creates_correct_output(tmp_path):
    df = pd.DataFrame({"num": [1, 2], "txt": ["a", "b"]})
    target_path = tmp_path / "nested" / "canonical.csv"

    DatasetIngestService.materialize_canonical_csv(df, target_path)

    assert target_path.exists()
    content = target_path.read_text(encoding="utf-8").splitlines()
    assert content[0] == '"num","txt"'
    roundtrip = pd.read_csv(target_path, encoding="utf-8")
    pd.testing.assert_frame_equal(roundtrip, df, check_dtype=False)


def test_infer_columns_returns_correct_dtypes():
    df = pd.DataFrame(
        {
            "num": list(range(1, 11)),
            "cat": ["a"] * 9 + ["b"],
            "text": [f"t{i}" for i in range(10)],
            "dt": pd.to_datetime([f"2020-01-{i + 1:02d}" for i in range(10)]),
        }
    )

    cols = DatasetIngestService.infer_columns(df)
    by_name = {c["name"]: c for c in cols}

    assert by_name["num"]["dtype"] == "numeric"
    assert by_name["cat"]["dtype"] == "categorical"
    assert by_name["text"]["dtype"] == "text"
    assert by_name["dt"]["dtype"] == "datetime"
    assert by_name["num"]["position"] == 0
    assert by_name["cat"]["null_count"] == 0
    assert by_name["cat"]["unique_count"] == 2


@pytest.mark.parametrize(
    "series,expected",
    [
        (pd.Series([1, 2, 3]), "numeric"),
        (pd.Series(pd.to_datetime(["2020-01-01", "2020-01-02"])), "datetime"),
        (pd.Series(["a"] * 9 + ["b"]), "categorical"),
        (pd.Series(["a", "b", "c", "d"]), "text"),
        (pd.Series([], dtype="object"), "text"),
    ],
)
def test_infer_dtype_edge_cases(series, expected):
    assert DatasetIngestService._infer_dtype(series) == expected


def test_infer_dtype_ratio_boundary_is_text():
    series = pd.Series(["a", "a", "b", "b"])  # 2/4 = 0.5 => not < 0.5 => text
    assert DatasetIngestService._infer_dtype(series) == "text"
