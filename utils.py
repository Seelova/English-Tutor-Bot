import random

def store_answer(role, answer):
    with open(r'dialog.txt', 'r', encoding='utf-8') as file:
        dialog = file.read()
    dialog += f"{role}: {answer}\n"
    with open(r'dialog.txt', 'w', encoding='utf-8') as file:
        file.write(dialog)

def get_current_dialog():
    with open(r'dialog.txt', 'r', encoding='utf-8') as file:
        dialog = file.read()
    return dialog

def get_random_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return random.choice(lines).strip()