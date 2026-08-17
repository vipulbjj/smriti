"""
Milestone-based interview question bank for smriti.
Each milestone has a set of questions asked in sequence.
Language variants included: English (en), Hindi (hi), Punjabi (pa).
For V1, pick one language per user (ask once, or default to Hindi).
"""

MILESTONES = ["wedding", "buying_house", "birth_of_kids"]

QUESTIONS = {
    "wedding": {
        "en": [
            "Let's talk about your wedding. Where and when did it take place?",
            "How did you meet your spouse?",
            "What do you remember most vividly about your wedding day?",
            "Was there a funny or unexpected moment during the wedding?",
        ],
        "hi": [
            "चलिए आपकी शादी के बारे में बात करते हैं। यह कहाँ और कब हुई थी?",
            "आप अपने जीवनसाथी से कैसे मिले?",
            "आपको अपनी शादी के दिन की सबसे यादगार बात क्या लगती है?",
            "क्या शादी के दौरान कोई मजेदार या अनोखी घटना हुई थी?",
        ],
        "pa": [
            "ਆਓ ਤੁਹਾਡੇ ਵਿਆਹ ਬਾਰੇ ਗੱਲ ਕਰੀਏ। ਇਹ ਕਿੱਥੇ ਅਤੇ ਕਦੋਂ ਹੋਇਆ ਸੀ?",
            "ਤੁਸੀਂ ਆਪਣੇ ਜੀਵਨ ਸਾਥੀ ਨੂੰ ਕਿਵੇਂ ਮਿਲੇ?",
            "ਤੁਹਾਨੂੰ ਆਪਣੇ ਵਿਆਹ ਦੇ ਦਿਨ ਦੀ ਸਭ ਤੋਂ ਯਾਦਗਾਰੀ ਗੱਲ ਕੀ ਲੱਗਦੀ ਹੈ?",
            "ਕੀ ਵਿਆਹ ਦੌਰਾਨ ਕੋਈ ਮਜ਼ੇਦਾਰ ਜਾਂ ਅਚਾਨਕ ਪਲ ਹੋਇਆ ਸੀ?",
        ],
    },
    "buying_house": {
        "en": [
            "Tell me about the first home you bought. Where was it?",
            "What made you choose that particular house or area?",
            "Do you remember the day you moved in? What was it like?",
        ],
        "hi": [
            "अपने पहले घर के बारे में बताइए जो आपने खरीदा था। यह कहाँ था?",
            "आपने उस घर या इलाके को क्यों चुना?",
            "क्या आपको वह दिन याद है जब आप वहाँ रहने आए थे? कैसा लगा था?",
        ],
        "pa": [
            "ਆਪਣੇ ਪਹਿਲੇ ਘਰ ਬਾਰੇ ਦੱਸੋ ਜੋ ਤੁਸੀਂ ਖਰੀਦਿਆ ਸੀ। ਇਹ ਕਿੱਥੇ ਸੀ?",
            "ਤੁਸੀਂ ਉਹ ਘਰ ਜਾਂ ਇਲਾਕਾ ਕਿਉਂ ਚੁਣਿਆ?",
            "ਕੀ ਤੁਹਾਨੂੰ ਉਹ ਦਿਨ ਯਾਦ ਹੈ ਜਦੋਂ ਤੁਸੀਂ ਉੱਥੇ ਰਹਿਣ ਆਏ ਸੀ? ਕਿਹੋ ਜਿਹਾ ਸੀ?",
        ],
    },
    "birth_of_kids": {
        "en": [
            "Tell me about when your first child was born. Where were you?",
            "What was going through your mind in those first moments?",
            "Is there a memory from your child's early years that stays with you?",
        ],
        "hi": [
            "अपने पहले बच्चे के जन्म के बारे में बताइए। आप उस समय कहाँ थे?",
            "उन पहले पलों में आपके मन में क्या चल रहा था?",
            "क्या आपके बच्चे के शुरुआती सालों की कोई याद है जो आपके साथ रह गई है?",
        ],
        "pa": [
            "ਆਪਣੇ ਪਹਿਲੇ ਬੱਚੇ ਦੇ ਜਨਮ ਬਾਰੇ ਦੱਸੋ। ਤੁਸੀਂ ਉਸ ਵੇਲੇ ਕਿੱਥੇ ਸੀ?",
            "ਉਹਨਾਂ ਪਹਿਲੇ ਪਲਾਂ ਵਿੱਚ ਤੁਹਾਡੇ ਮਨ ਵਿੱਚ ਕੀ ਚੱਲ ਰਿਹਾ ਸੀ?",
            "ਕੀ ਤੁਹਾਡੇ ਬੱਚੇ ਦੇ ਸ਼ੁਰੂਆਤੀ ਸਾਲਾਂ ਦੀ ਕੋਈ ਯਾਦ ਹੈ ਜੋ ਤੁਹਾਡੇ ਨਾਲ ਰਹਿ ਗਈ ਹੈ?",
        ],
    },
}


def get_question(milestone: str, question_index: int, lang: str = "hi") -> str | None:
    """Returns the question text, or None if the milestone is exhausted."""
    questions = QUESTIONS.get(milestone, {}).get(lang, [])
    if question_index < len(questions):
        return questions[question_index]
    return None


def get_question_count(milestone: str, lang: str = "hi") -> int:
    return len(QUESTIONS.get(milestone, {}).get(lang, []))


def get_next_milestone(current_milestone: str) -> str | None:
    """Returns the next milestone in sequence, or None if all are done."""
    if current_milestone not in MILESTONES:
        return MILESTONES[0]
    idx = MILESTONES.index(current_milestone)
    if idx + 1 < len(MILESTONES):
        return MILESTONES[idx + 1]
    return None
