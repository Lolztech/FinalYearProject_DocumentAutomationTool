from app.llm import (
    classify_doc_intent,
    classify_field_input,
    classify_confirmation_context,
    classify_clause_tag,
    extract_field_value,
    classify_rent_input,
)

def main_menu():
    print("\nLegal Doc Assistant — Classifier Tester")
    print("Choose a classifier to test:")
    print("1 ➔ classify_doc_intent")
    print("2 ➔ classify_field_input")
    print("3 ➔ classify_confirmation_context")
    print("4 ➔ classify_clause_tag")
    print("5 ➔ extract_field_value")
    print("6 ➔ classify_rent_input")
    print("exit ➔ Exit\n")

def run_advanced_tester():
    while True:
        main_menu()
        choice = input("Your choice: ").strip().lower()

        if choice in {"exit", "quit"}:
            print("Exiting...")
            break

        if choice not in {"1", "2", "3", "4", "5", "6"}:
            print("Invalid choice. Try again.")
            continue

        print(f"\n[INFO] Selected Classifier: {choice}")
        print("Type 'back' to return to main menu.\n")

        while True:
            user_input = input("User input ➔ ").strip()
            if user_input.lower() in {"back", "menu"}:
                break
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting...")
                return

            if choice == "1":
                result = classify_doc_intent(user_input)

            elif choice == "2":
                field_name = input("Enter field name ➔ ").strip()
                field_question = input("Enter field question ➔ ").strip()
                result = classify_field_input(user_input, field_name, field_question)

            elif choice == "3":
                result = classify_confirmation_context(user_input)

            elif choice == "4":
                result = classify_clause_tag(user_input)

            elif choice == "5":
                field_name = input("Enter field name ➔ ").strip()
                field_question = input("Enter field question ➔ ").strip()
                result = extract_field_value(user_input, field_name, field_question)
            
            elif choice == "6":
                result = classify_rent_input(user_input)

            print("\nResult:", result)
            print("-" * 50)

if __name__ == "__main__":
    run_advanced_tester()
