import requests
import json
from app.schemas import SCHEMAS
from docxtpl import DocxTemplate
import datetime
import os

LLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:11434")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3:8b")


def llama_answer(user_input: str, active_schema: str = None, current_field: str = None, current_question: str = None, context: str = None, recent_messages: list = None, slots: dict = None, user_state: str = "answer") -> str:
    """
    Calls the local LLaMA 3 model and returns a structured assistant-style reply.
    If schema context is available, it's used to generate contextual legal answers.
    """

    schema_valid = active_schema in SCHEMAS

    if recent_messages:
        history_snippet = "\n".join([
            f"User: {msg['user']}\nAssistant: {msg.get('bot', '[no reply yet]')}"
            for msg in recent_messages[-3:]
        ])
    else:
        history_snippet = ""

    if slots:
        slots_snippet = json.dumps(slots, indent=2)
        slots_snippet = f"Current information collected so far:\n{slots_snippet}\n"
    else:
        slots_snippet = ""

    if schema_valid:
        expected_fields = []

        for field in SCHEMAS[active_schema]["fields"]:
            if "name" in field and "question" in field:
                if "depends_on" not in field or evaluate_condition(field["depends_on"], slots or {}):
                    expected_fields.append(f"- {field['name']} ({field['question']})")
        
        expected_fields_snippet = "Expected fields to collect:\n" + "\n".join(expected_fields) + "\n"
    else:
        expected_fields_snippet = ""



    # ─────────────────────────────────────
    # CASE 1 — Schema + Field context (most helpful) / Session Termination
    # ─────────────────────────────────────
    if (current_field == "exit_confirmation") or (schema_valid and current_field and current_question):
        print(f"[DEBUG] CASE 1 triggered — Schema + Field context")
        if context:
            context_info = f"Context for this field:\n{context}\n\n"
        else:
            context_info = ""

        if current_field == "exit_confirmation":
            # Special case: user is thinking about exiting
            print(f"[DEBUG] exit_confirmation triggered in llm.py")
            prompt = (
                "It appears they may wish to abandon the session and discard the information collected so far.\n"
                "Respond briefly and politely:\n"
                "- Confirm if they truly want to exit.\n"
                "- Gently warn them that all progress will be lost.\n"
                "- Avoid discussing specific contract fields.\n"
                "- Then invite them to confirm their choice (yes/no)."
            )
        else:
            if user_state == "answer":
                guidance = (
                    "If the user's message answers the field question, proceed naturally.\n"
                    "If unsure, politely confirm the answer before proceeding."
                )
            elif user_state == "question":
                guidance = (
                    "The user seems to have a question.\n"
                    "- Answer the user and present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
                    "- Then gently guide them back to answering the current field."
                )
            elif user_state == "off_topic":
                guidance = (
                    "The user seems off-topic (e.g., chatting, joking, emotional).\n"
                    "- Answer the user and present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
                    "- Gently remind them that you are assisting in filling out a legal rental agreement.\n"
                    "- Redirect them back to answering the current field.\n"
                    "- Do not create new topics or prolong the off-topic conversation."
                )
            else:
                guidance = ""

            prompt = (
                "Important:\n"
                "- Speak directly to the user.\n"
                "- Do not prefix your reply with 'Assistant:' or 'Bot:' or any label.\n"
                "- Just answer naturally, as if talking directly to the user.\n\n"
                f"You are a contract assistant helping fill out a '{SCHEMAS[active_schema]['display_name']}'.\n"
                f"{slots_snippet}{expected_fields_snippet}Recent conversation history:\n{history_snippet}\n"
                f"User has been asked: '{current_question}'\n"
                f"Some context on the nature of the question only for you, the assistnat: {context_info}"
                f"User response: '{user_input}'\n"
                f"{guidance}"
            )


    # ─────────────────────────────────────
    # CASE 2 — Schema active, but no field info (e.g. post-summary questions)
    # ─────────────────────────────────────
    elif schema_valid:
        print(f"[DEBUG] CASE 2 triggered — Schema active, but no field info.")
        if user_state == "answer":
            guidance = (
                "The user may be providing a clarification or asking about the collected information.\n"
                "- Respond helpfully in context of the current form.\n"
                "- If appropriate, guide them back to confirming the collected data or proceeding to finalize the document."
            )
        elif user_state == "question":
            guidance = (
                "The user has a question.\n"
                "- Answer the user and present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
                "- Then politely encourage them to either review or finalize the document."
            )
        elif user_state == "off_topic":
            guidance = (
                "The user seems off-topic (e.g., chatting or emotional).\n"
                "- Answer the user and present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
                "- Remind them you are assisting in completing the document.\n"
                "- Steer the conversation back to reviewing or finalizing the collected data."
            )
        else:
            guidance = ""

        prompt = (
            "Important:\n"
            "- Speak directly to the user.\n"
            "- Do not prefix your reply with 'Assistant:' or 'Bot:' or any label.\n"
            f"The user is currently filling out a '{SCHEMAS[active_schema]['display_name']}'.\n"
            f"{slots_snippet}{expected_fields_snippet}Recent conversation history:\n{history_snippet}\n"
            f"Their most recent message was:\n{user_input}\n"
            f"{guidance}"
        )

    # ─────────────────────────────────────
    # CASE 3 — No schema yet (doc selection fallback)
    # ─────────────────────────────────────
    else:
        print(f"[DEBUG] CASE 3 triggered — No schema selected yet.")
        print(f"[DEBUG] User input: {user_input}")
        print(f"[DEBUG] Detected user_state: {user_state}")
        if user_state == "answer":
            print("[DEBUG] User answered with a document choice (probably). Guiding to confirmation.")
            guidance = (
                "You are a Assued Shorthold Tennancy agreemetn document automation bot powered by AI, and for you to initiate your document drafting functions you need the user to say 'Rental agreement' and confirm that this is what they want\n"
                "Your goal is to guide the user to pick one of the supported contract types which is only a Rental Agreement.\n"
                "- The user needs to say 'I want a rental agreement', your goal it to get them to say that\n"
                "- If they go off-topic, gently remind them of the available options."
            )

        elif user_state in {"question", "ask_about_rental", "ask_about_nda"}:
            print("[DEBUG] User asked a question about the contracts or assistant. Responding normally.")
            guidance = (
                "The user has asked a question.\n"
                "- Present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
                "- If the user naturally expresses interest, invite them to proceed with creating a Rental Agreement.\n"
            )

        elif user_state == "off_topic" or user_state in {"none"}:
            print("[DEBUG] User went off-topic. Acknowledge briefly and redirect to picking a document.")
            guidance = (

                "- Politely acknowledge and answer their statement in whatever format you deem fit to do so.\n"
                "- Gently redirect them back to saying they want a Rental Agreement.\n"
                "- Present information clearly. You can use bullets, paragraphs, and empty lines where appropriate to make the information easy to read.\n"
            )
        else:
            print("[DEBUG] Unknown user_state detected. Defaulting to polite redirection.")
            guidance = "Answer user statement and gently redirect them back to picking one of the two supported document types"

        prompt = (
        "Important:\n"
        "- Speak directly to the user.\n"
        "- Do not prefix your reply with 'Assistant:' or 'Bot:' or any label.\n"
        "You only support generating the following contract type:\n"
        "- Rental Agreement (rental_agreement)\n"
        f"{slots_snippet}{expected_fields_snippet}Recent conversation history:\n{history_snippet}\n"
        f"User: {user_input}\n"
        f"{guidance}"
    )



    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt,
            "temperature": 0.4,
            "top_p": 0.9,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.1,
            "stream": False
        })
        res.raise_for_status()
        response = res.json().get("response", "").strip()
        return response

    except Exception as e:
        return f"[LLM Error: {str(e)}]"
    

