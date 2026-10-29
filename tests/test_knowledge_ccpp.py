"""Phase 1 slice 1: C/C++ knowledge, cyber topics untouched, honest fallback."""
from app.services.creox_engine import CreoXEngine


def _ask(q):
    return CreoXEngine().complete([{"role": "user", "content": q}], "creox").reply


def test_old_cyber_topic_still_works():
    assert "Phishing" in _ask("what is phishing?")


def test_c_pointer_with_source():
    r = _ask("pointer kya hota hai")
    assert "pointer" in r.lower()
    assert "C Language CheatSheet.pdf" in r


def test_c_pointer_english_phrasing_same_answer():
    r = _ask("what is a pointer in C?")
    assert "dereference" in r.lower()


def test_cpp_class_and_inheritance():
    assert "class Car" in _ask("what is a class in C++?")
    assert "Vehicle" in _ask("explain inheritance in C++")


def test_outside_topics_still_honest_fallback():
    r = _ask("what is quantum entanglement?")
    assert "don't have a reliable answer" in r
