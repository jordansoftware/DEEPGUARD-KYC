from __future__ import annotations

from fastapi import APIRouter, Depends
from rapidfuzz import fuzz

from ..schemas import ScreeningIn, ScreeningOut
from ..security import current_client

router = APIRouter(prefix="/api/screening", tags=["screening"])

SANCTIONS_LIST: list[dict[str, str]] = [
    {"name": "Vladimir Putin", "kind": "sanctions", "source": "OFAC SDN"},
    {"name": "Bashar al-Assad", "kind": "sanctions", "source": "OFAC SDN"},
    {"name": "Kim Jong Un", "kind": "sanctions", "source": "OFAC SDN"},
    {"name": "Ebrahim Raisi", "kind": "sanctions", "source": "EU Consolidated"},
    {"name": "Ali Khamenei", "kind": "sanctions", "source": "OFAC SDN"},
    {"name": "Nicolás Maduro", "kind": "sanctions", "source": "OFAC SDN"},
    {"name": "Alexander Lukashenko", "kind": "sanctions", "source": "EU Consolidated"},
    {"name": "Mohammed bin Salman", "kind": "pep", "source": "PEP Database"},
    {"name": "Volodymyr Zelenskyy", "kind": "pep", "source": "PEP Database"},
    {"name": "Sanctioned Bank of X", "kind": "sanctions", "source": "OFAC SDN"},
]

THRESHOLD = 0.60


def _score_name(query: str, target: str) -> float:
    q = query.lower().strip()
    t = target.lower().strip()
    token_set = fuzz.token_set_ratio(q, t) / 100.0
    partial = fuzz.partial_ratio(q, t) / 100.0
    return round(max(token_set, partial), 4)


def run_screening(name: str, birth_date: str = "", country: str = "") -> dict:
    query_lower = name.lower().strip()
    matches: list[dict] = []
    best_score = 0.0

    for entry in SANCTIONS_LIST:
        score = _score_name(query_lower, entry["name"])
        if score >= THRESHOLD:
            matches.append({
                "matched_name": entry["name"],
                "score": score,
                "kind": entry["kind"],
                "source": entry["source"],
            })
            best_score = max(best_score, score)

    matched = best_score >= THRESHOLD
    kind = matches[0]["kind"] if matched else "sanctions"
    source = matches[0]["source"] if matched else "DeepGuard AML Engine"

    return {
        "query_name": name,
        "kind": kind,
        "matched": matched,
        "match_score": round(best_score, 4) if matched else 0.0,
        "matches": matches,
        "source": source,
    }


@router.post("", response_model=ScreeningOut)
def screen_person(
    payload: ScreeningIn,
    client=Depends(current_client),
):
    result = run_screening(payload.name, payload.birth_date, payload.country)
    return ScreeningOut(**result)
