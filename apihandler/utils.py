# A SET OF USEFUL TOOLS

def normalize_email(email: str) -> str:
    return "" if (email == "") or (email is None) else email.lower().strip()