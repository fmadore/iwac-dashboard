#!/usr/bin/env python3
"""
Unit tests for IWAC Shared Utilities (iwac_utils.py)

Run with: python -m pytest test_iwac_utils.py -v
"""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from iwac_utils import (
    DATASET_ID,
    SUBSETS,
    configure_logging,
    copy_to_build,
    create_metadata_block,
    extract_month,
    extract_year,
    find_column,
    generate_timestamp,
    load_dataset_safe,
    normalize_country,
    normalize_location_name,
    parse_coordinates,
    parse_multi_value,
    parse_pipe_separated,
    save_json,
)


# =============================================================================
# Test normalize_country
# =============================================================================

class TestNormalizeCountry:
    """Tests for normalize_country function."""

    def test_single_country_string(self):
        assert normalize_country("Benin") == ["Benin"]
        assert normalize_country("benin") == ["Benin"]
        assert normalize_country("BENIN") == ["Benin"]

    def test_pipe_separated_countries(self):
        result = normalize_country("Benin|Togo")
        assert result == ["Benin", "Togo"]

    def test_comma_separated_countries(self):
        result = normalize_country("Benin, Togo, Niger")
        assert result == ["Benin", "Togo", "Niger"]

    def test_semicolon_separated_countries(self):
        result = normalize_country("Benin; Togo")
        assert result == ["Benin", "Togo"]

    def test_slash_separated_countries(self):
        result = normalize_country("Benin/Togo")
        assert result == ["Benin", "Togo"]

    def test_none_value(self):
        assert normalize_country(None) == ["Unknown"]

    def test_nan_value(self):
        assert normalize_country(float("nan")) == ["Unknown"]

    def test_empty_string(self):
        assert normalize_country("") == ["Unknown"]
        assert normalize_country("   ") == ["Unknown"]

    def test_list_input(self):
        result = normalize_country(["benin", "togo"])
        assert result == ["Benin", "Togo"]

    def test_tuple_input(self):
        result = normalize_country(("benin", "togo"))
        assert result == ["Benin", "Togo"]

    def test_return_list_false(self):
        assert normalize_country("Benin", return_list=False) == "Benin"
        assert normalize_country("benin|togo", return_list=False) == "Benin, Togo"
        assert normalize_country(None, return_list=False) == "Unknown"

    def test_custom_unknown_value(self):
        assert normalize_country(None, unknown_value="N/A") == ["N/A"]


# =============================================================================
# Test normalize_location_name
# =============================================================================

class TestNormalizeLocationName:
    """Tests for normalize_location_name function."""

    def test_basic_normalization(self):
        assert normalize_location_name("Abidjan") == "abidjan"
        assert normalize_location_name("  Abidjan  ") == "abidjan"

    def test_unicode_normalization(self):
        # NFC normalized
        result = normalize_location_name("Côte d'Ivoire")
        assert result == "côte d'ivoire"

    def test_empty_input(self):
        assert normalize_location_name("") == ""
        assert normalize_location_name(None) == ""


# =============================================================================
# Test extract_year
# =============================================================================

class TestExtractYear:
    """Tests for extract_year function."""

    def test_iso_date_string(self):
        assert extract_year("2023-05-15") == 2023
        assert extract_year("2023-01-01") == 2023

    def test_year_only_string(self):
        assert extract_year("2023") == 2023

    def test_datetime_object(self):
        dt = datetime(2023, 5, 15)
        assert extract_year(dt) == 2023

    def test_pandas_timestamp(self):
        ts = pd.Timestamp("2023-05-15")
        assert extract_year(ts) == 2023

    def test_integer_year(self):
        assert extract_year(2023) == 2023

    def test_float_year(self):
        assert extract_year(2023.0) == 2023

    def test_none_value(self):
        assert extract_year(None) is None

    def test_nan_value(self):
        assert extract_year(float("nan")) is None

    def test_invalid_string(self):
        assert extract_year("invalid") is None
        assert extract_year("abc") is None

    def test_year_out_of_range(self):
        assert extract_year(1500) is None  # Below min_year
        assert extract_year(2500) is None  # Above max_year

    def test_custom_year_range(self):
        assert extract_year(1700, min_year=1600, max_year=1800) == 1700
        assert extract_year(1700, min_year=1800, max_year=2100) is None

    def test_embedded_year_in_string(self):
        assert extract_year("Published in 2023") == 2023
        assert extract_year("Article from 1999") == 1999