def generate_greeting():
    prompt = (
        "You are a helpful and professional legal document assistant. "
        "Greet the user in a friendly but concise way. "
        "Let them know you’re here to help them generate a rental agreement for a property in England or Wales.\n\n"

        "Explain briefly:\n"
        "- Once they select the document type (Rental Agreement), you will ask them a series of structured questions.\n"
        "- The user can stop at any time by asking you to terminate the session.\n"
        "- At any point, they can also ask questions about the fields or the process.\n"
        "- After each answer, the tool will ask for confirmation in case of mistakes.\n"
        "- At the end, they can edit any previously filled field before the final contract is generated.\n"
        "- Once a document is selected, a progress tracker will appear on the left showing how many questions have been answered.\n\n"

        "Finish your greeting by politely prompting the user to type something to begin."
    )

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.5,
            "top_p": 0.9,
            "presence_penalty": 0.2,
            "frequency_penalty": 0.1
        })
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as e:
        return f"[LLM Error: {str(e)}]"



def classify_doc_intent(user_input: str) -> str:
    """
    Classifies whether the user wants to start a document, ask a question, go off-topic, or exit.
    Returns one of: 'start_rental', 'question', 'off_topic', 'terminate_session'
    """

    prompt = f"""
You are a classification engine for a legal document assistant.

Analyze the user's message carefully:

"{user_input}"

Classify it as strictly one of the following:
- start_rental: The user explicitly wants to create a rental agreement.
- question: The user is asking a question about rental agreements, NDAs, the assistant, or anything related.
- off_topic: The message is casual, playful, emotional, or unrelated to documents.
- terminate_session: The user expresses a desire to stop, quit, cancel, or exit.

Important rules:
- Prefer "question" generously if the user is asking anything, even if slightly unrelated.
- Only "off_topic" if the message is random, emotional, or has no relevance.
- If in doubt between "question" and "off_topic", prefer "question".
- If the user says anything like "I want to stop", "I want this over", "I want to end this", "I want to quit", "I'm done", "no more", "can we stop", "I don't want to continue", **always** classify as terminate_session.
- Prefer terminate_session aggressively if the user sounds like they are expressing ending the task.
- If unsure between "terminate_session" and other options, **prefer terminate_session**.

Respond only with one label: start_rental, question, off_topic, or terminate_session.
"""

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.2,
            "top_p": 1.0,
            "presence_penalty": 0,
            "frequency_penalty": 0
        })
        res.raise_for_status()
        return res.json().get("response", "off_topic").strip().lower()
    except Exception as e:
        return f"[LLM classification error: {str(e)}]"

    
    
