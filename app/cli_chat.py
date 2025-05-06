import requests
from colorama import init, Fore, Style


init()

print(Fore.YELLOW + "Legal Doc Assistant CLI" + Style.RESET_ALL)
print("Type 'exit' to quit.\n")

while True:
    user_input = input(Fore.CYAN + "You: " + Style.RESET_ALL)
    if user_input.lower() in ["exit", "quit"]:
        break

    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"text": user_input}
    )

    if response.status_code == 200:
        bot_response = response.json().get("response", "[No response]")
        print(Fore.GREEN + "Bot:" + Style.RESET_ALL, bot_response)
    else:
        print(Fore.RED + "Error:", response.status_code, Style.RESET_ALL)
