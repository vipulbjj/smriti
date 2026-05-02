"""
52 story prompts — one per week for a year.
Each prompt is bilingual: Hindi first, English below.
Designed for grandparents who may speak limited English.
Arc: childhood → family → world events → wisdom → legacy.
"""

from .db import Language

PROMPTS_HINDI = [
    # Childhood (1–10)
    "आपका बचपन कहाँ गुज़रा? आपके घर और मोहल्ले के बारे में बताइए।",
    "बचपन में आपका सबसे प्रिय खेल कौन सा था? उस समय की कोई मज़ेदार याद सुनाइए।",
    "आपके माता-पिता कैसे थे? उनकी कोई एक बात जो आप कभी नहीं भूले।",
    "आपके भाई-बहन कितने थे? उनके साथ कोई खास याद?",
    "बचपन में आप क्या बनना चाहते थे? वो सपना कैसा था?",
    "आपके स्कूल के दिन कैसे थे? कोई प्रिय अध्यापक याद है?",
    "बचपन में आपके घर का खाना — क्या बनता था जो आपको सबसे ज़्यादा पसंद था?",
    "आपके गाँव या शहर में त्योहार कैसे मनाए जाते थे?",
    "बचपन में कोई ऐसी घटना जिसने आपको डरा दिया हो या हँसा दिया हो?",
    "आपके दादा-दादी या नाना-नानी के बारे में बताइए। वे कैसे थे?",
    # Youth & Coming of Age (11–20)
    "जवानी में आपने पहली बार क्या काम किया? वो अनुभव कैसा था?",
    "आपकी पढ़ाई कैसे हुई? क्या कोई मुश्किल थी जो आपने पार की?",
    "आपकी शादी कैसे हुई? पहली बार मिलने की कहानी सुनाइए।",
    "शादी के शुरुआती साल कैसे थे? क्या मुश्किलें आईं?",
    "आपने अपनी ज़िंदगी में सबसे बड़ा फ़ैसला कब और क्यों लिया?",
    "पहली बार घर से दूर जाने का अनुभव कैसा था?",
    "आपके ज़माने में पैसों की क्या क़ीमत थी? एक रुपये में क्या मिलता था?",
    "जवानी में आपकी सबसे पक्की दोस्ती किससे थी? वो दोस्त कैसे थे?",
    "कोई एक मौका जब आप बहुत डरे हों — क्या हुआ था?",
    "उस ज़माने में मनोरंजन कैसे होता था? सिनेमा, रेडियो, मेले?",
    # Family & Parenthood (21–30)
    "जब आपके पहले बच्चे का जन्म हुआ, आपको कैसा लगा?",
    "अपने बच्चों की परवरिश में आपने सबसे ज़रूरी क्या समझा?",
    "परिवार में कोई ऐसी परंपरा जो आपने शुरू की या आगे बढ़ाई?",
    "आपके घर में बड़े फ़ैसले कैसे होते थे? कौन सलाह देता था?",
    "अपने बच्चों को लेकर कोई वो याद जो आज भी दिल में है?",
    "परिवार में कोई मुश्किल वक्त जब सब साथ आए — क्या हुआ था?",
    "आपके घर का सबसे ख़ास त्योहार कौन सा था और कैसे मनता था?",
    "आपकी माँ या सास के हाथ का कोई खास पकवान जो आप कभी नहीं भूले?",
    "पोते-पोतियों के बारे में आपको सबसे क्या अच्छा लगता है?",
    "परिवार को एक साथ रखने का राज़ क्या है आपके हिसाब से?",
    # Work & World (31–40)
    "आपने अपनी ज़िंदगी में सबसे मेहनत का काम क्या किया?",
    "कोई ऐसा दिन जब काम में बड़ी कामयाबी मिली?",
    "आपने देखा है भारत कैसे बदला — आज़ादी से लेकर अब तक। सबसे बड़ा बदलाव क्या लगा?",
    "1947 की आज़ादी या बँटवारे की आपके परिवार पर क्या असर हुआ?",
    "इंदिरा गाँधी का ज़माना — उस वक्त ज़िंदगी कैसी थी?",
    "जब टेलीविज़न या टेलीफ़ोन पहली बार आया — आपको कैसा लगा?",
    "आपके इलाके में कोई बड़ी प्राकृतिक आपदा या घटना जो आपने देखी?",
    "आपने कौन सी जगह सबसे ज़्यादा पसंद की — कोई यात्रा जो दिल में रही?",
    "ज़िंदगी में पैसे की सबसे बड़ी तकलीफ़ कब आई और आपने कैसे निपटे?",
    "आपकी नज़र में आज की पीढ़ी और आपकी पीढ़ी में सबसे बड़ा फ़र्क़ क्या है?",
    # Wisdom & Reflection (41–48)
    "ज़िंदगी में सबसे बड़ी ग़लती जो आपने की — और उससे क्या सीखा?",
    "अगर आप अपनी ज़िंदगी दोबारा जी सकते, तो क्या बदलते?",
    "ख़ुशी क्या है आपके लिए? सच्ची ख़ुशी कहाँ से मिली?",
    "आपने ज़िंदगी में सबसे बड़ा दुख कब झेला? उससे कैसे उबरे?",
    "भगवान या ऊपरवाले पर आपका विश्वास — वो कब सबसे ज़्यादा मज़बूत हुआ?",
    "कोई एक इंसान जिसने आपकी ज़िंदगी बदल दी — वो कौन था?",
    "ज़िंदगी ने आपको सबसे बड़ा सबक क्या दिया?",
    "अगर आपको एक बात कहनी हो जो हमेशा याद रहे — वो क्या होगी?",
    # Legacy & Message to Future (49–52)
    "अपने बच्चों और पोते-पोतियों को आप क्या संदेश देना चाहते हैं?",
    "हमारे परिवार की सबसे बड़ी ताक़त क्या है आपके हिसाब से?",
    "आप चाहते हैं कि लोग आपको किस तरह याद करें?",
    "ज़िंदगी के इस सफ़र में — एक बात जो सबसे ज़रूरी लगी। वो क्या है?",
]

