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

BENIGN_CLASSES = [
    "benign",
    "safe",
    "legitimate",
    "clean",
    "trusted",
    "secure"
]

def is_class_malicious(class_name: str) -> bool:
    if not class_name:
        return False
    return class_name.lower().strip() in MALICIOUS_CLASSES

def normalize_class_name(class_name: str) -> str:
    if not class_name:
        return "unknown"
    
    normalized = class_name.lower().strip()
    
    if normalized in MALICIOUS_CLASSES:
        return "malicious"
    elif normalized in BENIGN_CLASSES:
        return "benign"
    else:
        return normalized

def map_prediction_class(prediction_value: str) -> tuple[bool, str]:
    if not prediction_value:
        return False, "unknown"
    
    normalized = prediction_value.lower().strip()
    
    if normalized in MALICIOUS_CLASSES:
        return True, "malicious"
    
    if normalized in BENIGN_CLASSES:
        return False, "benign"
    
    if any(malicious in normalized for malicious in MALICIOUS_CLASSES):
        return True, "malicious"
    
    if any(benign in normalized for benign in BENIGN_CLASSES):
        return False, "benign"
    
    return False, "unknown"