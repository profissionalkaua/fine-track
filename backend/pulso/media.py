import hashlib
import subprocess

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .adapters.media import MediaAnalyzer
from .db import session_for, uid
from .jobs import workspace
from .models import AuthorizedMedia, VideoAnalysis


def analyze_authorized(app, workspace_id, reference):
    unavailable = {
        "state": "unavailable",
        "reason": "Mídia autorizada não disponível para esta análise.",
        "segments": [],
    }
    analyzer = MediaAnalyzer(app.state.settings)
    with session_for(app.state.engine) as db:
        workspace(db, workspace_id)
        media = db.get(AuthorizedMedia, (workspace_id, reference["id"]))
        if media is None:
            return unavailable
        path, expected_hash = media.path, media.media_hash
        cache_key = analyzer.cache_key(media.media_hash, reference["description"])
        try:
            file = analyzer.authorized_file(path)
            if hashlib.sha256(file.read_bytes()).hexdigest() != expected_hash:
                return {
                    **unavailable,
                    "reason": "A mídia mudou. O operador deve renovar a autorização da versão.",
                }
        except (OSError, ValueError):
            return {**unavailable, "reason": "O arquivo autorizado não está acessível."}
        cached = db.scalar(
            select(VideoAnalysis).where(
                VideoAnalysis.video_id == reference["id"], VideoAnalysis.cache_key == cache_key
            )
        )
        if cached and cached.result.get("state") == "completed":
            return cached.result
    try:
        result = analyzer.analyze(path, reference["description"])
    except (OSError, ValueError, subprocess.SubprocessError):
        return {**unavailable, "reason": "A mídia não pôde ser processada dentro do orçamento desta análise."}
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        statement = insert(VideoAnalysis).values(
            id=uid(),
            workspace_id=workspace_id,
            video_id=reference["id"],
            cache_key=cache_key,
            result=result,
            created_at=app.state.clock(),
        )
        db.execute(
            statement.on_conflict_do_update(
                index_elements=["workspace_id", "video_id", "cache_key"],
                set_={"result": statement.excluded.result},
            )
        )
    return result