def classify_field_input(user_input: str, field_name: str, field_question: str) -> str:
    """
    Classifies the user's message as:
    - answer: it's likely a direct answer to the current field
    - question: If they are asking *any* question about the current field, the form, the document, or the reason behind it.
    - off_topic: it's irrelevant small talk or unrelated
    - terminate_session: user desires to exit the process now
    """

    prompt = f"""
You are a classification assistant. A user is filling out a legal form.

The current field being asked is: "{field_name}"
The question shown to the user was: "{field_question}"

User message: "{user_input}"

Classify the user input as one of:
- answer: Only if they directly and clearly answer the question, providing a usable input.
- question: The user is asking for clarification, more information, or expressing confusion.
- off_topic: If their message is unrelated, random, casual, playful, or otherwise not answering.
- terminate_session: If they express a desire to abandon or exit the session.

**Important:**
- Be very strict.
- If unsure, choose 'off_topic' rather than 'answer'.
- Only 'answer' if it would be valid to insert directly into the legal document.
- If the user's message starts with "why", "how", "what", "do I need", "is it necessary" — assume it is a question.
- If the user's message has a question mark (?) at the end of it - assume it is a question.
- Be generous in recognizing questions.
- Only classify as "off_topic" if it is completely irrelevant, joking, or random.
- If the user's message ends with phrases like "yes?", "right?", "correct?", "isn't it?", assume it is a question.


Respond with only one label: answer, question, off_topic, or terminate_session.
"""

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.2,
            "top_p": 1.0,
            "presence_penalty": 0,
            "frequency_penalty": 0
        })
        res.raise_for_status()
        return res.json().get("response", "off_topic").strip().lower()
    except Exception as e:
        return f"[classification error: {str(e)}]"
        

