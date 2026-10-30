import re

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.module2 import CourseChunk
from app.services.gemini import generate_json, generate_text
from app.services.module2_rag import retrieve

UNSAFE = re.compile(r"\b(kill|weapon|bomb|suicide|sex|porn|drug|hack|kill myself|tuer|arme|bombe|suicide|sexe|drogue)\b", re.I)
REDIRECT = "Je suis là pour t'aider à apprendre tes cours. Choisissons ensemble un sujet de ta leçon !"


def curriculum_context(session: Session, course_id: int, query: str, k: int = 5):
    chunks = session.exec(select(CourseChunk).where(CourseChunk.course_id == course_id).order_by(CourseChunk.position)).all()
    if not chunks:
        raise HTTPException(400, "Aucun cours indexé. Ajoute d'abord une leçon dans le Module 2.")
    try:
        found = retrieve(query, chunks, k=k)
    except Exception as exc:
        raise HTTPException(502, "La recherche dans le cours est indisponible.") from exc
    if not found or found[0][0] < 0.35:
        return [], ""
    sources = [{"id": i + 1, "label": f"Cours · extrait {chunk.position + 1}", "score": round(score, 2), "text": chunk.content[:1000]} for i, (score, chunk) in enumerate(found)]
    return sources, "\n\n".join(f"[Source {i+1}] {chunk.content}" for i, (_, chunk) in enumerate(found))


def safe_prompt(text: str) -> bool:
    return bool(text.strip()) and not UNSAFE.search(text)


def _lesson_sentences(context: str) -> list[str]:
    clean = re.sub(r"\[Source\s+\d+\]\s*", "", context, flags=re.I)
    clean = re.sub(r"\[\d+\]\s*", "", clean)
    return [
        sentence.strip(" \t\r\n-•")
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", clean)
        if len(sentence.strip()) >= 12
    ]


def tutor_answer(session: Session, course_id: int, message: str, hint: bool, analogy: str):
    if not safe_prompt(message):
        return {"answer": REDIRECT, "sources": [], "redirected": True, "badges": [], "generation_mode": "local"}
    sources, context = curriculum_context(session, course_id, message)
    if not context:
        return {"answer": "Je ne trouve pas cette idée dans ta leçon. Demande-moi quelque chose sur le cours indexé et on cherchera ensemble !", "sources": [], "redirected": False, "badges": [], "generation_mode": "local"}
    sentences = _lesson_sentences(context)
    excerpt = sentences[0] if sentences else context[:500]
    theme_instruction = f" Explique avec une analogie {analogy}." if analogy else ""
    mode = "local"
    generated = generate_text(
        "Tu es un tuteur scolaire chaleureux pour un enfant. Réponds uniquement à partir du contexte. "
        "Ne donne pas d'information extérieure. Si indice demandé, guide par une question sans donner la réponse finale. "
        f"Question: {message}. Indice: {hint}.{theme_instruction}\nContexte du cours: {context[:10000]}"
    )
    context_words = {word.casefold() for sentence in sentences for word in re.findall(r"\w+", sentence) if len(word) > 5}
    grounded = generated and any(word in generated.casefold() for word in context_words)
    if grounded and not (hint and re.search(r"\b(answer|solution|rÃ©ponse finale|rÃ©sultat est)\b", generated, re.I)):
        answer, mode = generated[:3000], "ai"
    elif hint:
        answer = f"Petit indice : relis cette phrase de ta leçon : « {excerpt} » [Source 1]. Quel mot ou quelle idée te semble la plus importante ?"
    else:
        answer = f"Dans ta leçon, on lit : « {excerpt} » [Source 1]. Essaie de l'expliquer avec tes mots, et je peux ensuite te donner un indice."
    return {"answer": answer, "sources": sources, "redirected": False, "badges": ["Curious Explorer"], "generation_mode": mode}


