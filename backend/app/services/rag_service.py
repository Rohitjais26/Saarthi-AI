from dataclasses import dataclass


@dataclass
class RAGAnswer:
    answer: str
    citations: list[str]


KB = {
    'en': [
        {
            'id': 'kb/programs/registration#chunk_01',
            'keywords': ['register', 'registration', 'apply', 'application'],
            'answer': 'Start with registration, then complete eligibility, document upload, and orientation to confirm enrollment.',
        },
        {
            'id': 'kb/programs/documents#chunk_02',
            'keywords': ['document', 'upload', 'proof', 'id'],
            'answer': 'Accepted documents include identity proof, age proof, and education proof. Upload clear images for faster verification.',
        },
        {
            'id': 'kb/programs/orientation#chunk_03',
            'keywords': ['orientation', 'session', 'when'],
            'answer': 'Orientation is scheduled after document verification. You will receive reminders on your consented channels.',
        },
    ],
    'hi': [
        {
            'id': 'kb/programs_hi/registration#chunk_01',
            'keywords': ['registration', 'apply', 'aavedan'],
            'answer': 'Pehle registration karein, phir eligibility, document upload aur orientation complete karein.',
        },
        {
            'id': 'kb/programs_hi/documents#chunk_02',
            'keywords': ['document', 'upload', 'praman', 'id'],
            'answer': 'Pehchan patra, umr praman aur shiksha praman patra upload karein. Saaf photo verification jaldi karti hai.',
        },
        {
            'id': 'kb/programs_hi/orientation#chunk_03',
            'keywords': ['orientation', 'session'],
            'answer': 'Document verify hone ke baad orientation session hota hai aur reminder message bheja jata hai.',
        },
    ],
}


def _select_chunk(question: str, locale: str) -> dict:
    chunks = KB.get(locale, KB['en'])
    q = question.lower()
    best = chunks[0]
    best_score = -1
    for chunk in chunks:
        score = sum(1 for keyword in chunk['keywords'] if keyword in q)
        if score > best_score:
            best = chunk
            best_score = score
    return best


def answer_faq(question: str, locale: str = 'en', program: str | None = None) -> RAGAnswer:
    locale = (locale or 'en').lower()
    if locale not in KB:
        locale = 'en'
    chunk = _select_chunk(question, locale)
    program_hint = f' for {program}' if program else ''
    return RAGAnswer(
        answer=f"{chunk['answer']}{program_hint}",
        citations=[chunk['id']],
    )
