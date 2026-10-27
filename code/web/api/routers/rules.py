from fastapi import APIRouter, HTTPException

from ..deps import Role, catalog

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("/{rule_id}")
def rule_detail(rule_id: str, role: Role) -> dict:
    """A rule cited in a package, with its owner, version and status (US-007 AC-003)."""
    try:
        return catalog().get(rule_id).model_dump()
    except KeyError:
        raise HTTPException(404, detail=f"No rule {rule_id}") from None
