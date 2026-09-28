"""
MCQ generation for the AI Quiz Generator / Diagnostic engine.

Design goals (per project requirements):
- Works fully offline, with NO paid API key required for the demo.
- If LLM_PROVIDER + LLM_API_KEY are configured via environment variables,
  an LLM call is attempted first; on any failure (missing key, no network,
  bad response) it silently falls back to the deterministic local generator
  below, so the feature never breaks the UI.
- The deterministic generator never fabricates false claims: when there is
  not enough extracted text to build a content-grounded question, it draws
  from the curated topic question bank instead of inventing facts.
"""
import random
import re
from typing import List, Dict, Optional

from app.config import settings
from app.seed_data import TOPIC_QUESTION_BANK

STOPWORDS = set(
    "the a an of to in on for and or is are was were be been being this that "
    "with as by from at it its into your you their his her our we they them "
    "which who whom will shall can may might must not no if then than so such "
    "these those there here about over under between within without".split()
)


def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 6]


def _keyword(sentence: str) -> Optional[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", sentence)
    candidates = [w for w in words if w.lower() not in STOPWORDS]
    if not candidates:
        return None
    return max(candidates, key=len)


def _distractors(pool: List[str], exclude: str, n: int) -> List[str]:
    options = [w for w in pool if w.lower() != exclude.lower()]
    random.shuffle(options)
    picked, seen = [], {exclude.lower()}
    for w in options:
        if w.lower() in seen:
            continue
        picked.append(w)
        seen.add(w.lower())
        if len(picked) == n:
            break
    generic = ["Data Governance", "Manual Processing", "Static Reporting", "Legacy System", "Ad-hoc Review"]
    i = 0
    while len(picked) < n:
        candidate = generic[i % len(generic)]
        if candidate.lower() not in seen:
            picked.append(candidate)
            seen.add(candidate.lower())
        i += 1
    return picked


def _from_material_text(text: str, count: int, difficulty: str) -> List[Dict]:
    sentences = _sentences(text)
    if len(sentences) < 3:
        return []
    random.shuffle(sentences)
    all_keywords = []
    for s in sentences:
        kw = _keyword(s)
        if kw:
            all_keywords.append(kw)

    questions = []
    used = set()
    for sentence in sentences:
        if len(questions) >= count:
            break
        kw = _keyword(sentence)
        if not kw or kw.lower() in used:
            continue
        used.add(kw.lower())
        blanked = re.sub(re.escape(kw), "_____", sentence, count=1, flags=re.IGNORECASE)
        options = _distractors(all_keywords, kw, 3) + [kw]
        random.shuffle(options)
        correct_index = options.index(kw)
        questions.append({
            "question_text": f"Fill in the blank based on the uploaded material: \"{blanked}\"",
            "options": options,
            "correct_index": correct_index,
            "explanation": f"The source material states: \"{sentence}\"",
            "difficulty": difficulty,
        })
    return questions


def _from_topic_bank(topic: str, count: int, difficulty: str) -> List[Dict]:
    topic_l = (topic or "").lower()
    bank = list(TOPIC_QUESTION_BANK)
    if topic_l:
        matched = [q for q in bank if topic_l in q["topic"].lower() or any(
            kw in topic_l for kw in q.get("keywords", [])
        )]
        if matched:
            bank = matched + [q for q in TOPIC_QUESTION_BANK if q not in matched]
    random.shuffle(bank)
    result = []
    i = 0
    while len(result) < count and bank:
        item = bank[i % len(bank)]
        result.append({
            "question_text": item["question"],
            "options": item["options"],
            "correct_index": item["answer"],
            "explanation": item.get("explanation", ""),
            "difficulty": difficulty,
        })
        i += 1
        if i > count * 4:
            break
    return result


def _try_llm(material_text: str, topic: str, count: int, difficulty: str) -> Optional[List[Dict]]:
    if not settings.LLM_PROVIDER or not settings.LLM_API_KEY:
        return None
    try:
        # Deliberately generic/best-effort: only used if the operator has
        # configured a provider + key via environment variables. Any error
        # here is swallowed so the deterministic path always keeps working.
        import json
        if settings.LLM_PROVIDER.lower() == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
            prompt = (
                f"Generate {count} multiple choice questions (4 options each, one correct) "
                f"at {difficulty} difficulty about: {topic or 'the provided material'}.\n\n"
                f"Material excerpt:\n{material_text[:4000]}\n\n"
                "Respond ONLY with a JSON array of objects: "
                "{question_text, options (array of 4), correct_index (0-3), explanation}."
            )
            resp = client.messages.create(
                model=settings.LLM_MODEL or "claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            data = json.loads(text.strip().strip("`").replace("json\n", "", 1))
            return data
    except Exception:
        return None
    return None


def generate_quiz_questions(
    material_text: Optional[str], topic: Optional[str], count: int, difficulty: str
) -> List[Dict]:
    count = max(1, min(int(count or 5), 50))
    llm_result = _try_llm(material_text or "", topic or "", count, difficulty)
    if llm_result:
        return llm_result[:count]

    questions: List[Dict] = []
    if material_text:
        questions.extend(_from_material_text(material_text, count, difficulty))
    if len(questions) < count:
        questions.extend(_from_topic_bank(topic or "General Skills", count - len(questions), difficulty))
    return questions[:count]