PROMPTS_ENGLISH = [
    # Childhood (1–10)
    "Where did you grow up? Tell me about your home and your neighbourhood as a child.",
    "What games did you love playing as a child? Share a funny or happy memory from those days.",
    "What were your parents like? Tell me one thing about them you've never forgotten.",
    "How many siblings did you have? What's a special memory you share with them?",
    "What did you dream of becoming when you were young? What was that dream like?",
    "What were your school days like? Is there a teacher you still remember fondly?",
    "What was your favourite home-cooked meal growing up? Who made it?",
    "How were festivals celebrated in your village or town when you were young?",
    "Tell me about something that frightened or delighted you as a child.",
    "Tell me about your grandparents. What were they like?",
    # Youth & Coming of Age (11–20)
    "What was the first real work you ever did? What was that experience like?",
    "How far did your education go? Was there a challenge you had to overcome to study?",
    "How did your marriage come about? Tell me the story of when you first met.",
    "What were the early years of marriage like? What difficulties did you face together?",
    "What is the biggest decision you ever made in life, and why?",
    "What was it like the first time you left home and went somewhere far?",
    "What was the value of money in your time? What could you buy with one rupee?",
    "Who was your closest friend in your youth? What were they like?",
    "Tell me about a time you were truly frightened. What happened?",
    "How did people entertain themselves in those days — cinema, radio, fairs?",
    # Family & Parenthood (21–30)
    "What did you feel when your first child was born?",
    "What did you consider most important in raising your children?",
    "Is there a family tradition you started or kept alive?",
    "How were big decisions made in your household? Who did you turn to for advice?",
    "What is one memory of your children that still lives in your heart?",
    "Tell me about a difficult time when the whole family came together.",
    "What was your family's most special festival, and how did you celebrate it?",
    "Is there a dish — made by your mother or mother-in-law — that you've never forgotten?",
    "What do you love most about your grandchildren?",
    "What is the secret to keeping a family together, in your view?",
    # Work & World (31–40)
    "What was the hardest work you ever did in your life?",
    "Tell me about a day when something went really well at work — a proud moment.",
    "You have watched India change since Independence. What is the biggest change you have seen?",
    "How did Partition or Independence affect your family?",
    "What was life like during Indira Gandhi's time?",
    "What was it like the first time you saw a television or telephone?",
    "Did your region experience any major natural disaster or historic event? Tell me about it.",
    "What is one place you visited that stayed in your heart?",
    "When was money the tightest in your life, and how did you get through it?",
    "What is the biggest difference between your generation and the generation of today?",
    # Wisdom & Reflection (41–48)
    "What is the biggest mistake you made in life, and what did you learn from it?",
    "If you could live your life again, what would you change?",
    "What does happiness mean to you? Where has real joy come from in your life?",
    "What is the greatest sorrow you have carried? How did you find your way through it?",
    "Tell me about a moment when your faith in God or in life became strongest.",
    "Who is one person who truly changed the course of your life?",
    "What is the most important lesson life has taught you?",
    "If you could say one thing that you want us to always remember — what would it be?",
    # Legacy (49–52)
    "What message do you want to leave for your children and grandchildren?",
    "What do you think is the greatest strength of our family?",
    "How do you want people to remember you?",
    "In this whole journey of life — what is the one thing that mattered most?",
]

