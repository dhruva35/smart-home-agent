from agent.tools import build_tools


def test_build_tools_returns_expected_toolset():
    tools = build_tools(source="test")
    names = {t.name for t in tools}
    assert names == {
        "list_devices",
        "get_device_status",
        "lock_door",
        "unlock_door",
        "toggle_light",
        "set_thermostat",
        "arm_alarm",
        "disarm_alarm",
        "view_camera_snapshot",
    }


def test_source_is_never_an_llm_controllable_argument():
    """
    Security invariant: the model must never be able to set or override its
    own trust label. If `source` ever leaks into a tool's args_schema, an
    attacker could get the model to self-report "source: chat" for an
    action that actually originated from the untrusted webhook channel,
    silently defeating the entire audit trail.
    """
    tools = build_tools(source="chat")
    for tool in tools:
        if tool.args_schema is not None:
            field_names = set(tool.args_schema.model_fields.keys())
            assert "source" not in field_names, (
                f"tool '{tool.name}' exposes 'source' as an LLM-fillable argument"
            )
