from agents.onboarding_knowledge.agent import best_match, compose

RECORDS = [
    {
        "id": "KB-001",
        "title": "Forms for a W-2 hire in Texas",
        "question": "Which forms does a W-2 hire in Texas need?",
        "tags": ["texas", "forms"],
        "status": "validated",
        "steps": [],
        "answer": "W-4 and I-9.",
        "source": "procedure",
    },
    {
        "id": "KB-003",
        "title": "Requesting a laptop and access",
        "question": "How do I request a laptop?",
        "tags": ["laptop", "equipment"],
        "status": "validated",
        "steps": ["IT approves.", "The approver approves."],
        "answer": "The Coworker adds it to the package.",
        "source": "procedure",
    },
]


def test_a_paraphrase_finds_the_record() -> None:
    match = best_match("How can I get a laptop for my new hire?", RECORDS)

    assert match["id"] == "KB-003"


def test_one_shared_word_is_not_enough() -> None:
    assert best_match("Which forms does a hire in Ohio need?", RECORDS) is None


def test_an_empty_question_matches_nothing() -> None:
    assert best_match("how do I?", RECORDS) is None


def test_answer_lists_the_steps_and_cites_the_record() -> None:
    text = compose(RECORDS[1])

    assert "Steps: 1) IT approves. 2) The approver approves." in text
    assert "Source: KB-003 · Requesting a laptop and access (procedure)." in text
