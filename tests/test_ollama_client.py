from pressure_evals.ollama_client import _supports_thinking, install_instructions


def test_install_instructions_format():
    text = install_instructions(["qwen3:4b", "gemma3:4b"])
    assert text == "ollama pull qwen3:4b\nollama pull gemma3:4b"


def test_install_instructions_empty():
    assert install_instructions([]) == ""


def test_supports_thinking_only_for_qwen3():
    assert _supports_thinking("qwen3:4b") is True
    assert _supports_thinking("qwen3:8b") is True
    assert _supports_thinking("gemma3:4b") is False
    assert _supports_thinking("llama3.2:3b") is False
