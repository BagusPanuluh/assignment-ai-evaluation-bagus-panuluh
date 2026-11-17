"""Router sederhana untuk memilih jawaban FAQ atau tool status tiket."""

import re

from app.rag import answer_from_knowledge_base
from app.tools import get_ticket_status

TICKET_ID_PATTERN = re.compile(r"TICKET-\d{4}", re.IGNORECASE)
FAQ_TERMS = (
    "cuti", "password", "vpn", "laptop", "perangkat", "email",
    "akses", "onboarding", "software", "login", "reimbursement",
)


async def detect_intent(query: str) -> str:
    """
    Menentukan intent sederhana tanpa panggilan LLM tambahan.
    """
    if TICKET_ID_PATTERN.search(query):
        return "ticket_status"

    normalized_query = query.lower()
    asks_about_ticket = "tiket" in normalized_query or "ticket" in normalized_query
    asks_about_faq = any(term in normalized_query for term in FAQ_TERMS)

    if asks_about_ticket and not asks_about_faq:
        return "ticket_status"
    return "faq"


def extract_ticket_id(query: str) -> str:
    """Mengekstrak ticket_id dari teks query menggunakan regex."""
    match = TICKET_ID_PATTERN.search(query)
    if match:
        return match.group(0).upper()
    return ""


async def handle_query(query: str) -> dict:
    """Fungsi utama yang dipanggil oleh endpoint /ask."""
    try:
        if not query or not query.strip():
            return {
                "status": "error",
                "intent": "invalid_query",
                "data": "Pertanyaan tidak boleh kosong. Silakan masukkan pertanyaan helpdesk.",
            }

        if len(query) > 2000:
            return {
                "status": "error",
                "intent": "invalid_query",
                "data": "Pertanyaan terlalu panjang. Mohon ringkas menjadi maksimal 2000 karakter.",
            }

        intent = await detect_intent(query)

        if intent == "ticket_status":
            ticket_id = extract_ticket_id(query)
            if not ticket_id:
                return {
                    "status": "error",
                    "intent": "ticket_status",
                    "data": "Mohon sertakan ID tiket (format: TICKET-XXXX) pada pertanyaan Anda.",
                }
            data = get_ticket_status(ticket_id)
            return {"status": "success", "intent": "ticket_status", "data": data}

        else:  # intent == "faq"
            data = await answer_from_knowledge_base(query)
            return {"status": "success", "intent": "faq", "data": data}

    except Exception:
        return {
            "status": "error",
            "intent": "unknown",
            "data": "Layanan sedang mengalami kendala. Silakan coba lagi beberapa saat kemudian.",
        }
