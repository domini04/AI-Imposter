import random

ADJECTIVES = [
    "Witty", "Clever", "Silent", "Sneaky", "Wise", "Brave", "Calm", "Eager",
    "Gentle", "Happy", "Jolly", "Kind", "Lively", "Nice", "Proud", "Silly",
]
ANIMALS = [
    "Walrus", "Cat", "Wolf", "Dog", "Lion", "Tiger", "Bear", "Fox", "Shark",
    "Eagle", "Owl", "Hawk", "Snake", "Rabbit", "Deer", "Goat",
]

def generate_unique_nicknames(count: int) -> list[str]:
    """
    Generates a list of unique, random nicknames.

    Args:
        count: The number of unique nicknames to generate.

    Returns:
        A list of strings, where each string is a unique nickname.
    
    Raises:
        ValueError: If the requested count is larger than the number of
                    possible unique combinations.
    """
    possible_combinations = len(ADJECTIVES) * len(ANIMALS)
    if count > possible_combinations:
        raise ValueError("Cannot generate more unique nicknames than possible combinations.")

    used_nicknames = set()
    nicknames = []
    while len(nicknames) < count:
        adjective = random.choice(ADJECTIVES)
        animal = random.choice(ANIMALS)
        nickname = f"{adjective} {animal}"
        if nickname not in used_nicknames:
            used_nicknames.add(nickname)
            nicknames.append(nickname)
    
    return nicknames
