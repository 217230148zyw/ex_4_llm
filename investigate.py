## Import the necessary modules
import json
from ollama import chat

## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result
MODEL = "qwen3:8b"
ITEMS_FILE = "found_items.json"
OUTPUT_FILE = "output/match_result.json"

## Build your prompt based on the description the user provides 
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.

def build_prompt(description, available_items):
    system_prompt = (
        "Rules for the Model:\n"
        "- The model must use only the given JSON file\n"
        "- Not all the details of an item must match to be a possible match.\n"
        "- Only JSON must be returned, with exactly the following structure:\n"
        "{\n"
        '        "matches": ["ITEM_ID"],\n'
        '        "confidence": "LOW"\n'
        "}\n"
        '\n'
        '- "matches" contains all the possible matches\n'
        '- "confidence" measures how confident the model is about the matches.\n'
        '- It must be exactly one of: LOW, MEDIUM, HIGH.\n'
        '- If there is no match the model must return an empty list for "matches".'
    )

    user_prompt = (
        f"User's lost item description: {description}\n\n"
        "These are the available unclaimed items in the lost-and-found database "
        "(given as JSON):\n"
        f"{json.dumps(available_items, indent=2, ensure_ascii=False)}\n\n"
        "Decide which items are possible matches for the user's description. "
        "Remember: not every detail has to match. "
        "Return ONLY the JSON object described in the rules, with no extra text."
    )

    return system_prompt, user_prompt

    

## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.message.content

## Logic to parse the response from Qwen and return the result. 
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    start = response_text.find("{")
    end = response_text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in the model response.")
    return json.loads(response_text[start:end + 1])
    


## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False

    if "matches" not in result or "confidence" not in result:
        return False

    matches = result["matches"]
    confidence = result["confidence"]

    if not isinstance(matches, list):
        return False

    if not isinstance(confidence, str) or confidence not in ("LOW", "MEDIUM", "HIGH"):
        return False
    valid_ids = {item["id"] for item in available_items}
    for item_id in matches:
        if not isinstance(item_id, str) or item_id not in valid_ids:
            return False

    return True

## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
""" 
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================

Describe the item you lost: I lost a black bag somewhere

Searching for possible matches...

MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM

Possible matches:

ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15

Result saved to output/match_result.json
 """
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print()

    matches = result["matches"]
    items_by_id = {item["id"]: item for item in available_items}

    if not matches:
        print("No matches were found for this description.")
        print(f"Possible matches: {matches}")
        return

    print("Possible matches:")
    print()
    for item_id in matches:
        item = items_by_id.get(item_id, {})
        print(f"ID: {item_id}")
        print(f"Item: {item.get('item', 'N/A')}")
        print(f"Color: {item.get('color', 'N/A')}")
        print(f"Location: {item.get('location', 'N/A')}")
        print(f"Date found: {item.get('date', 'N/A')}")
        print()


## Control center for the entire program.
def main():
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    print()
    items = load_items(ITEMS_FILE)
    available_items = get_unclaimed_items(items)
    description = input("Describe the item you lost: ")
    print()
    print("Searching for possible matches...")
    print()
    system_prompt, user_prompt = build_prompt(description, available_items)
    response_text = ask_qwen(system_prompt, user_prompt)
    result = parse_response(response_text)
    if not validate_result(result, available_items):
        print("Warning: the model returned an invalid result; using an empty match set.")
        result = {"matches": [], "confidence": "LOW"}
        display_matches(result, available_items)
    save_result(result, OUTPUT_FILE)
    print(f"Result saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()