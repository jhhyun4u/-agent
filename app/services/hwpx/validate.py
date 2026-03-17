"""HWPX 구조 무결성 검증.

원본: Canine89/hwpxskill/scripts/validate.py
서비스 모듈로 래핑 — CLI argparse 제거, 함수 API만 노출.
"""

from pathlib import Path
from zipfile import ZIP_STORED, BadZipFile, ZipFile

from lxml import etree

REQUIRED_FILES = [
    "mimetype",
    "Contents/content.hpf",
    "Contents/header.xml",
    "Contents/section0.xml",
]

EXPECTED_MIMETYPE = "application/hwp+zip"


def validate_hwpx(hwpx_path: str | Path) -> list[str]:
    """HWPX 파일 구조 검증. 빈 리스트 반환 시 유효."""
    errors: list[str] = []
    path = Path(hwpx_path)

    if not path.is_file():
        return [f"파일 없음: {hwpx_path}"]

    try:
        zf = ZipFile(path, "r")
    except BadZipFile:
        return [f"유효하지 않은 ZIP: {hwpx_path}"]

    with zf:
        names = zf.namelist()

        for required in REQUIRED_FILES:
            if required not in names:
                errors.append(f"필수 파일 누락: {required}")

        if "mimetype" in names:
            mimetype_content = zf.read("mimetype").decode("utf-8").strip()
            if mimetype_content != EXPECTED_MIMETYPE:
                errors.append(
                    f"잘못된 mimetype: '{EXPECTED_MIMETYPE}' 기대, "
                    f"'{mimetype_content}' 발견"
                )

            if names[0] != "mimetype":
                errors.append(
                    f"mimetype이 첫 번째 ZIP 엔트리가 아님 "
                    f"(인덱스 {names.index('mimetype')})"
                )

            info = zf.getinfo("mimetype")
            if info.compress_type != ZIP_STORED:
                errors.append(
                    f"mimetype은 ZIP_STORED(0)이어야 함, "
                    f"compress_type={info.compress_type}"
                )

        for name in names:
            if name.endswith(".xml") or name.endswith(".hpf"):
                try:
                    data = zf.read(name)
                    etree.fromstring(data)
                except etree.XMLSyntaxError as e:
                    errors.append(f"XML 구문 오류 ({name}): {e}")

    return errors
