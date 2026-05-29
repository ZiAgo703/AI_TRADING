"""아침 분석 파이프라인 실행기.

실행 방법:
    python scheduler/morning_runner.py          # 직접 실행
    python -m scheduler.morning_runner          # 모듈로 실행

Windows 작업 스케줄러 또는 cron 등록 가능.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (직접 실행 시)
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.analysis.stock_analyzer import StockAnalyzer
from src.report.report_writer import ReportWriter
from app.data.kor_fetcher import get_market_indices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("morning_runner")

_CONFIG_DIR   = _ROOT / "configs"
_OUTPUT_ROOT  = _ROOT / "output"
_OUTPUT_DIR   = _OUTPUT_ROOT / "latest"
_INDICES_PATH = _OUTPUT_DIR / "market_indices.json"
_RANK_JSON    = _OUTPUT_DIR / "all_stock_rank.json"


# ── 지수 저장 ─────────────────────────────────────────────────────────────────

def _save_indices(indices: dict) -> None:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "indices": indices,
    }
    with open(_INDICES_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("지수 저장 완료: %s", _INDICES_PATH)


def _load_indices() -> dict:
    """기존 저장된 지수 데이터 로드 (폴백용)."""
    if _INDICES_PATH.exists():
        with open(_INDICES_PATH, encoding="utf-8") as f:
            return json.load(f).get("indices", {})
    return {}


# ── 종목 분석 폴백 ────────────────────────────────────────────────────────────

def _last_rank_exists() -> bool:
    return _RANK_JSON.exists()


def _stamp_last_rank_as_stale() -> None:
    """기존 JSON에 stale 플래그와 타임스탬프를 추가해 대시보드가 오래된 데이터임을 표시."""
    if not _RANK_JSON.exists():
        return
    with open(_RANK_JSON, encoding="utf-8") as f:
        data = json.load(f)
    data["stale"] = True
    data["last_run_failed_at"] = datetime.now().isoformat()
    with open(_RANK_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.warning("기존 분석 결과를 stale 상태로 표시 (대시보드에 경고 표시됨)")


# ── 메인 파이프라인 ───────────────────────────────────────────────────────────

def run() -> bool:
    """아침 파이프라인 실행. 성공 시 True, 실패 시 False 반환."""
    logger.info("=" * 52)
    logger.info("아침 분석 파이프라인 시작  %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 52)
    start_time = datetime.now()

    # 1. KOSPI / KOSDAQ 지수 수집 (KRX 로그인 불필요 — pykrx 공개 API)
    try:
        indices = get_market_indices()
        if indices:
            for name, data in indices.items():
                sign = "+" if data["change_pct"] >= 0 else ""
                logger.info(
                    "%-8s  %.2f  (%s%.2f%%)",
                    name, data["close"], sign, data["change_pct"],
                )
            _save_indices(indices)
        else:
            logger.warning(
                "지수 데이터 없음 — pykrx 설치 여부 확인: pip install pykrx"
            )
            # 기존 저장본이 있으면 유지
            cached = _load_indices()
            if cached:
                logger.info("캐시된 지수 데이터 유지: %s", list(cached.keys()))
    except Exception:
        logger.exception("지수 수집 중 예외 발생 — 계속 진행")

    # 2. 전체 종목 분석 (한국 + 미국)
    analysis_ok = False
    try:
        analyzer = StockAnalyzer(config_dir=str(_CONFIG_DIR))
        df, raw_data = analyzer.run()

        if df.empty:
            logger.error("분석 결과 없음 — 네트워크 또는 데이터 문제 확인")
        else:
            writer = ReportWriter(output_dir=str(_OUTPUT_ROOT))
            writer.save(df, raw_data)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info("%d개 종목 분석 완료  (%.1f초)", len(df), elapsed)

            # 분류별 요약
            for cat, label in [
                ("TOP 관심", "TOP 관심"),
                ("매수후보", "매수후보"),
                ("과열",     "과열"),
                ("위험",     "위험"),
            ]:
                sub = df[df["분류"] == cat]
                if sub.empty:
                    continue
                names = ", ".join(sub["종목"].tolist())
                logger.info("  [%s] %d개: %s", label, len(sub), names)

            analysis_ok = True

    except Exception:
        logger.exception("종목 분석 중 예외 발생")

    # 3. 분석 실패 시 기존 데이터에 stale 마킹 — 대시보드가 비지 않도록
    if not analysis_ok:
        if _last_rank_exists():
            _stamp_last_rank_as_stale()
            logger.warning("대시보드는 이전 데이터를 stale 표시와 함께 표시합니다")
        else:
            logger.error("저장된 이전 데이터도 없습니다 — 대시보드가 빌 수 있습니다")

    logger.info("=" * 52)
    return analysis_ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
