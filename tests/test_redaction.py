from ktk_pipeline.jobs.fb_insights import _redact_graph_error


def test_redacts_exact_token_and_eaa_strings():
    message = (
        "request used fake-system-token; old token EAA-fake-legacy "
        "and another EAAsecret"
    )

    redacted = _redact_graph_error(message, "fake-system-token")

    assert redacted == (
        "request used [REDACTED]; old token [REDACTED] "
        "and another [REDACTED]"
    )


def test_redacts_token_without_replacing_nonmatching_text():
    message = "keep this fake-token-suffix and EAA"

    redacted = _redact_graph_error(message, "fake-token")

    assert redacted == "keep this [REDACTED]-suffix and [REDACTED]"