def classify_confirmation_context(user_input: str) -> str:
    """
    Improved version: Classify if user input is a clean yes, no, question, off-topic, or exit.
    """
    prompt = f"""
You are an intent classifier helping with a legal document assistant.

Analyze the following user input carefully:

"{user_input}"

Your goal is to classify it into one of these categories:

- yes: The user clearly, directly, and affirmatively agrees (e.g., "yes", "yeah", "absolutely", "of course").
- no: The user clearly, directly, and affirmatively disagrees (e.g., "no", "nope", "absolutely not").
- question: The user is asking for clarification, more information, or expressing confusion.
- off_topic: The user is chatting, joking, expressing emotions, or saying something unrelated.
- terminate_session: The user expresses a desire to quit, cancel, or exit the document creation.

Important rules:
- Only classify as "yes" or "no" if the user's ENTIRE message is a clear answer.
- If the message is long, contains unrelated parts, or asks a question, prefer "question" or "off_topic".
- If the message suggests abandoning the task, classify as "terminate_session".

Respond with ONLY one word: yes, no, question, off_topic, or terminate_session.
"""

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.2,
            "top_p": 1.0,
            "presence_penalty": 0,
            "frequency_penalty": 0
        })
        res.raise_for_status()
        response = res.json().get("response", "").strip().lower()

        if response in ["yes", "no", "question", "off_topic", "terminate_session"]:
            return response
        else:
            return "off_topic"

    except Exception as e:
        return "off_topic"

    
    
def extract_field_value(user_input: str, field_name: str, field_question: str) -> str:
    """
    Extracts the most likely answer to the field from the user input.
    """
    prompt = f"""
You are extracting values for a contract form.

Field name: "{field_name}"
Question: "{field_question}"
User response: "{user_input}"

Extract only the user's actual answer (the value you would save into the form), and nothing else.
Respond with just the value. 
Only return in BLOCK CAPITALS if the field name includes the word "name" (e.g., tenant_name, landlord_name, company_name).
If the field is specifically a person's **full name** or a **company name**, return it in BLOCK CAPITALS.
Never capitalize values unless the field name includes "name" (e.g., tenant_name, landlord_name).
In all other cases — including fields like "payment_method", "rent_amount", etc. — return the value exactly as stated by the user, preserving their casing.
If the value is a date, return it in the format YYYY-MM-DD.
If the value is a number but spelled out, convert the value to numeric ("one" becomes "1")
If the value is "yes" or "no" (in any case), return exactly "yes" or "no" in lowercase.
"""

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.1,
            "top_p": 0.8,
            "presence_penalty": 0,
            "frequency_penalty": 0.1
        })
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as e:
        return user_input  # fallback to full input
    




def classify_rent_input(user_input: str,) -> str:
    """
    Classifies rent review input into: fixed, fixed_percentage, fixed_increase, or cpi_indexed.
    """
    prompt = f"""
You are helping classify answers to a contract form for UK rental agreements.


Question asked: "Will the rent remain fixed throughout the tenancy, or is there a provision for annual increases (e.g., by a fixed percentage or linked to inflation)? Please explain how rent changes over time, if at all."
User response: "{user_input}"

You MUST classify the user's intention as ONE of the following options:

- fixed: The rent amount stays the same for the full term.
- fixed_percentage: The rent increases each term by a fixed percentage.
- fixed_increase: The rent increases each term my a fixed value amount
- cpi_indexed: The rent increases each term according to CPI inflation (consumer price index).

Choose the BEST match from the list above — return only the exact label (no explanation).

Examples:
- The rent will go up by 300 a year = fixed_increase
- The rent will go up 3% a year = fixed_percentage  
- It increases with inflation = cpi_indexed  
- Rent stays flat = fixed  
- +5% annually = fixed_percentage  
- Rent will rise with CPI index annually = cpi_indexed

Now classify this input:
"{user_input}"

Your response (choose only one: fixed, fixed_percentage, cpi_indexed, fixed_increase):
"""

    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.2,
            "top_p": 1.0,
            "presence_penalty": 0,
            "frequency_penalty": 0
        })
        res.raise_for_status()
        output = res.json().get("response", "").strip().lower()

        # Safety: enforce exact labels
        if output in {"fixed", "fixed_percentage", "cpi_indexed", "fixed_increase"}:
            return output
        return user_input  # fallback to raw input if unclassifiable
    except Exception:
        return user_input

    


