"""템플릿 기반 HWPX 조립.

원본: Canine89/hwpxskill/scripts/build_hwpx.py
서비스 모듈로 래핑 — CLI argparse 제거, 함수 API만 노출.

기능:
1. 기본 템플릿 복사
2. 문서 유형 템플릿 오버레이 (proposal, gonmun, report, minutes)
3. header.xml / section0.xml 커스텀 오버라이드
4. 메타데이터 설정 (title, creator)
5. XML 무결성 검증
6. HWPX 패키징 (mimetype first, ZIP_STORED)
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree

# 템플릿 경로: 이 모듈과 같은 디렉토리의 templates/
_MODULE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = _MODULE_DIR / "templates"
BASE_DIR = TEMPLATES_DIR / "base"

AVAILABLE_TEMPLATES = ["gonmun", "report", "minutes", "proposal"]


def _validate_xml(filepath: Path) -> None:
    """XML 무결성 검증. 오류 시 ValueError 발생."""
    try:
        etree.parse(str(filepath))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"XML 구문 오류 ({filepath.name}): {e}")


def _update_metadata(
    content_hpf: Path,
    title: str | None,
    creator: str | None,
) -> None:
    """content.hpf 메타데이터 업데이트."""
    if not title and not creator:
        return

    tree = etree.parse(str(content_hpf))
    root = tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf/"}

    if title:
        title_el = root.find(".//opf:title", ns)
        if title_el is not None:
            title_el.text = title

    now = datetime.now(timezone.utc)
    iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for meta in root.findall(".//opf:meta", ns):
        name = meta.get("name", "")
        if creator and name == "creator":
            meta.text = creator
        elif creator and name == "lastsaveby":
            meta.text = creator
        elif name == "CreatedDate":
            meta.text = iso_now
        elif name == "ModifiedDate":
            meta.text = iso_now
        elif name == "date":
            meta.text = now.strftime("%Y년 %m월 %d일")

    etree.indent(root, space="  ")
    tree.write(
        str(content_hpf),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def _pack_hwpx(input_dir: Path, output_path: Path) -> None:
    """HWPX 아카이브 생성 (mimetype first, ZIP_STORED)."""
    mimetype_file = input_dir / "mimetype"
    if not mimetype_file.is_file():
        raise FileNotFoundError(f"mimetype 파일 없음: {input_dir}")

    all_files = sorted(
        p.relative_to(input_dir).as_posix()
        for p in input_dir.rglob("*")
        if p.is_file()
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zf:
        zf.write(mimetype_file, "mimetype", compress_type=ZIP_STORED)
        for rel_path in all_files:
            if rel_path == "mimetype":
                continue
            zf.write(input_dir / rel_path, rel_path, compress_type=ZIP_DEFLATED)


def build_from_template(
    output_path: str | Path,
    template: str | None = None,
    header_override: str | Path | None = None,
    section_override: str | Path | None = None,
    title: str | None = None,
    creator: str | None = None,
) -> Path:
    """템플릿 기반 HWPX 조립.

    Args:
        output_path: 출력 .hwpx 파일 경로
        template: 문서 유형 템플릿 ('proposal', 'gonmun', 'report', 'minutes')
        header_override: 커스텀 header.xml 경로
        section_override: 커스텀 section0.xml 경로
        title: 문서 제목 (content.hpf 메타데이터)
        creator: 작성자 (content.hpf 메타데이터)

    Returns:
        생성된 HWPX 파일 경로

    Raises:
        FileNotFoundError: 기본 템플릿이 없을 때
        ValueError: XML 무결성 오류
    """
    output = Path(output_path)

    if not BASE_DIR.is_dir():
        raise FileNotFoundError(f"기본 템플릿 없음: {BASE_DIR}")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "build"

        # 1. 기본 템플릿 복사
        shutil.copytree(BASE_DIR, work)

        # 2. 문서 유형 오버레이
        if template:
            overlay_dir = TEMPLATES_DIR / template
            if not overlay_dir.is_dir():
                raise FileNotFoundError(
                    f"템플릿 '{template}' 없음. "
                    f"사용 가능: {', '.join(AVAILABLE_TEMPLATES)}"
                )
            for overlay_file in overlay_dir.iterdir():
                if overlay_file.is_file() and overlay_file.suffix == ".xml":
                    dest = work / "Contents" / overlay_file.name
                    shutil.copy2(overlay_file, dest)

        # 3. 커스텀 오버라이드
        if header_override:
            header_path = Path(header_override)
            if not header_path.is_file():
                raise FileNotFoundError(f"header 파일 없음: {header_override}")
            shutil.copy2(header_path, work / "Contents" / "header.xml")

        if section_override:
            section_path = Path(section_override)
            if not section_path.is_file():
                raise FileNotFoundError(f"section 파일 없음: {section_override}")
            shutil.copy2(section_path, work / "Contents" / "section0.xml")

        # 4. 메타데이터 업데이트
        _update_metadata(work / "Contents" / "content.hpf", title, creator)

        # 5. XML 무결성 검증
        for xml_file in work.rglob("*.xml"):
            _validate_xml(xml_file)
        for hpf_file in work.rglob("*.hpf"):
            _validate_xml(hpf_file)

        # 6. 패키징
        _pack_hwpx(work, output)

    return output


def validate_output(hwpx_path: str | Path) -> list[str]:
    """생성된 HWPX의 빠른 구조 검증."""
    from app.services.hwpx.validate import validate_hwpx
    return validate_hwpx(hwpx_path)