# =============================================================================
# Test extract_month
# =============================================================================

class TestExtractMonth:
    """Tests for extract_month function."""

    def test_iso_date_string(self):
        assert extract_month("2023-05-15") == "2023-05"
        assert extract_month("2023-01-01") == "2023-01"

    def test_datetime_object(self):
        dt = datetime(2023, 5, 15)
        assert extract_month(dt) == "2023-05"

    def test_pandas_timestamp(self):
        ts = pd.Timestamp("2023-05-15")
        assert extract_month(ts) == "2023-05"

    def test_none_value(self):
        assert extract_month(None) is None

    def test_nan_value(self):
        assert extract_month(float("nan")) is None

    def test_empty_string(self):
        assert extract_month("") is None
        assert extract_month("   ") is None

    def test_invalid_string(self):
        assert extract_month("invalid") is None


# =============================================================================
# Test parse_coordinates
# =============================================================================

class TestParseCoordinates:
    """Tests for parse_coordinates function."""

    def test_valid_coordinates_with_space(self):
        result = parse_coordinates("12.34, -56.78")
        assert result == (12.34, -56.78)

    def test_valid_coordinates_without_space(self):
        result = parse_coordinates("12.34,-56.78")
        assert result == (12.34, -56.78)

    def test_negative_coordinates(self):
        result = parse_coordinates("-12.34, -56.78")
        assert result == (-12.34, -56.78)

    def test_integer_coordinates(self):
        result = parse_coordinates("12, -56")
        assert result == (12.0, -56.0)

    def test_invalid_latitude(self):
        assert parse_coordinates("95.0, 0") is None  # > 90

    def test_invalid_longitude(self):
        assert parse_coordinates("0, 185.0") is None  # > 180

    def test_none_value(self):
        assert parse_coordinates(None) is None

    def test_empty_string(self):
        assert parse_coordinates("") is None
        assert parse_coordinates("   ") is None

    def test_invalid_format(self):
        assert parse_coordinates("invalid") is None
        assert parse_coordinates("12.34") is None


# =============================================================================
# Test parse_pipe_separated
# =============================================================================

class TestParsePipeSeparated:
    """Tests for parse_pipe_separated function."""

    def test_pipe_separated_values(self):
        result = parse_pipe_separated("value1|value2|value3")
        assert result == ["value1", "value2", "value3"]

    def test_trimming(self):
        result = parse_pipe_separated(" value1 | value2 | value3 ")
        assert result == ["value1", "value2", "value3"]

    def test_empty_values_filtered(self):
        result = parse_pipe_separated("value1||value3")
        assert result == ["value1", "value3"]

    def test_list_input(self):
        result = parse_pipe_separated(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_none_value(self):
        assert parse_pipe_separated(None) == []

    def test_nan_value(self):
        assert parse_pipe_separated(float("nan")) == []

    def test_empty_string(self):
        assert parse_pipe_separated("") == []


# =============================================================================
# Test parse_multi_value
# =============================================================================

class TestParseMultiValue:
    """Tests for parse_multi_value function."""

    def test_pipe_separator(self):
        assert parse_multi_value("a|b|c") == ["a", "b", "c"]

    def test_comma_separator(self):
        assert parse_multi_value("a,b,c") == ["a", "b", "c"]

    def test_semicolon_separator(self):
        assert parse_multi_value("a;b;c") == ["a", "b", "c"]

    def test_slash_separator(self):
        assert parse_multi_value("a/b/c") == ["a", "b", "c"]

    def test_single_value(self):
        assert parse_multi_value("single") == ["single"]

    def test_none_value(self):
        assert parse_multi_value(None) == []


# =============================================================================
# Test find_column
# =============================================================================

class TestFindColumn:
    """Tests for find_column function."""

    def test_finds_first_match(self):
        df = pd.DataFrame({"title": [1], "Title": [2]})
        assert find_column(df, ["title", "Title"]) == "title"

    def test_finds_second_candidate(self):
        df = pd.DataFrame({"Title": [1]})
        assert find_column(df, ["title", "Title"]) == "Title"

    def test_returns_none_when_not_found(self):
        df = pd.DataFrame({"other": [1]})
        assert find_column(df, ["title", "Title"]) is None

    def test_required_raises_error(self):
        df = pd.DataFrame({"other": [1]})
        with pytest.raises(ValueError, match="Required column not found"):
            find_column(df, ["title"], required=True)


# =============================================================================
# Test save_json
# =============================================================================

class TestSaveJson:
    """Tests for save_json function."""

    def test_save_json_pretty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"key": "value", "number": 42}
            save_json(data, path, log=False)

            assert path.exists()
            with path.open() as f:
                loaded = json.load(f)
            assert loaded == data

    def test_save_json_minified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"key": "value"}
            save_json(data, path, minify=True, log=False)

            content = path.read_text()
            # Minified JSON has no spaces after colons
            assert content == '{"key":"value"}'

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "test.json"
            save_json({"key": "value"}, path, log=False)
            assert path.exists()