PROMPTS_PUNJABI = [
    # Childhood (1–10)
    "ਤੁਸੀਂ ਬਚਪਨ ਕਿੱਥੇ ਗੁਜ਼ਾਰਿਆ? ਆਪਣੇ ਘਰ ਅਤੇ ਮੁਹੱਲੇ ਬਾਰੇ ਦੱਸੋ।",
    "ਬਚਪਨ ਵਿੱਚ ਤੁਹਾਡੀ ਮਨਪਸੰਦ ਖੇਡ ਕੀ ਸੀ? ਕੋਈ ਖੁਸ਼ੀ ਭਰੀ ਯਾਦ ਸੁਣਾਓ।",
    "ਤੁਹਾਡੇ ਮਾਤਾ-ਪਿਤਾ ਕਿਹੋ ਜਿਹੇ ਸਨ? ਕੋਈ ਇੱਕ ਗੱਲ ਜੋ ਤੁਸੀਂ ਕਦੇ ਨਹੀਂ ਭੁੱਲੇ।",
    "ਤੁਹਾਡੇ ਭੈਣ-ਭਰਾ ਕਿੰਨੇ ਸਨ? ਉਨ੍ਹਾਂ ਨਾਲ ਕੋਈ ਖਾਸ ਯਾਦ?",
    "ਬਚਪਨ ਵਿੱਚ ਤੁਸੀਂ ਕੀ ਬਣਨਾ ਚਾਹੁੰਦੇ ਸੀ?",
    "ਤੁਹਾਡੇ ਸਕੂਲ ਦੇ ਦਿਨ ਕਿਹੋ ਜਿਹੇ ਸਨ? ਕੋਈ ਅਧਿਆਪਕ ਜੋ ਯਾਦ ਹੈ?",
    "ਬਚਪਨ ਵਿੱਚ ਘਰ ਦਾ ਕਿਹੜਾ ਖਾਣਾ ਸਭ ਤੋਂ ਚੰਗਾ ਲੱਗਦਾ ਸੀ?",
    "ਤੁਹਾਡੇ ਪਿੰਡ ਜਾਂ ਸ਼ਹਿਰ ਵਿੱਚ ਤਿਉਹਾਰ ਕਿਵੇਂ ਮਨਾਏ ਜਾਂਦੇ ਸਨ?",
    "ਬਚਪਨ ਦੀ ਕੋਈ ਅਜਿਹੀ ਗੱਲ ਜਿਸਨੇ ਤੁਹਾਨੂੰ ਡਰਾਇਆ ਜਾਂ ਹਸਾਇਆ?",
    "ਆਪਣੇ ਦਾਦਾ-ਦਾਦੀ ਜਾਂ ਨਾਨਾ-ਨਾਨੀ ਬਾਰੇ ਦੱਸੋ।",
    # Youth (11–20) — use English prompts for remaining (Punjabi support is partial in MVP)
    *PROMPTS_ENGLISH[10:],
]


assert len(PROMPTS_HINDI) == 52, f"Expected 52 Hindi prompts, got {len(PROMPTS_HINDI)}"
assert len(PROMPTS_ENGLISH) == 52, f"Expected 52 English prompts, got {len(PROMPTS_ENGLISH)}"


def get_prompt(index: int, language: Language) -> str:
    """Return the prompt at position index (0–51) for the given language."""
    if index < 0 or index >= 52:
        raise ValueError(f"Prompt index must be 0–51, got {index}")
    if language == Language.hindi:
        return PROMPTS_HINDI[index]
    if language == Language.punjabi:
        return PROMPTS_PUNJABI[index]
    return PROMPTS_ENGLISH[index]


def format_whatsapp_prompt(index: int, language: Language, grandparent_name: str) -> str:
    """Format a prompt for WhatsApp delivery — bilingual header + question."""
    week = index + 1
    prompt = get_prompt(index, language)

    if language == Language.hindi:
        header = f"🪔 *smriti* — सप्ताह {week}/52\nनमस्ते {grandparent_name} जी,"
        footer = "\n\n_आप आवाज़ में या लिखकर जवाब दे सकते हैं।_"
    elif language == Language.punjabi:
        header = f"🪔 *smriti* — ਹਫ਼ਤਾ {week}/52\nਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {grandparent_name} ਜੀ,"
        footer = "\n\n_ਤੁਸੀਂ ਬੋਲ ਕੇ ਜਾਂ ਲਿਖ ਕੇ ਜਵਾਬ ਦੇ ਸਕਦੇ ਹੋ।_"
    else:
        header = f"🪔 *smriti* — Week {week}/52\nNamaste {grandparent_name},"
        footer = "\n\n_You can reply by voice note or by typing your answer._"

    return f"{header}\n\n{prompt}{footer}"