def classify_clause_tag(clause_text: str) -> str:
    """
    Classify a user-supplied custom clause into the correct section of the tenancy agreement.
    """
    prompt = f"""
You are categorizing tenancy agreement clauses.

Given a clause, classify it into one of the following tags based on its topic:

- interpretation: Definitions, interpretive rules, or meanings of terms.
- additional_occupants: Clauses about non-tenant household members or occupancy limits.
- term_and_expiry: Anything about the start/end date, fixed term, or statutory continuation.
- termination_end_of_term: Conditions or notices relating to ending the tenancy at its natural expiry.
- rent_terms: Rent amounts, frequency, review terms, CPI/indexation rules, etc.
- included_charges: Which services (utilities, council tax, broadband) are or aren’t included in the rent.
- inventory_terms: Inventory checks, condition reports, acceptance, or disputes.
- tenant_obligations_use_of_premises: Pets, business use, behaviour, nuisance, or legal/moral use.
- tenant_obligations_security: Locks, alarms, leaving vacant, or securing the property.
- tenant_obligations_entry_and_inspections: Access rights for inspections, maintenance, or viewings.
- tenant_obligations_assignment: Transfer of the tenancy to someone else.
- tenant_obligations_subletting_whole: Subletting the entire property.
- tenant_obligations_subletting_part: Subletting a room or part of the property.
- tenant_obligations_subletting_restricted: Blanket bans on subletting.
- tenant_obligations_end_of_term: Keys, cleaning, rubbish, or vacating procedures.
- landlord_obligations_general: Possession at start, quiet enjoyment, repair exclusions.
- landlord_obligations_insurance: Property insurance, rent suspension due to damage.
- landlord_possession_rights: Statutory grounds (e.g. Schedule 2, Housing Act 1988).
- break_clause_tenant: Tenant’s right to serve break notice during the fixed term.
- break_clause_landlord: Landlord’s right to serve break notice during the fixed term.
- break_clause_landlord_sale: Landlord terminating tenancy to sell the property.
- break_clause_universal: Shared rules applying to both landlord and tenant break clauses.

Here is the clause to classify:
\"\"\"
{clause_text}
\"\"\"

Respond **only** with one of the section tags listed above (e.g., "tenant_obligations_use_of_premises").
"""
    try:
        res = requests.post(f"{LLAMA_API_URL}/api/generate", json={
            "model": LLAMA_MODEL,
            "prompt": prompt.strip(),
            "stream": False,
            "temperature": 0.3,
            "top_p": 0.95,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1
        })
        res.raise_for_status()
        return res.json().get("response", "").strip().lower()
    except Exception:
        return "general_provisions"

    

# NON LLM ITEMS -------------------------------------------------------------------------------------------------------------------------



def evaluate_condition(condition: str, slots: dict) -> bool:
    """
    Evaluates a 'depends_on' condition string against the current slots.
    """
    try:
        safe_slots = {k: v for k, v in (slots or {}).items() if isinstance(k, str)}
        return eval(condition, {}, safe_slots)
    except Exception as e:
        print(f"[DEBUG] Condition eval error for '{condition}': {e}")
        return False



def generate_contract_from_template(finalized_fields: dict) -> str:
    """
    Renders the tenancy agreement from a styled Word DOCX template using docxtpl.
    Returns the path to the generated .docx file.
    """
    template_path = "app/templates/rental_agreement_ast_2.docx"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rental_agreement_{timestamp}.docx"
    output_path = os.path.join("app", "output", filename)

    doc = DocxTemplate(template_path)
    doc.render(finalized_fields)
    doc.save(output_path)

    return output_path

