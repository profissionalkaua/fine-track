"""Read-only hourly diagnostics. Synthetic rankings never count as real coverage."""

import argparse
import json
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))

from sqlalchemy import select

from pulso.config import Settings
from pulso.db import engine_for, session_for
from pulso.feed import normalize
from pulso.models import Ranking

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--once", action="store_true")
parser.add_argument("--hours", type=int, default=168, choices=range(1, 745))
parser.add_argument("--country", action="append", default=[])
parser.add_argument("--category", default="")
args = parser.parse_args()
countries = args.country or ["BR", "PT"]
if any(len(country) != 2 or not country.isalpha() for country in countries):
    parser.error("Use códigos ISO de duas letras.")
settings = Settings()
destination = root / ".runtime/pilot"
destination.mkdir(parents=True, exist_ok=True)
stop_at = time.monotonic() + args.hours * 3600
while True:
    sampled_at = datetime.now(UTC)
    sample = {
        "sampled_at": sampled_at.isoformat(),
        "collection_enabled": settings.collection_enabled,
        "phase": "observation" if settings.collection_enabled else "preflight_source_disabled",
        "coverage": [],
        "acceptance_approved": False,
    }
    engine = engine_for(settings.database_url)
    try:
        with session_for(engine) as db:
            for country in countries:
                for period in ["day", "week", "month"]:
                    ranking = db.scalar(
                        select(Ranking).where(
                            Ranking.country == country.upper(), Ranking.period == period,
                            Ranking.category == normalize(args.category),
                        ).order_by(Ranking.as_of.desc()).limit(1)
                    )
                    items = ranking.items if ranking else []
                    count = sum(item.get("synthetic") is False for item in items)
                    age = (sampled_at - ranking.as_of).total_seconds() if ranking else None
                    sample["coverage"].append({
                        "country": country.upper(), "period": period,
                        "eligible_real": count,
                        "synthetic_excluded": sum(item.get("synthetic") is True for item in items),
                        "ranking_age_seconds": age,
                        "coverage_target_met": bool(
                            settings.collection_enabled and count >= 20
                            and age is not None and 0 <= age <= settings.latest_snapshot_hours * 3600
                        ),
                    })
        # Aggregate metrics contain stable routes and counts, without payloads or credentials.
        with urllib.request.urlopen("http://127.0.0.1:8000/metrics", timeout=5) as response:
            metrics = response.read(2_000_000).decode("utf8")
        stamp = sampled_at.strftime("%Y%m%dT%H%M%SZ")
        (destination / f"metrics-{stamp}.prom").write_text(metrics, encoding="utf8")
    except Exception as exc:
        sample["error_type"] = type(exc).__name__
    finally:
        engine.dispose()
    with (destination / "samples.jsonl").open("a", encoding="utf8") as stream:
        stream.write(json.dumps(sample, ensure_ascii=False) + "\n")
    print(json.dumps(sample, ensure_ascii=False), flush=True)
    if args.once or time.monotonic() >= stop_at:
        break
    time.sleep(min(3600, max(0, stop_at - time.monotonic())))
    settings = Settings()
