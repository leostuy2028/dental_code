#Test to check extract_letter specifically, ignoring the refusals

import pytest

from clients.parsing import extract_letter


#bare
# string = letter + non letter stuff
@pytest.mark.parametrize("reply, expected", [
    ("B", "B"),
    ("b", "B"),               # lowercase 
    ("B.", "B"),
    ("(C)", "C"),
    ("[D]", "D"),#brackets
    ("C)", "C"),
    ("  D  ", "D"),           # whitespace
])
def test_bare_replies(reply, expected):
    assert extract_letter(reply) == expected


# big three declaration check for layer 2
@pytest.mark.parametrize("reply, expected", [
    ("Answer: C", "C"),
    ("The answer is D", "D"),
    ("The correct answer is B", "B"),
    ("Option A is the correct answer.", "A"),
    ("**Correct Answer:** **C**", "C"),        # markdown gone
    ("Answer:    A", "A"),                     
])
def test_hard_cues(reply, expected):
    assert extract_letter(reply) == expected


#the last one is correct type check
@pytest.mark.parametrize("reply, expected", [
    ("...the answer is A, not B.", "A"),       # a cue beats a later bare token
    ("* C) #48  * D) #44  ... option A is the correct answer.  **A**", "A"),
])
def test_last_declaration_wins(reply, expected):
    assert extract_letter(reply) == expected


#  doomsday final layer: last standalone token
@pytest.mark.parametrize("reply, expected", [
    ("...= 29 teeth.\n\nD", "D"),      # trailing letter after reasoning
    ("D) #21", "D"),                   # letter with trailing content
])
def test_standalone_fallback_doomsday_operation(reply, expected):
    assert extract_letter(reply) == expected


#  regression guards
# Stupid naive parser should get them wrong
@pytest.mark.parametrize("reply, expected, naive_would_give", [
    ("Based on the panoramic radiograph...\n\nAnswer: A", "A", "B"),
    ("The correct answer is **D** (which corresponds to #38).", "D", "C"),
    ("A panoramic radiograph shows periapical lucency. Answer: C", "C", "A"),
])
def test_does_not_read_letters_out_of_english_words(reply, expected, naive_would_give):
    got = extract_letter(reply)
    assert got == expected
    assert got != naive_would_give

# dental caries = none  not D
def test_answer_followed_by_a_word_is_not_a_letter():
    """"Answer: dental caries" must not yield D from "Dental"."""
    assert extract_letter("Answer: dental caries") is None


# refusals
@pytest.mark.parametrize("reply", [
    "I am unable to view images",
    "As an AI, I cannot analyze medical images.",
    "",
    "   ",
    None,
    "no letter here",
])
def test_no_answer_returns_none(reply):
    assert extract_letter(reply) is None


# easy cot 
#smart model gets needs one

@pytest.mark.parametrize("reply, expected", [
    ("Answer: C", "C"),
    ("Long reasoning about tooth #38...\nAnswer: b", "B"),
    ("First I thought A, then B.\nAnswer: D", "D"),   
])
def test_cot_mode_reads_the_answer_line(reply, expected):
    assert extract_letter(reply, cot=True) == expected


@pytest.mark.parametrize("reply", [
    "Answer: None of the above",   # deliberate non-pick, must not scavenge
    "I considered A and B but no answer",
    "",
    None,
])
def test_cot_mode_returns_none_when_no_letter_declared(reply):
    assert extract_letter(reply, cot=True) is None


#invariant check always abcd or none
@pytest.mark.parametrize("reply", [
    "B", "Answer: C", "gibberish", "", None,
    "* C) #48 * D) #44 ... option A is the correct answer. **A**",
])
#final 
def test_output_is_always_a_valid_letter_or_none(reply):
    """Nothing downstream should ever see a value outside this set."""
    assert extract_letter(reply) in {"A", "B", "C", "D", None}