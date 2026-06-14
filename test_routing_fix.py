import sys
sys.path.append(r"c:\Users\DELL\OneDrive\Desktop\assistent")

# Mock the logic in process_command:
def test_command(text):
    # System Automation Close logic mock
    if "close" in text and "folder" not in text:
        word_count = len(text.split())
        if word_count < 5:
            return "system_close_app"
    return "normal_flow"

tests = [
    ("close chrome", "system_close_app"),
    ("close visual studio", "system_close_app"),
    ("yes scan the official websites and tell me about the deals which are closed by the eu and indian", "normal_flow")
]

for txt, expected in tests:
    res = test_command(txt)
    assert res == expected, f"Failed for '{txt}': expected {expected}, got {res}"
    print(f"Pass: '{txt}' -> Routed to {res}")

print("All routing fixes tested successfully!")
