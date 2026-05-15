from app.modules import Idea, MockProvider, ScriptDraft


def test_module_exports() -> None:
    idea = Idea(id="i1", title="Topic", audience="Founders", premise="Fast path")
    script = ScriptDraft(idea_id=idea.id, hook="Hi", outline=["a", "b"], cta="Subscribe")
    provider = MockProvider()

    assert script.idea_id == "i1"
    response = provider.generate("hello")
    assert response.startswith("{")
    assert "sections" in response
