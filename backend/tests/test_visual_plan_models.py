import pytest
from pydantic import ValidationError

from uuid import UUID

from app.modules.visual_plan import VisualPlan, VisualScene, VisualType


def _scene(**overrides):
    data = {
        "scene_number": 1,
        "narration_excerpt": "Hook setup",
        "visual_type": VisualType.chart,
        "visual_description": "Bar chart comparing retention",
        "purpose": "Reinforce retention contrast",
        "asset_notes": None,
        "risk_notes": None,
        "filler_risk_score": 0.4,
    }
    data.update(overrides)
    return data


def test_visual_type_enum_validity() -> None:
    scene = VisualScene(**_scene(visual_type=VisualType.map))
    assert scene.visual_type == VisualType.map


@pytest.mark.parametrize("purpose", ["", "   "])
def test_purpose_required(purpose: str) -> None:
    with pytest.raises(ValidationError):
        VisualScene(**_scene(purpose=purpose))


def test_scene_ordering_enforced() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        VisualPlan(
            script_id=UUID("00000000-0000-0000-0000-000000000001"),
            scenes=[
                VisualScene(**_scene(scene_number=2)),
                VisualScene(**_scene(scene_number=1, purpose="next")),
            ],
        )


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_filler_risk_range_enforcement(score: float) -> None:
    with pytest.raises(ValidationError):
        VisualScene(**_scene(filler_risk_score=score))
