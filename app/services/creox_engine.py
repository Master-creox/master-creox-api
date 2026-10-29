"""CreoXEngine — Master CreoX API's own chat engine (Phase 4).

Fully built-in, deterministic and offline: no network call, no third-party
API, no API key, no per-token cost. It answers cybersecurity-awareness
questions from a knowledge base of the topics CreoX actually works on, and
falls back honestly when a question is outside that base — it never invents
an answer and never claims to be a large language model.

A local LLM can be plugged in later behind the same ModelAdapter protocol
without changing the chat endpoint; until then this engine is the provider.
"""
from __future__ import annotations

import re

from app.services.knowledge_ccpp import _CCPP_TOPICS
from app.services.model_adapter import ChatResult

MODEL_ID = "creox"

_GREETING_WORDS = {"hi", "hello", "hey", "namaste", "namaskar", "hii", "hiiiii"}
_GREETING_PHRASES = {"good morning", "good afternoon", "good evening"}

_GREETING_REPLY = (
    "Hello! I am CreoX, the built-in assistant of the Master CreoX API. "
    "Ask me a cybersecurity-awareness question — for example about phishing, "
    "ransomware, OTP fraud, UPI scams, or public WiFi safety — or a C/C++ "
    "question, for example about pointers, classes, or inheritance."
)

_CAPABILITIES_REPLY = (
    "I can answer cybersecurity-awareness questions on topics like password "
    "safety, phishing, ransomware, AI voice scams, OTP fraud, UPI and QR scams, "
    "public WiFi dangers, malware, two-factor authentication, safe browsing, "
    "fake customer-care numbers, and WhatsApp phishing links. I can also answer "
    "C/C++ questions — pointers, arrays, strings, structures, memory, classes, "
    "inheritance, polymorphism, templates and STL — each with its cheat-sheet "
    "source. I can also point you to this platform's own tools: "
    "POST /tools/password-check for password strength and "
    "POST /tools/phishing-check for suspicious URLs."
)

_FALLBACK_REPLY = (
    "I don't have a reliable answer for that one. I answer "
    "cybersecurity-awareness questions — try asking about phishing, ransomware, "
    "OTP fraud, UPI scams, or password safety — and C/C++ questions like "
    "pointers, classes, or inheritance. You can also use this platform's "
    "own tools: POST /tools/password-check for password strength and "
    "POST /tools/phishing-check for suspicious URLs."
)

