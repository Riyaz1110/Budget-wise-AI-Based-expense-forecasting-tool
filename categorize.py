import re

CATEGORY_KEYWORDS = {
    "Groceries": ["supermarket", "grocery", "food", "vegetable", "store"],
    "Rent": ["rent", "apartment", "lease", "housing"],
    "Transport": ["bus", "train", "uber", "fuel", "taxi", "cab"],
    "Utilities": ["electricity", "water", "internet", "bill", "gas"],
    "Entertainment": ["movie", "game", "netflix", "music", "concert"],
    "Salary": ["salary", "income", "bonus", "payroll"],
    "Shopping": ["amazon", "clothes", "mall", "electronics"]
}

def categorize_transaction(description):
    desc = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{kw}\b", desc) for kw in keywords):
            return category
    return "Uncategorized"
