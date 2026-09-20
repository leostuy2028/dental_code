import re

#these are common phrases that let you know a model is refusing a question


_REFUSAL_MARKERS = (
    "i'm unable", "i am unable", "i cannot", "i can't", "unable to view",
    "unable to analyze", "can't analyze", "cannot analyze", "as an ai",
    "i'm sorry", "i am sorry", "consult a", "seek professional",
    "not able to", "i'm not able", "cannot provide", "can't provide",
    "unable to provide", "i must decline", "i won't",
)


def looks_like_refusal(text):
    t = (text or "").lower()
    for m in _REFUSAL_MARKERS:
        if m in t:
            return True
    return False

#For actual infrastructure failure unlike model refusal
# "==" rather than in because I want the string to only be that message rather than being able to contain it as in looks_like_refusal
_API_FAILURE_ERROR_MESSAGE = "max retries exceeded"
def is_api_failure(text):
    """True if `raw_response` is a stored API-failure marker not actual output."""
    return isinstance(text, str) and text.strip() == _API_FAILURE_ERROR_MESSAGE



_ANSWER_CUES = [
   
    r"CORRECT\s+(?:OPTION|CHOICE|ANSWER)\s+IS\W{0,6}([ABCD])(?![A-Z])", #"The correct answer is B"
    r"\bANSWER\W{0,6}(?:IS\W{0,6})?([ABCD])(?![A-Z])",       #"answer: C", "answer is D"
     r"OPTION\s+([ABCD])\s+IS\s+(?:THE\s+)?CORRECT",          #"option A is the correct answer"
]
# simple layer for one letter answer. (b) "[B]"
_ONLY_ONE_L = re.compile(r"^[(\[]?\s*([ABCD])\s*[).\]]?$")
#fall back layer, diff from 1 cue because no wrap takes the last letter with nothing around it. searches forward takes the last.
_STANDALONE = re.compile(r"(?<![A-Z])([ABCD])(?![A-Z])")


def extract_letter(text, cot=False):
    """when cot false this returns a b c or d when it finds something and none when it doesnt rather than guessing.
    Order is _ONLY_ONE_L if it falls through then it searches for the last of any Answer cues
    if Answer cues falls it goes to _STANDALONE. Then you get a letter or none.
    """
    if cot:
        # the prompt asks for a  "Answer: X" format cot model always responds right (350/350). So no deep 3 layer needed.
        u = re.sub(r"[*_`]", " ", text or "")
        hits = list(re.finditer(r"\bANSWER\b\s*:?\s*([ABCD])(?![A-Za-z])", u, re.IGNORECASE))
        return hits[-1].group(1).upper() if hits else None

    raw = text or ""
    if not raw.strip():
        return None

    one_letter_response = _ONLY_ONE_L.match(raw.strip().upper())
    if one_letter_response:
        return one_letter_response.group(1)

    # substitutes special markdown with space (*``_) *C* = C
    #uppercase too
    u = re.sub(r"[*_`]", " ", raw).upper()

    cue_hits = []
    for i in _ANSWER_CUES:
        cue_hits += list(re.finditer(i, u))  #adds all match objects from all of the instances together 
    if cue_hits:
        return max(cue_hits, key=lambda m: m.start()).group(1) #winner decided based on last position

    tokens = _STANDALONE.findall(u) #fallback
    if tokens:
        return tokens[-1]#takes the last based on the order of letters
    return None