# topic -> (keywords, answer). Keywords are matched as whole words, except
# multi-word phrases which are matched as substrings of the normalized text.
_TOPICS: dict[str, tuple[list[str], str]] = {
    "ai voice scams": (
        ["voice cloning", "voice clone", "cloned voice", "ai voice", "ai call",
         "fake call", "deepfake voice", "voice scam"],
        "AI voice scams: scammers clone a real voice from a short audio clip "
        "and call family members pretending to be that person. 1) A sudden "
        "emergency call asking for money is the classic pattern — hang up and "
        "call the person back on their known number. 2) Never share OTPs or "
        "bank details on a call, even if the voice sounds familiar. 3) Agree "
        "on a family safe word for real emergencies. 4) Report the number to "
        "your telecom provider and the cybercrime portal.",
    ),
    "upi scams": (
        ["upi", "collect request", "collect-request", "qr code", "qr scam",
         "payment request", "gpay", "phonepe", "paytm", "bhim"],
        "UPI and QR scams: 1) You never need to enter a PIN or approve a "
        "collect request to RECEIVE money — any such request is fraud. "
        "2) Never scan a QR code sent by a stranger to 'receive' a payment; "
        "QR codes are for paying, not receiving. 3) Verify the receiver's "
        "name in your UPI app before confirming any payment. 4) If you paid a "
        "scammer, report it in your bank app and on the cybercrime portal "
        "immediately — speed matters for freezing the money.",
    ),
    "whatsapp phishing": (
        ["whatsapp"],
        "WhatsApp phishing links: 1) Links promising prizes, jobs, or 'account "
        "verification' in forwarded messages are usually traps — do not tap "
        "them. 2) Check the sender: scammers impersonate banks, delivery "
        "companies, and even friends. 3) Never forward OTPs or verification "
        "codes, even to a contact who asks on WhatsApp — accounts get hijacked "
        "and then used to scam others. 4) Enable two-step verification in "
        "WhatsApp settings (a 6-digit PIN) so a stolen OTP alone is not enough.",
    ),
    "fake customer care": (
        ["customer care", "customer-care", "support number", "helpline",
         "toll free", "toll-free", "fake helpline"],
        "Fake customer-care numbers: scammers buy ads and post fake helpline "
        "numbers that appear above the real ones in search results. 1) Only "
        "use numbers from the company's official website or app, never from a "
        "search ad. 2) A real support agent will never ask for your OTP, PIN, "
        "or remote access to your phone. 3) If someone asks you to install a "
        "screen-sharing app for 'support', hang up — that is how accounts get "
        "drained. 4) Report fake numbers to the platform where you found them.",
    ),
    "otp fraud": (
        ["otp", "one time password", "one-time password", "verification code"],
        "OTP fraud: your OTP is the key to your account, and no legitimate "
        "company will ever ask for it. 1) Never share an OTP on a call, SMS, "
        "or chat — not even with someone claiming to be bank staff. "
        "2) Read the full OTP message: it says what it is for and warns never "
        "to share it. 3) If you shared an OTP by mistake, change your password "
        "and contact your bank immediately. 4) Use app-based authenticators "
        "where available — they cannot be forwarded like SMS codes.",
    ),
    "ransomware": (
        ["ransomware", "ransom", "locked files", "encrypted files", "hostage"],
        "Ransomware: malicious software that encrypts your files and demands "
        "payment to unlock them. 1) It usually starts with a phishing email "
        "attachment or a fake download — do not open unexpected attachments. "
        "2) Keep regular backups offline or in the cloud, so locked files are "
        "recoverable without paying. 3) Keep your OS and apps updated — many "
        "attacks use known, patched flaws. 4) Never pay the ransom: payment "
        "does not guarantee your files back and marks you as a payer.",
    ),
    "phishing": (
        ["phishing", "phish", "fake link", "suspicious link", "fraudulent email",
         "scam email", "spoof", "phishing email"],
        "Phishing: fake messages designed to steal your login or money. "
        "1) Check the sender address carefully — scammers use lookalike "
        "domains (e.g. support-paytm.com instead of paytm.com). 2) Hover over "
        "links before tapping; a mismatch between text and destination is a "
        "red flag. 3) Urgency ('account will close in 1 hour') is a pressure "
        "tactic — slow down and verify through the official app or website. "
        "4) You can also check a suspicious URL with this platform's own "
        "POST /tools/phishing-check endpoint.",
    ),
    "password safety": (
        ["password", "passwords", "passcode", "passphrase", "credential",
         "credentials", "breach", "leaked"],
        "Password safety: 1) Use a long, unique password for every important "
        "account — a password manager makes this practical. 2) Never reuse "
        "your email password anywhere else; one leak then opens everything. "
        "3) Turn on two-factor authentication wherever it is offered. "
        "4) You can check a password's strength with this platform's own "
        "POST /tools/password-check endpoint — it is assessed in memory and "
        "never stored.",
    ),
    "malware": (
        ["malware", "virus", "trojan", "spyware", "infected", "malicious app"],
        "Malware: 1) Install apps only from the official Play Store or App "
        "Store — APKs shared on chat groups are a common infection route. "
        "2) Check app permissions: a torch app does not need your contacts or "
        "SMS. 3) Keep your phone and apps updated; updates close the holes "
        "malware uses. 4) If your phone starts showing pop-up ads, draining "
        "battery, or sending messages by itself, uninstall recently added apps "
        "and run a scan.",
    ),
    "two factor authentication": (
        ["two factor", "two-factor", "2fa", "authenticator", "second factor"],
        "Two-factor authentication (2FA): even if someone steals your password, "
        "a second factor stops them. 1) Prefer app-based authenticator codes "
        "over SMS codes — SMS can be intercepted. 2) Save your backup codes "
        "somewhere safe when you enable 2FA. 3) Never share a 2FA code with "
        "anyone, including 'support' staff. 4) Enable 2FA first on your email, "
        "bank, and cloud accounts — email is the master key to password resets.",
    ),
    "public wifi": (
        ["public wifi", "public wi-fi", "free wifi", "hotspot", "open network"],
        "Public WiFi dangers: open networks let attackers snoop on unencrypted "
        "traffic. 1) Avoid banking or sensitive logins on public WiFi; use "
        "mobile data for those. 2) If you must use it, use a reputable VPN. "
        "3) Turn off auto-connect and file sharing, and forget the network "
        "afterwards. 4) Watch for 'evil twin' networks — a hotspot named "
        "exactly like the cafe's official one, run by an attacker.",
    ),
    "safe browsing": (
        ["safe browsing", "browser safety", "https", "secure site",
         "private browsing", "cookies"],
        "Safe browsing: 1) Look for https and the correct domain before "
        "entering any login or payment detail. 2) Keep your browser updated "
        "and be careful with extensions — they can read page content. "
        "3) Use private browsing on shared computers and always log out. "
        "4) Clear saved passwords from browsers you do not control, and use a "
        "password manager instead of letting every site remember you.",
    ),
}

