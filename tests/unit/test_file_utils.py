"""Unit tests for file utilities (U-FU-*)"""

import pytest
from app.utils.file_utils import (
    get_extension,
    validate_extension,
    sanitize_filename,
    validate_file_size,
    FileFormatError,
    FileSizeExceededError,
    InvalidRequestError,
)


class TestExtensionHandling:
    """Tests for extension extraction and validation"""

    def test_ufu_01_normal_filename(self):
        """U-FU-01: Normal filename extension"""
        assert get_extension("document.pdf") == "pdf"

    def test_ufu_02_mixed_case(self):
        """U-FU-02: Mixed case extension normalized to lowercase"""
        assert get_extension("Report.PDF") == "pdf"
        assert get_extension("FILE.DocX") == "docx"

    def test_ufu_03_no_extension(self):
        """U-FU-03: No extension returns empty string"""
        assert get_extension("nodotfile") == ""

    def test_ufu_04_multiple_dots(self):
        """U-FU-04: Multiple dots - extract last segment"""
        assert get_extension("my.document.docx") == "docx"
        assert get_extension("file.tar.gz") == "gz"

    def test_ufu_05_valid_extension(self):
        """U-FU-05: Valid extension for category returns extension"""
        result = validate_extension("report.pdf", "intranet_doc")
        assert result == "pdf"

    def test_ufu_06_invalid_extension(self):
        """U-FU-06: Invalid extension raises FileFormatError"""
        with pytest.raises(FileFormatError):
            validate_extension("virus.exe", "intranet_doc")

    def test_ufu_07_unknown_category(self):
        """U-FU-07: Unknown category raises ValueError"""
        with pytest.raises(ValueError):
            validate_extension("file.pdf", "unknown_category")

    def test_ufu_08_allowed_extensions_intranet(self):
        """U-FU-08: All intranet_doc extensions work"""
        for ext in ["pdf", "docx", "hwp", "hwpx", "xlsx", "pptx", "txt"]:
            filename = f"test.{ext}"
            result = validate_extension(filename, "intranet_doc")
            assert result == ext


class TestFilenameHandling:
    """Tests for filename sanitization"""

    def test_ufu_09_normal_filename_pass(self):
        """U-FU-09: Normal filename passes unchanged"""
        result = sanitize_filename("my doc.pdf")
        assert result == "my doc.pdf"

    def test_ufu_10_path_traversal_blocked(self):
        """U-FU-10: Path traversal sequences stripped"""
        result = sanitize_filename("../../etc/passwd")
        # Should only keep the basename
        assert ".." not in result
        assert "/" not in result

    def test_ufu_11_dot_prefix_rejected(self):
        """U-FU-11: Dot-prefix filenames raise InvalidRequestError"""
        with pytest.raises(InvalidRequestError):
            sanitize_filename(".hidden")

    def test_ufu_12_none_input_fallback(self):
        """U-FU-12: None input uses 'upload' fallback"""
        result = sanitize_filename(None)
        assert result == "upload"

    def test_ufu_13_empty_string_fallback(self):
        """U-FU-13: Empty string uses 'upload' fallback"""
        result = sanitize_filename("")
        assert result == "upload"

    def test_ufu_14_whitespace_stripped(self):
        """U-FU-14: Leading/trailing whitespace stripped"""
        result = sanitize_filename("  myfile.txt  ")
        assert result == "myfile.txt"


class TestFileSizeValidation:
    """Tests for file size checking"""

    def test_ufu_15_within_limit_pass(self):
        """U-FU-15: Within limit passes silently"""
        # Should not raise
        validate_file_size(b"x" * 1024 * 1024, max_mb=10)

    def test_ufu_16_at_limit_boundary(self):
        """U-FU-16: Exactly at limit passes"""
        # 10MB exactly
        validate_file_size(b"x" * (10 * 1024 * 1024), max_mb=10)

    def test_ufu_17_over_limit_raises(self):
        """U-FU-17: Over limit raises FileSizeExceededError"""
        with pytest.raises(FileSizeExceededError):
            # 11MB > 10MB limit
            validate_file_size(b"x" * (11 * 1024 * 1024), max_mb=10)

    def test_ufu_18_zero_bytes_pass(self):
        """U-FU-18: Zero-byte file passes"""
        validate_file_size(b"", max_mb=10)
