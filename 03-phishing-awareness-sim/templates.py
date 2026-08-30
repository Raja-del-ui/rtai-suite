"""Simulation templates: each embeds deliberate, teachable red flags."""

TEMPLATES = {
    "password_expiry": {
        "name": "Password Expiry Notice",
        "scenario": "IT sends an urgent password-expiration warning with a reset link.",
        "red_flags": [
            {"flag": "lookalike sender domain", "why": f"mail comes from {{{{sender_domain}}}} instead of the real company domain"},
            {"flag": "urgency + threat language", "why": "'within 24 hours or access is revoked' pressures quick action"},
            {"flag": "generic greeting", "why": "'Dear User' instead of the recipient's real name"},
            {"flag": "mismatched link text vs URL", "why": "button says 'Company Portal' but points at the lookalike domain"},
        ],
        "link_label": "Company Portal",
    },
    "hr_bonus_letter": {
        "name": "Confidential HR Bonus Letter",
        "scenario": "HR shares a confidential compensation document that requires 'verification'.",
        "red_flags": [
            {"flag": "curiosity bait subject", "why": "confidential bonuses trigger clicks"},
            {"flag": "sent outside working hours context", "why": "unusual timing is a classic social-engineering tell"},
            {"flag": "requests credentials to 'view document'", "why": "legitimate HR never needs your password to share a file"},
            {"flag": "reply-to differs from from", "why": "replies silently route to the attacker"},
        ],
        "link_label": "Secure Document Portal",
    },
    "invoice_attachment": {
        "name": "Overdue Invoice",
        "scenario": "Finance receives an overdue-invoice notice referencing a plausible PO number.",
        "red_flags": [
            {"flag": "plausible but wrong PO number", "why": "specificity creates false legitimacy"},
            {"flag": "payment urgency with bank-change hint", "why": "bank-detail changes are the #1 BEC payout trick"},
            {"flag": "attachment lure wording", "why": "'details attached' — in this simulation nothing harmful is ever attached"},
            {"flag": "signature lacks contactable phone", "why": "no verifiable callback channel"},
        ],
        "link_label": "Invoice Details",
    },
    "package_delivery": {
        "name": "Missed Package Delivery",
        "scenario": "A courier claims a parcel could not be delivered and asks to reschedule.",
        "red_flags": [
            {"flag": "unsolicited delivery notice", "why": "recipient likely expects no package"},
            {"flag": "small fee request framing", "why": "'1.99 redelivery fee' normalizes entering card details"},
            {"flag": "short-lived link pressure", "why": "'link expires today' forces haste"},
            {"flag": "brand-adjacent domain", "why": "courier name embedded in an unrelated TLD"},
        ],
        "link_label": "Reschedule Delivery",
    },
}
