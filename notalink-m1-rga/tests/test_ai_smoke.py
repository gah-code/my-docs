from mcp_server.tools.ai import ai_generate
def test_ai_generate_smoke():
    out = ai_generate({"variables": {"text": "One. Two. Three. Four."}, "seed": 42})
    assert "text" in out and "trace_id" in out