# =============================================================================
# Test copy_to_build
# =============================================================================

class TestCopyToBuild:
    """Tests for copy_to_build function."""

    def test_copies_when_build_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.json"
            build_dir = Path(tmpdir) / "build"
            build_dir.mkdir()

            src.write_text('{"key": "value"}')
            result = copy_to_build(src, build_dir)

            assert result is True
            assert (build_dir / "src.json").exists()

    def test_returns_false_when_build_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.json"
            src.write_text('{"key": "value"}')

            build_dir = Path(tmpdir) / "nonexistent"
            result = copy_to_build(src, build_dir)

            assert result is False


# =============================================================================
# Test load_dataset_safe
# =============================================================================

class TestLoadDatasetSafe:
    """Tests for load_dataset_safe function."""

    @patch("iwac_utils.hf_load_dataset")
    def test_successful_load(self, mock_load):
        mock_df = pd.DataFrame({"col": [1, 2, 3]})
        mock_dataset = MagicMock()
        mock_dataset.__getitem__.return_value.to_pandas.return_value = mock_df
        mock_load.return_value = mock_dataset

        result = load_dataset_safe("articles")

        assert result is not None
        assert len(result) == 3
        mock_load.assert_called_once()

    @patch("iwac_utils.hf_load_dataset")
    def test_failed_load_returns_none(self, mock_load):
        mock_load.side_effect = Exception("Network error")

        result = load_dataset_safe("articles")

        assert result is None


# =============================================================================
# Test generate_timestamp
# =============================================================================

class TestGenerateTimestamp:
    """Tests for generate_timestamp function."""

    def test_returns_iso_format_with_z(self):
        ts = generate_timestamp()
        assert ts.endswith("Z")
        # Should be parseable
        datetime.fromisoformat(ts.replace("Z", "+00:00"))


# =============================================================================
# Test create_metadata_block
# =============================================================================

class TestCreateMetadataBlock:
    """Tests for create_metadata_block function."""

    def test_basic_metadata(self):
        meta = create_metadata_block(1000)
        assert meta["totalRecords"] == 1000
        assert meta["dataSource"] == DATASET_ID
        assert "generatedAt" in meta

    def test_extra_fields(self):
        meta = create_metadata_block(1000, countries=["Benin", "Togo"])
        assert meta["countries"] == ["Benin", "Togo"]

    def test_custom_data_source(self):
        meta = create_metadata_block(100, data_source="custom/dataset")
        assert meta["dataSource"] == "custom/dataset"


# =============================================================================
# Test constants
# =============================================================================

class TestConstants:
    """Tests for module constants."""

    def test_dataset_id(self):
        assert DATASET_ID == "fmadore/islam-west-africa-collection"

    def test_subsets_list(self):
        assert "articles" in SUBSETS
        assert "index" in SUBSETS
        assert len(SUBSETS) == 6


# =============================================================================
# Test configure_logging
# =============================================================================

class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_returns_logger(self):
        logger = configure_logging()
        assert isinstance(logger, logging.Logger)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