_CAPABILITY_PHRASES = ("what can you do", "kya kar sakte", "what do you do")


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def _last_user_message(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, dict):
            role, content = m.get("role"), m.get("content", "")
        else:
            role, content = getattr(m, "role", None), getattr(m, "content", "")
        if role == "user":
            return str(content)
    if messages:
        m = messages[-1]
        return str(m.get("content", "") if isinstance(m, dict) else getattr(m, "content", ""))
    return ""


class CreoXEngine:
    """Deterministic, offline cybersecurity-awareness engine.

    ``temperature`` is accepted for interface compatibility with the
    ModelAdapter protocol but has no effect — answers are fixed by the
    knowledge base, which is what makes the engine reproducible.
    """

    def __init__(self, temperature: float | None = None):
        self.temperature = temperature

    def _answer(self, text: str) -> str:
        normalized = _normalize(text)
        words = normalized.split()
        tokens = set(words)

        # Greetings: only when the message is essentially just a greeting.
        if normalized.strip() in _GREETING_PHRASES or (
            words and words[0] in _GREETING_WORDS and len(words) <= 3
        ):
            return _GREETING_REPLY

        # Capabilities: explicit "what can you do" style questions.
        if any(p in normalized for p in _CAPABILITY_PHRASES) or (
            len(words) <= 4 and "help" in tokens
        ):
            return _CAPABILITIES_REPLY

        # Topic matching: count distinct matched keywords per topic.
        # Cyber topics first (existing behaviour unchanged), then the
        # separate C/C++ module — so a cyber question never changes meaning.
        for topics in (_TOPICS, _CCPP_TOPICS):
            best_topic, best_score = None, 0
            for topic, (keywords, _answer) in topics.items():
                score = 0
                for kw in keywords:
                    if " " in kw:
                        if kw in normalized:
                            score += 1
                    elif kw in tokens:
                        score += 1
                if score > best_score:
                    best_topic, best_score = topic, score
            if best_topic is not None:
                return topics[best_topic][1]
        return _FALLBACK_REPLY

    def complete(self, messages: list, model: str) -> ChatResult:
        text = _last_user_message(messages)
        reply = self._answer(text)
        prompt_tokens = sum(len(str(
            m.get("content", "") if isinstance(m, dict)
            else getattr(m, "content", "")).split()) for m in messages)
        return ChatResult(reply=reply, model=model,
                          prompt_tokens=prompt_tokens,
                          completion_tokens=len(reply.split()))