def quiz(session: Session, course_id: int, topic: str, difficulty: str, count: int):
    if not safe_prompt(topic):
        raise HTTPException(422, REDIRECT)
    sources, context = curriculum_context(session, course_id, topic)
    if not context:
        raise HTTPException(422, "Ce sujet n'apparaît pas dans la leçon indexée.")
    sentences = _lesson_sentences(context)
    if not sentences:
        raise HTTPException(422, "Le cours indexé ne contient pas assez de texte pour créer un quiz.")
    generated = generate_json(
        "Crée exactement " + str(count) + " questions de quiz en français fondées exclusivement sur le cours ci-dessous. "
        "Types permis: mcq, true_false, short. Retourne un objet JSON {questions:[{type,question,options,answer,explanation}]}. "
        "Pour mcq, answer doit être exactement une option; true_false: options Vrai/Faux et answer Vrai/Faux. "
        f"Sujet: {topic}. Difficulté: {difficulty}. Cours:\n{context[:12000]}"
    )
    generated_questions = generated.get("questions") if isinstance(generated, dict) else None
    if isinstance(generated_questions, list) and len(generated_questions) == count and all(_valid_question(item) for item in generated_questions):
        return {"topic": topic, "questions": generated_questions, "sources": sources, "generation_mode": "ai"}
    questions = []
    for index in range(count):
        answer = sentences[index % len(sentences)]
        kind = ("mcq", "true_false", "short")[index % 3]
        if kind == "true_false":
            question = {"type": kind, "question": f"Vrai ou faux : selon ta leçon, « {answer} » ?", "options": ["Vrai", "Faux"], "answer": "Vrai", "explanation": "Cette phrase est tirée de ton cours."}
        elif kind == "short":
            question = {"type": kind, "question": f"Que dit ta leçon à propos de « {topic} » ?", "options": [], "answer": answer, "explanation": "Compare ta réponse avec cette phrase du cours."}
        else:
            options = [answer]
            for candidate in sentences:
                if candidate != answer and candidate not in options and len(options) < 4:
                    options.append(candidate)
            while len(options) < 3:
                options.append("Je relis le passage du cours.")
            question = {"type": kind, "question": f"Quelle phrase est extraite de la leçon sur « {topic} » ?", "options": options, "answer": answer, "explanation": "Cette phrase apparaît dans ton cours."}
        questions.append(question)
    return {"topic": topic, "questions": questions, "sources": sources, "generation_mode": "local"}


def _valid_question(item: object) -> bool:
    if not isinstance(item, dict) or item.get("type") not in {"mcq", "true_false", "short"}:
        return False
    if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("question", "answer", "explanation")):
        return False
    options = item.get("options")
    if not isinstance(options, list) or not all(isinstance(option, str) for option in options):
        return False
    if item["type"] == "mcq":
        return len(options) >= 2 and item["answer"] in options
    if item["type"] == "true_false":
        return options == ["Vrai", "Faux"] and item["answer"] in options
    return len(options) == 0


def visuals(session: Session, course_id: int, topic: str):
    sources, context = curriculum_context(session, course_id, topic)
    if not context:
        raise HTTPException(422, "Ce sujet n'apparaît pas dans la leçon indexée.")
    sentences = _lesson_sentences(context)
    if not sentences:
        raise HTTPException(422, "Le cours indexé ne contient pas assez de texte pour créer un schéma.")
    generated = generate_json(
        "Crée un schéma d'apprentissage enfant en français uniquement depuis le cours. "
        "JSON: {title:string,steps:[{label:string,detail:string}],mind_map:[{label:string,children:[string]}]}. "
        f"Sujet: {topic}. Cours:\n{context[:12000]}"
    )
    if isinstance(generated, dict):
        steps = generated.get("steps")
        mind_map = generated.get("mind_map")
        if (isinstance(generated.get("title"), str) and isinstance(steps, list) and steps and
                all(isinstance(step, dict) and isinstance(step.get("label"), str) and isinstance(step.get("detail"), str) for step in steps) and
                isinstance(mind_map, list) and all(isinstance(node, dict) and isinstance(node.get("label"), str) and isinstance(node.get("children"), list) for node in mind_map)):
            return {"title": generated["title"][:200], "steps": steps[:8], "mind_map": mind_map[:8], "sources": sources, "generation_mode": "ai"}
    steps = [{"label": f"Idée {index + 1}", "detail": sentence} for index, sentence in enumerate(sentences[:6])]
    return {
        "title": topic,
        "steps": steps,
        "mind_map": [{"label": topic, "children": sentences[:6]}],
        "sources": sources,
        "generation_mode": "local",
    }
