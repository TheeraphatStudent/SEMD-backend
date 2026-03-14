MALICIOUS_CLASSES = [
    "malicious",
    "malware", 
    "phishing",
    "spam",
    "scam",
    "fraud",
    "trojan",
    "virus",
    "ransomware",
    "adware",
    "spyware"
]

def is_class_malicious(class_name: str) -> bool:
    if not class_name:
        return False
    return class_name.lower().strip() in MALICIOUS_CLASSES

def normalize_class_name(class_name: str) -> str:
    if not class_name:
        return "malicious"
    return class_name.lower().strip()