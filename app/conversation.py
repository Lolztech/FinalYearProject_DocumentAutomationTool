from app.schemas import SCHEMAS
from app.llm import generate_greeting, llama_answer, classify_doc_intent, classify_confirmation_context, classify_rent_input, classify_field_input, extract_field_value, classify_clause_tag, generate_contract_from_template
import difflib
from typing import Dict, Any


class ConversationState:
    def __init__(self):
        self.greeted = False
        self.state = "doc_selection"  # Possible values: doc_selection, info_retrieval
        self.active_schema = None
        self.current_field_index = None
        self.slots = {}
        self.memory_notes = {}
        self.awaiting_confirmation = False
        self.pending_confirmation_value = None
        self.pending_confirmation_field = None
        self.prompted_for_doc_type = False
        self.all_information_gathered = False
        self.editing_mode = False
        self.awaiting_final_confirmation = False
        self.awaiting_generate_confirmation = False
        self.awaiting_edit_field_selection = False
        self.awaiting_doc_type_confirmation = False
        self.awaiting_tenant_count = False
        self.awaiting_tenant_name_index = None  # Index we're currently asking for
        self.tenant_fields_order = ["name", "email", "phone"]
        self.current_tenant_step = 0  # index in tenant_fields_order
        self.awaiting_additional_occupant_index = None  # For iterating additional occupants
        self.awaiting_additional_occupant_reset_confirmation = False 
        self.after_additional_occupant_recollection = False
        self.awaiting_tenant_reset_confirmation = False  # set when user wants to change tenant count
        self.after_tenant_recollection = False
        self.recollecting_dependent = False
        self.awaiting_custom_clause = False
        self.awaiting_custom_clause_index = None
        self.awaiting_custom_clause_entry = False
        self.awaiting_property_include = False
        self.awaiting_property_include_entry = False
        self.awaiting_shared_area = False
        self.awaiting_shared_area_entry = False
        self.awaiting_property_include_index = None
        self.awaiting_shared_area_index = None
        self.awaiting_utility_included = False
        self.awaiting_utility_included_entry = False
        self.awaiting_utility_included_index = None
        self.awaiting_which_utilities_not_included = False
        self.awaiting_which_utilities_not_included_entry = False
        self.awaiting_which_utilities_not_included_index = None
        self.awaiting_exit_confirmation = False
        self.recent_messages = []
        self.generated_contract = None






    def reset(self):
        self.__init__()

    def handle_user_message(self, user_input: str) -> str:

        # [1] Save the user's message *immediately* upon receiving it
        self.recent_messages.append({"user": user_input})

        # ─────────────────────────────────────────────────────────────
        # DEBUG HELPERS
        # ─────────────────────────────────────────────────────────────

        if user_input.strip().lower() == "debug_jump_to_utilities_included":
            print("[DEBUG] Shortcut triggered: debug_jump_to_utilities_included")

            self.active_schema = "rental_agreement"
            self.state = "info_retrieval"
            self.slots = {
                "tenant_count": 2,
                "tenant_info": [
                    {"name": "David", "email": "david@gmail.com", "phone": "1234567891"},
                    {"name": "Hugh", "email": "hugh@gmail.com", "phone": "1234567890"}
                ],
                "additional_occupants_check": "yes",
                "additional_occupants_count": 2,
                "additional_occupants": ["Tanya", "Lema"],
                "landlord_name": "Cris",
                "landlord_address": "123 Laugh Street",
                "landlord_email": "landlord@gmail.com",
                "landlord_phone": "12345677898",
                "notice_service_same_as_landlord": "yes",
                "property_address": "808 Caspian House, 9 Violet Road, W3 3NV",
                "property_description": "2 bedroom, 2 bathroom, 1 ensuite, 1 livingroom and kitchen",
                "property_includes_confirmation": "yes",
                "property_includes": ["grage", "back yard", "tennis court"],
                "shared_areas": "yes",
                "shared_areas_description": ["kitchen", "rooftop terrace", "kitchen"],
                "furnished": "yes",

            }

            self.current_field_index = 16  # index of 'utilities_included'
            expected_field = self._current_field()
            response = expected_field["question"]
            self.recent_messages.append({"user": user_input, "bot": response})
            return response
        

        if user_input.strip().lower() == "debug_jump_to_summary":
            print("[DEBUG] Shortcut triggered: debug_jump_to_summary")

            self.active_schema = "rental_agreement"
            self.state = "info_retrieval"
            self.current_field_index = 0
            self.slots = {
                "tenant_count": 2,
                "tenant_info": [
                    {"name": "Alice Johnson", "email": "alice@example.com", "phone": "07123456789"},
                    {"name": "Bob Smith", "email": "bob@example.com", "phone": "07987654321"}
                ],
                "additional_occupants_check": "yes",
                "additional_occupants_count": 1,
                "additional_occupants": ["Charlie"],
                "landlord_name": "John Landlord",
                "landlord_address": "10 Downing Street, London",
                "landlord_email": "landlord@example.com",
                "landlord_phone": "07000000000",
                "notice_service_same_as_landlord": "yes",
                "property_address": "42 Elm Street, London, E1 6AN",
                "property_description": "3 bed flat with 2 bathrooms and shared kitchen",
                "property_includes_confirmation": "yes",
                "property_includes": ["Garden", "Parking space"],
                "shared_areas": "yes",
                "shared_areas_description": ["Hallway", "Stairwell"],
                "furnished": "yes",
                "mortgage_check": "no",
                "rent_review_type": "fixed_percentage",
                "fixed_percentage_increase": "5",
                "weekly_rent": "300",
                "monthly_rent": "1300",
                "payment_method": "bank transfer",
                "payment_day": "1st of each month",
                "first_payment_amount": "1200",
                "first_payment_due_date": "1-1-2001",
                "deposit_amount": "1500",
                "deposit_protection_scheme": "MyDeposits",
                "lease_term": "2 years",
                "start_date": "1-1-2021",
                "end_date": "1-1-2022",
                "has_break_clause": "yes",
                "break_clause_notice": "2 months",
                "council_tax_included": "no",
                "utilities_included": "yes",
                "which_utilities_included": ["Electricity", "Gas", "Water"],
                "which_utilities_not_included": ["Internet"],
                "key_handover_date": "1-1-2021",
                "tenant_absence": "30",
                "right_to_rent_completed": "yes",
                "gas_safety_certificate": "yes",
                "energy_performance_certificate": "yes",
                "how_to_rent_booklet": "yes",
                "alterations_permitted": "no",
                "pets_allowed": "yes",
                "subletting_allowed": "no",
                "is_deed": "yes",
                "smoking_allowed": "no",
                "business_use_allowed": "no",
                "wants_custom_clauses": "yes",
                "custom_clauses": [
                    {"text": "Test Clause 1", "tag": "interpretation"},
                    {"text": "Test Clause 2", "tag": "interpretation"},

                    {"text": "Test Clause 3", "tag": "additional_occupants"},
                    {"text": "Test Clause 4", "tag": "additional_occupants"},

                    {"text": "Test Clause 5", "tag": "term_and_expiry"},
                    {"text": "Test Clause 6", "tag": "term_and_expiry"},

                    {"text": "Test Clause 7", "tag": "termination_end_of_term"},
                    {"text": "Test Clause 8", "tag": "termination_end_of_term"},

                    {"text": "Test Clause 9", "tag": "rent_terms"},
                    {"text": "Test Clause 10", "tag": "rent_terms"},

                    {"text": "Test Clause 11", "tag": "included_charges"},
                    {"text": "Test Clause 12", "tag": "included_charges"},

                    {"text": "Test Clause 13", "tag": "inventory_terms"},
                    {"text": "Test Clause 14", "tag": "inventory_terms"},

                    {"text": "Test Clause 15", "tag": "tenant_obligations_use_of_premises"},
                    {"text": "Test Clause 16", "tag": "tenant_obligations_use_of_premises"},

                    {"text": "Test Clause 17", "tag": "tenant_obligations_security"},
                    {"text": "Test Clause 18", "tag": "tenant_obligations_security"},

                    {"text": "Test Clause 19", "tag": "tenant_obligations_entry_and_inspections"},
                    {"text": "Test Clause 20", "tag": "tenant_obligations_entry_and_inspections"},

                    {"text": "Test Clause 21", "tag": "tenant_obligations_assignment"},
                    {"text": "Test Clause 22", "tag": "tenant_obligations_assignment"},

                    {"text": "Test Clause 23", "tag": "tenant_obligations_subletting_whole"},
                    {"text": "Test Clause 24", "tag": "tenant_obligations_subletting_whole"},

                    {"text": "Test Clause 25", "tag": "tenant_obligations_subletting_part"},
                    {"text": "Test Clause 26", "tag": "tenant_obligations_subletting_part"},

                    {"text": "Test Clause 27", "tag": "tenant_obligations_subletting_restricted"},
                    {"text": "Test Clause 28", "tag": "tenant_obligations_subletting_restricted"},

                    {"text": "Test Clause 29", "tag": "tenant_obligations_end_of_term"},
                    {"text": "Test Clause 30", "tag": "tenant_obligations_end_of_term"},

                    {"text": "Test Clause 31", "tag": "landlord_obligations_general"},
                    {"text": "Test Clause 32", "tag": "landlord_obligations_general"},

                    {"text": "Test Clause 33", "tag": "landlord_obligations_insurance"},
                    {"text": "Test Clause 34", "tag": "landlord_obligations_insurance"},

                    {"text": "Test Clause 35", "tag": "landlord_possession_rights"},
                    {"text": "Test Clause 36", "tag": "landlord_possession_rights"},

                    {"text": "Test Clause 37", "tag": "break_clause_tenant"},
                    {"text": "Test Clause 38", "tag": "break_clause_tenant"},

                    {"text": "Test Clause 39", "tag": "break_clause_landlord"},
                    {"text": "Test Clause 40", "tag": "break_clause_landlord"},

                    {"text": "Test Clause 41", "tag": "break_clause_landlord_sale"},
                    {"text": "Test Clause 42", "tag": "break_clause_landlord_sale"},

                    {"text": "Test Clause 43", "tag": "break_clause_universal"},
                    {"text": "Test Clause 44", "tag": "break_clause_universal"}
                ]

            }

            self.all_information_gathered = True
            self.awaiting_final_confirmation = True

            response = self._render_summary_and_ask_if_happy()
            self.recent_messages.append({"user": user_input, "bot": response})
            return response





        #------------------------------------------------------------------------------------------------------------------------------------------------------


        """
        Main conversational entry point.
        This dispatches behavior based on the current assistant state.
        """
        if not self.greeted:
            self.greeted = True
            greeting = generate_greeting()
            print(f"[DEBUG] Greeted user")
            self.recent_messages.append({"user": user_input, "bot": greeting})
            return greeting

        if self.awaiting_doc_type_confirmation:
            response = self.confirm_document_selection(user_input)
        elif self.state == "doc_selection":
            response = self._handle_doc_selection(user_input)
        elif self.state == "info_retrieval":
            response = self._handle_info_retrieval(user_input)
        else:
            response = "Unknown state. Please restart."
        
        # Save bot response
        if response and self.recent_messages:
            self.recent_messages[-1]["bot"] = response

        # Trim memory if necessary
        if len(self.recent_messages) > 10:
            self.recent_messages = self.recent_messages[-10:]

        return response

        
    def _list_doc_options(self) -> str:
        return "\n".join([f"- {v['display_name']} (`{k}`)" for k, v in SCHEMAS.items()])

    # ─────────────────────────────────────────────────────────────
    # DOC SELECTION STATE
    # ─────────────────────────────────────────────────────────────

    def _handle_doc_selection(self, user_input: str) -> str:
        print(f"[DEBUG] Entered _handle_doc_selection() with user_input: {user_input}")
        
        intent = classify_doc_intent(user_input)
        print(f"[DEBUG] classify_doc_intent: {intent}")

        if intent == "start_rental":
            print("[DEBUG] Detected intent: start_rental (user wants to create Rental Agreement)")
            self.awaiting_doc_type_confirmation = True
            self._pending_schema = "rental_agreement"
            self.prompted_for_doc_type = False
            response = "Just to confirm — would you like to generate a *Rental Agreement*? (yes/no)"

        elif intent == "start_nda":
            print("[DEBUG] Detected intent: start_nda (user wants to create NDA)")
            self.awaiting_doc_type_confirmation = True
            self._pending_schema = "nda"
            self.prompted_for_doc_type = False
            response = "Just to confirm — would you like to generate a *Non-Disclosure Agreement (NDA)*? (yes/no)"

        elif intent == "question":
            print("[DEBUG] Detected intent: question (user is asking something relevant)")
            self.prompted_for_doc_type = True
            answer = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema or "unknown",
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state="question"
            )
            print(f"[DEBUG] llama_answer response to question: {answer}")
            print("[DEBUG] Recent messages history:", self.recent_messages)
            response = f"{answer}"

        elif intent == "off_topic":
            print("[DEBUG] Detected intent: off_topic (user went casual or unrelated)")
            self.prompted_for_doc_type = True
            answer = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema or "unknown",
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state="off_topic"
            )
            print(f"[DEBUG] llama_answer response to off_topic: {answer}")
            print("[DEBUG] Recent messages history:", self.recent_messages)
            response = f"{answer}\n\nWhat kind of document would you like to create?"

        elif intent == "terminate_session":
            print("[DEBUG] Detected intent: terminate_session (user wants to quit)")
            self.reset()
            response = "Session aborted. Thank you for using the assistant."
            if self.recent_messages:
                print("[DEBUG] Updating last bot message to reflect session end.")
                self.recent_messages[-1]["bot"] = response
            return response

        else:
            print(f"[DEBUG] Unknown intent detected: {intent}. Falling back to polite redirect.")
            response = (
                "I'm here to help you create a Rental Agreement or NDA.\n"
                "Which document would you like to generate?"
            )

        if self.recent_messages:
            print("[DEBUG] Saving bot reply to recent_messages history.")
            self.recent_messages[-1]["bot"] = response

        print(f"[DEBUG] Returning final response: {response}")
        return response


    # ─────────────────────────────────────────────────────────────
    # INFO RETRIEVAL STATE
    # ─────────────────────────────────────────────────────────────

    def _handle_info_retrieval(self, user_input: str) -> str:
        print(f"[DEBUG] Entering _handle_info_retrieval with input: {user_input}")
        print(
            f"[DEBUG] Flags: "
            f"awaiting_confirmation={self.awaiting_confirmation}, "
            f"awaiting_edit_field_selection={self.awaiting_edit_field_selection}, "
            f"awaiting_final_confirmation={self.awaiting_final_confirmation}, "
            f"editing_mode={self.editing_mode}"
        )
        print(f"[DEBUG] Top of _handle_info_retrieval — awaiting_edit_field_selection={self.awaiting_edit_field_selection}")


        # Handle user desire to terminate session ------------------------------------------------------------------------------------------------------------------------------------------------

        if self.awaiting_exit_confirmation:
            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Confirming exit with input: {user_input}")
            print(f"[DEBUG] Interpretation: {interpretation}")

            if interpretation == "yes":
                response = "Session aborted. Thank you for using the assistant."
                self.recent_messages[-1]["bot"] = response  # Modify before reset
                self.reset()
                return response

            elif interpretation == "no":
                self.awaiting_exit_confirmation = False
                if hasattr(self, "saved_context_before_exit") and self.saved_context_before_exit:
                    question = self.saved_context_before_exit.get("current_question")
                    self.saved_context_before_exit = None
                    response = f"Okay, let's continue.\n{question}"
                else:
                    response = "Okay, let's continue."

                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation in {"question", "off_topic"}:
                confirmation_prompt = "The user is deciding whether to abandon the session and discard all collected information. Help clarify if they really want to exit."
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    context=confirmation_prompt,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Please confirm — do you want to abandon this session? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

        # Handle tenant name input (iteratively) ---------------------------------------------------------------------------
        
        if self.awaiting_tenant_name_index is not None and not self.awaiting_confirmation:
            print(f"[DEBUG] Entered tenant name collection block.")
            print(f"[DEBUG] Collecting '{self.tenant_fields_order[self.current_tenant_step]}' for tenant index: {self.awaiting_tenant_name_index}")
            print(f"[DEBUG] Current tenant_info[{self.awaiting_tenant_name_index}]: {self.slots['tenant_info'][self.awaiting_tenant_name_index]}")
            print(f"[DEBUG] User input: {user_input}")
            print(f"[DEBUG] Flags - editing_mode={self.editing_mode}, after_tenant_recollection={self.after_tenant_recollection}")

            index = self.awaiting_tenant_name_index
            field = self.tenant_fields_order[self.current_tenant_step]

            # Classify user input
            classification = classify_field_input(user_input, "tenant_info", f"What is the {field} of tenant {index + 1}?")
            print(f"[DEBUG] classify_field_input returned: {classification}")

            if classification == "answer":
                value = extract_field_value(user_input, "tenant_info", f"What is the {field} of tenant {index + 1}?")
                self.slots["tenant_info"][index][field] = value.strip()

                if self.editing_mode and not self.after_tenant_recollection:
                    print("[DEBUG] Editing mode active — field updated. Returning to summary.")
                    self.editing_mode = False
                    self.awaiting_tenant_name_index = None
                    self.current_tenant_step = 0
                    self.awaiting_final_confirmation = True
                    response = self._render_summary_and_ask_if_happy()
                    self.recent_messages[-1]["bot"] = response
                    return response
            
                # Move to next subfield
                self.current_tenant_step += 1

                if self.current_tenant_step < len(self.tenant_fields_order):
                    next_field = self.tenant_fields_order[self.current_tenant_step]
                    response = f"What is the {next_field} of tenant {index + 1}?"
                    return response
                else:
                    # Done with current tenant, move to next
                    self.current_tenant_step = 0
                    self.awaiting_tenant_name_index += 1

                    if self.awaiting_tenant_name_index < self.slots["tenant_count"]:
                        response = f"What is the name of tenant {self.awaiting_tenant_name_index + 1}?"
                        return response
                    else:
                        # Done with all
                        self.awaiting_tenant_name_index = None
                        self.awaiting_confirmation = True
                        self.pending_confirmation_field = "tenant_info"
                        self.pending_confirmation_value = self.slots["tenant_info"]

                        if self.editing_mode:
                            self.after_tenant_recollection = True
                            print("[DEBUG] Marking after_tenant_recollection = True (edit mode)")

                        # Format tenant summary
                        formatted_tenants = [
                            f"Tenant {i+1}: {t['name']}, {t['email']}, {t['phone']}"
                            for i, t in enumerate(self.slots["tenant_info"])
                        ]
                        response = "Saving tenant list:\n" + "\n".join(formatted_tenants) + "\n\nIs this correct? (yes/no)"


            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification in {"question", "off_topic"}:
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="tenant_info",
                    current_question=f"What is the {field} of tenant {index + 1}?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nLet's get back to it: What is the {field} of tenant {index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = f"Sorry, I didn’t catch the name. What is the {field} of tenant {index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            if None in self.slots["tenant_info"]:
                next_index = self.slots["tenant_info"].index(None)
                print(f"[DEBUG] Continuing full tenant collection. Next index: {next_index}")
                self.awaiting_tenant_name_index = next_index
                response = f"What is the name of tenant {next_index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            print(f"[DEBUG] Tenant collection complete. Final list: {self.slots['tenant_info']}")
            self.awaiting_tenant_name_index = None
            self.current_tenant_step = 0 
            self.pending_confirmation_value = self.slots["tenant_info"]
            self.pending_confirmation_field = "tenant_info"
            self.awaiting_confirmation = True

            if self.editing_mode:
                self.after_tenant_recollection = True
                print("[DEBUG] Marking after_tenant_recollection = True (edit mode)")

            # Format tenant summary
            formatted_tenants = [
                f"Tenant {i+1}: {t['name']}, {t['email']}, {t['phone']}"
                for i, t in enumerate(self.slots["tenant_info"])
            ]
            response = "Saving tenant list:\n" + "\n".join(formatted_tenants) + "\n\nIs this correct? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response
        


        # Handle additional occupant name input (iteratively) - name collection ---------------------------------------------------------------------------

        if self.awaiting_additional_occupant_index is not None and not self.awaiting_confirmation:
            print(f"[DEBUG] Entered additional occupant name collection block.")
            print(f"[DEBUG] additional_occupant_index: {self.awaiting_additional_occupant_index}")
            print(f"[DEBUG] Current additional_occupants slot: {self.slots.get('additional_occupants')}")
            print(f"[DEBUG] User input for additional occupant {self.awaiting_additional_occupant_index + 1}: {user_input}")
            print(f"[DEBUG] Flags - editing_mode={self.editing_mode}, after_additional_occupant_recollection={self.after_additional_occupant_recollection}")

            index = self.awaiting_additional_occupant_index

            # Classify user input
            classification = classify_field_input(user_input, "additional_occupants", f"What is the name of additional occupant {index + 1}?")
            print(f"[DEBUG] classify_field_input returned: {classification}")

            if classification == "answer":
                # Extract clean name
                extracted_name = extract_field_value(user_input, "additional_occupants", f"What is the name of additional occupant {index + 1}?")
                self.slots["additional_occupants"][index] = extracted_name.strip()
                print(f"[DEBUG] Stored additional occupant name: {extracted_name.strip()}")

            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification in {"question", "off_topic"}:
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="additional_occupants",
                    current_question=f"What is the name of additional occupant {index + 1}?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nLet's get back to it: What is the name of additional occupant {index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = f"Sorry, I didn’t catch the name. What is the name of additional occupant {index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            # Now handle progression logic
            if self.editing_mode and not self.after_additional_occupant_recollection:
                print("[DEBUG] Editing mode active — stopping iteration early and summarizing.")
                self.editing_mode = False
                self.awaiting_additional_occupant_index = None
                self.awaiting_final_confirmation = True
                response = self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            if None in self.slots["additional_occupants"]:
                next_index = self.slots["additional_occupants"].index(None)
                print(f"[DEBUG] Continuing full additional occupant collection. Next index: {next_index}")
                self.awaiting_additional_occupant_index = next_index
                response = f"What is the name of additional occupant {next_index + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            print(f"[DEBUG] Additional occupant collection complete. Final list: {self.slots['additional_occupants']}")
            self.awaiting_additional_occupant_index = None
            self.pending_confirmation_value = self.slots["additional_occupants"]
            self.pending_confirmation_field = "additional_occupants"
            self.awaiting_confirmation = True
            if self.editing_mode:
                self.after_additional_occupant_recollection = True
                print("[DEBUG] Marking after_additional_occupant_recollection = True (edit mode)")
            response = f"Saving additional occupants list: {', '.join(self.slots['additional_occupants'])}. Is this correct? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        # Handle custom clause collection -----------------------------------------------------------------------------------------------------------------------------------------------------

        if getattr(self, "awaiting_custom_clause", False):
            print("[DEBUG] Entered custom clause continuation prompt")
            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Custom clause continuation - interpreted as: {interpretation}")

            if interpretation == "yes":
                self.awaiting_custom_clause = False
                self.awaiting_custom_clause_entry = True
                response = "What is the special clause you'd like to include?"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User has finished entering custom clauses.")
                self.awaiting_custom_clause = False
                self.awaiting_final_confirmation = True
                response = self._render_summary_and_ask_if_happy() # only here because this will always be at the end of a schema 
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "question":
                print("[DEBUG] User asked a question during custom clause continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="custom_clauses",
                    current_question="We're adding custom clauses to the contract. Would you like to add another special clause?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                response = f"{response}\n\nWould you like to add another custom clause? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic during custom clause continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="custom_clauses",
                    current_question="We’re currently adding special terms to the agreement. Would you like to include another custom clause?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                response = f"{response}\n\nWould you like to add another custom clause? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, I didn’t catch that. Would you like to add another custom clause? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

        elif getattr(self, "awaiting_custom_clause_entry", False):
            print("[DEBUG] Capturing new custom clause")
            clause_text = user_input.strip()

            self.slots.setdefault("custom_clauses", []).append({
                "text": clause_text,
                "tag": classify_clause_tag(clause_text)
            })

            print(f"[DEBUG] Added tagged custom clause: {clause_text}")

            self.awaiting_custom_clause_entry = False
            self.awaiting_custom_clause = True
            response = "Would you like to add another custom clause? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response
        

        # Handle collection of new shared area ----------------------------------------------------------------------------------------------------------------

        if self.awaiting_shared_area_entry:
            print("[DEBUG] Capturing new shared area")
            self.slots["shared_areas_description"].append(user_input.strip())
            self.awaiting_shared_area_entry = False
            self.awaiting_shared_area = True
            response = "Would you like to add another shared area? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        if self.awaiting_shared_area:
            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] classify_confirmation_context: {interpretation}")

            if interpretation == "yes":
                self.awaiting_shared_area = False
                self.awaiting_shared_area_entry = True
                response = f"What is shared area {len(self.slots['shared_areas_description']) + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User has finished entering shared_areas_description.")
                self.awaiting_shared_area = False
                self.awaiting_shared_area_entry = False
                self.current_field_index += 1
                next_field = self._current_field()
                response = next_field["question"]
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked a question during shared area continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="shared_areas_description",
                    current_question=None,
                    context="We're listing shared areas of the property (e.g., lobby, bike room). Would you like to continue?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                response = f"{response}\n\nWould you like to add another shared area? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic during shared area continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="shared_areas_description",
                    current_question=None,
                    context="We’re currently describing shared areas of the building (like hallways or gardens). Would you like to continue?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                response = f"{response}\n\nWould you like to add another shared area? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="terminate_session"
                )
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {"current_question": self._current_question()}
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, I didn’t catch that. Would you like to add another shared area? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            

        # Handle collection of new property part ------------------------------------------------------------------------------------------------


        if self.awaiting_property_include_entry:
            print("[DEBUG] Capturing new property_includes entry")
            self.slots["property_includes"].append(user_input.strip())
            self.awaiting_property_include_entry = False
            self.awaiting_property_include = True
            response = "Would you like to add another included property feature or space? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        if self.awaiting_property_include:
            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] classify_confirmation_context for property_includes continuation: {interpretation}")

            if interpretation == "yes":
                self.awaiting_property_include = False
                self.awaiting_property_include_entry = True
                response = f"What is included space {len(self.slots['property_includes']) + 1}? (e.g. garden, garage, balcony)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User has finished entering property_includes.")
                self.awaiting_property_include = False
                self.awaiting_property_include_entry = False
                self.current_field_index += 1
                next_field = self._current_field()
                response = next_field["question"]
                self.recent_messages[-1]["bot"] = response
                return response


            elif interpretation == "question":
                print("[DEBUG] User asked a question during property_includes continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="property_includes",
                    current_question=None,
                    context="We are collecting a list of included spaces in the property (e.g. garage, garden). Would you like to add another one?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                response = f"{response}\n\nWould you like to add another included space? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic during property_includes continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="property_includes",
                    current_question=None,
                    context="We're currently listing spaces included with the property (e.g. terrace, shed). Would you like to continue?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                response = f"{response}\n\nWould you like to add another included space? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {"current_question": self._current_question()}
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, I didn’t quite catch that. Would you like to add another included property space? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
        # Handle collection of included utilities  ------------------------------------------------------------------------------------------------------------------------

        # Handle utility included entry
        if self.awaiting_utility_included_entry:
            print("[DEBUG] Capturing included utility")
            self.slots["which_utilities_included"].append(user_input.strip())
            self.awaiting_utility_included_entry = False
            self.awaiting_utility_included = True
            response = "Would you like to add another included utility? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        # Handle utility included continuation
        if self.awaiting_utility_included:
            interpretation = classify_confirmation_context(user_input)
            if interpretation == "yes":
                self.awaiting_utility_included = False
                self.awaiting_utility_included_entry = True
                response = f"What is included utility {len(self.slots['which_utilities_included']) + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "no":
                self.awaiting_utility_included = False
                self.slots.setdefault("which_utilities_not_included", [])
                self.awaiting_which_utilities_not_included_entry = True
                response = "Understood. Let’s now list the utilities that are *not* included in the rent.\nWhat is the first excluded utility?"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "question":
                print("[DEBUG] User asked a question during included utility continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="which_utilities_included",
                    current_question=None,
                    context="We’re listing utilities covered by the rent. Would you like to add another one?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                response = f"{response}\n\nWould you like to add another included utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic during included utility continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="which_utilities_included",
                    current_question=None,
                    context="We’re currently describing which utilities are included. Would you like to add another one?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                response = f"{response}\n\nWould you like to add another included utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {"current_question": self._current_question()}
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            else:
                response = "Sorry, would you like to add another included utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            

        # Handle collection of non-included utilities  ------------------------------------------------------------------------------------------------------------------------

        # Handle utility excluded entry
        if self.awaiting_which_utilities_not_included_entry:
            print("[DEBUG] Capturing excluded utility")
            self.slots["which_utilities_not_included"].append(user_input.strip())
            self.awaiting_which_utilities_not_included_entry = False
            self.awaiting_which_utilities_not_included = True
            response = "Would you like to add another excluded utility? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        # Handle utility excluded continuation
        if self.awaiting_which_utilities_not_included:
            interpretation = classify_confirmation_context(user_input)
            if interpretation == "yes":
                self.awaiting_which_utilities_not_included = False
                self.awaiting_which_utilities_not_included_entry = True
                response = f"What is excluded utility {len(self.slots['which_utilities_not_included']) + 1}?"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "no":
                print("[DEBUG] User has finished entering which_utilities_not_included.")
                self.awaiting_which_utilities_not_included = False
                self.awaiting_which_utilities_not_included_entry = False
                self.current_field_index += 1
                next_field = self._current_field()
                response = next_field["question"]
                self.recent_messages[-1]["bot"] = response
                return response

            
            elif interpretation == "question":
                print("[DEBUG] User asked a question during excluded utility continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="which_utilities_not_included",
                    current_question=None,
                    context="We’re listing utilities *not* included in the rent. Would you like to add another one?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                response = f"{response}\n\nWould you like to add another excluded utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic during excluded utility continuation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="which_utilities_not_included",
                    current_question=None,
                    context="We're currently listing utilities not covered by the rent. Would you like to add another one?",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                response = f"{response}\n\nWould you like to add another excluded utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {"current_question": self._current_question()}
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, would you like to add another excluded utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            
        # Handle confirmation of tenant reset -------------------------------------------------------------------------------------------------   
        
        if self.awaiting_tenant_reset_confirmation:
            print("[DEBUG] Entered tenant reset confirmation block.")
            print(f"[DEBUG] User input for tenant reset: {user_input}")

            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Interpretation of input: {interpretation}")
            print(f"[DEBUG] Editing mode: {self.editing_mode}")

            if interpretation == "yes":
                print("[DEBUG] User confirmed tenant reset. Clearing tenant-related slots.")
                self.slots.pop("tenant_info", None)
                self.slots.pop("tenant_count", None)
                self.awaiting_tenant_reset_confirmation = False
                if self.editing_mode:
                    self.after_tenant_recollection = True
                    print("[DEBUG] Set after_tenant_recollection = True due to edit mode.")
                self.current_field_index = 0
                response = "How many tenants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User declined tenant reset. Returning to summary.")
                self.awaiting_tenant_reset_confirmation = False
                response = self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked a question instead of confirming reset.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context="The user is being asked whether they want to change the number of tenants. If they proceed, existing tenant data will be deleted.",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nAre you sure you want to change the number of tenants? This will remove all current tenant names. (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User said something off topic instead of confirming tenant reset.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context="The user is being asked whether they want to change the number of tenants. If they proceed, existing tenant data will be deleted.",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nAre you sure you want to change the number of tenants? This will remove all current tenant names. (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="terminate_session"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                print("[DEBUG] Input was not clearly yes/no/question. Asking again.")
                response = "Sorry, should we continue or not? Please say yes or no."
                self.recent_messages[-1]["bot"] = response
                return response
        

        # Handle confirmation of additional occupant reset -------------------------------------------------------------------------------------------------

        if self.awaiting_additional_occupant_reset_confirmation:
            print("[DEBUG] Entered additional occupant reset confirmation block.")
            print(f"[DEBUG] User input for additional occupant reset: {user_input}")

            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Interpretation of input: {interpretation}")
            print(f"[DEBUG] Editing mode: {self.editing_mode}")

            if interpretation == "yes":
                print("[DEBUG] User confirmed additional occupant reset. Clearing additional occupant-related slots.")
                self.slots.pop("additional_occupants", None)
                self.slots.pop("additional_occupants_count", None)
                self.awaiting_additional_occupant_reset_confirmation = False
                if self.editing_mode:
                    self.after_additional_occupant_recollection = True
                    print("[DEBUG] Set after_additional_occupant_recollection = True due to edit mode.")
                self.current_field_index = 0
                response = "How many additional occupants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User declined additional occupant reset. Returning to summary.")
                self.awaiting_additional_occupant_reset_confirmation = False
                response = self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked a question instead of confirming additional occupant reset.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context="The user is being asked whether they want to change the number of additional occupants. If they proceed, existing names will be removed.",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nAre you sure you want to change the number of additional occupants? This will remove all current additional occupant names. (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User said something off-topic instead of confirming additional occupant reset.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context="The user is being asked whether they want to change the number of additional occupants. If they proceed, existing names will be removed.",
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nAre you sure you want to change the number of additional occupants? This will remove all current additional occupant names. (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="terminate_session"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                print("[DEBUG] Input was not clearly yes/no/question. Asking again.")
                response = "Sorry, should we continue or not? Please say yes or no."
                self.recent_messages[-1]["bot"] = response
                return response

                        
        #  Handle redirect after full tenant reset flow -------------------------------------------------------------------------------------------------------

        if self.after_tenant_recollection and self.editing_mode and self.pending_confirmation_field == "tenant_info":
            print("[DEBUG] Completed tenant reset and recollection. Skipping to summary.")
            self.editing_mode = False
            self.awaiting_confirmation = False
            self.pending_confirmation_value = None
            self.pending_confirmation_field = None
            self.after_tenant_recollection = False
            self.awaiting_tenant_name_index = None
            self.current_tenant_step = 0  # Reset field step tracker
            return self._render_summary_and_ask_if_happy()
        
        # Handle redirect after full additional occupant reset flow -------------------------------------------------------------------------------------------------------

        if self.after_additional_occupant_recollection and self.editing_mode and self.pending_confirmation_field == "additional_occupants":
            print("[DEBUG] Completed additional occupant reset and recollection. Skipping to summary.")
            self.editing_mode = False
            self.awaiting_confirmation = False
            self.pending_confirmation_value = None
            self.pending_confirmation_field = None
            self.after_additional_occupant_recollection = False
            return self._render_summary_and_ask_if_happy()

        # Handle edits of stored items -------------------------------------------------------------------------------------------------------------
        
        if self.awaiting_edit_field_selection:
            print("[DEBUG] Entered awaiting_edit_field_selection block")

            schema_fields = self.get_editable_fields()
            tenant_count = len(self.slots.get("tenant_info", []))
            tenant_fields = [f"tenant_{i+1}_{sub}" for i in range(tenant_count) for sub in ["name", "email", "phone"]]
            custom_clauses = self.slots.get("custom_clauses", [])
            custom_fields = [f"custom_clause_{i+1}" for i in range(len(custom_clauses))]
            additional_occupants = len(self.slots.get("additional_occupants", []))
            additional_occupant_fields = [f"additional_occupant_{i+1}" for i in range(additional_occupants)]

            all_fields = schema_fields + ["tenant_count"] + tenant_fields + custom_fields + additional_occupant_fields

            print(f"[DEBUG] Available editable fields: {all_fields}")

            user_input_normalized = user_input.lower().strip().replace(" ", "_")
            print(f"[DEBUG] Normalized user input: {user_input_normalized}")

            closest = difflib.get_close_matches(user_input_normalized, all_fields, n=1, cutoff=0.5)
            print(f"[DEBUG] Closest match from difflib: {closest}")

            if not closest:
                options = ', '.join(all_fields)
                response = f"I couldn’t find a matching field for '{user_input}'. Try one of these: {options}"
                self.recent_messages[-1]["bot"] = response
                return response

            matched_field = closest[0]
            print(f"[DEBUG] Matched field to edit: {matched_field}")

            if matched_field == "monthly_rent":
                response = (
                    "The monthly rent is automatically calculated based on the weekly rent.\n"
                    "If you'd like to change it, please edit the *weekly rent* value instead."
                )
                self.recent_messages[-1]["bot"] = response
                return response

            if matched_field == "tenant_count":
                print("[DEBUG] User wants to change tenant_count")
                self.awaiting_edit_field_selection = False
                self.awaiting_tenant_reset_confirmation = True
                self.editing_mode = True
                response = (
                    "Are you sure you want to change the number of tenants? "
                    "This will remove all current tenant names. (yes/no)"
                )
                self.recent_messages[-1]["bot"] = response
                return response

            if matched_field.startswith("tenant_") and "_" in matched_field:
                try:
                    parts = matched_field.split("_")
                    tenant_index = int(parts[1]) - 1
                    subfield = parts[2] if len(parts) == 3 else "name"

                    field_order = ["name", "email", "phone"]
                    if 0 <= tenant_index < tenant_count and subfield in field_order:
                        print(f"[DEBUG] Editing tenant {tenant_index + 1}'s {subfield}")
                        self.slots["tenant_info"][tenant_index][subfield] = None  # Clear the current value
                        self.awaiting_edit_field_selection = False
                        self.awaiting_tenant_name_index = tenant_index
                        self.current_tenant_step = field_order.index(subfield)  # Use index to track which subfield we're editing
                        self.editing_mode = True
                        response = f"What is the {subfield} of tenant {tenant_index + 1}?"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse tenant subfield: {e}")

            if matched_field.startswith("additional_occupant_"):
                try:
                    occupant_index = int(matched_field.split("_")[-1]) - 1
                    additional_occupant_count = len(self.slots.get("additional_occupants", []))
                    if 0 <= occupant_index < additional_occupant_count:
                        print(f"[DEBUG] Editing individual additional occupant {occupant_index + 1}")
                        self.slots["additional_occupants"][occupant_index] = None  # Clear value before re-entry
                        self.awaiting_edit_field_selection = False
                        self.awaiting_additional_occupant_index = occupant_index
                        self.editing_mode = True
                        response = f"What is the name of additional occupant {occupant_index + 1}?"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse additional occupant index: {e}")


            if matched_field.startswith("custom_clause_"):
                try:
                    clause_index = int(matched_field.split("_")[-1]) - 1
                    if 0 <= clause_index < len(custom_clauses):
                        print(f"[DEBUG] Editing custom clause {clause_index + 1}")
                        self.awaiting_edit_field_selection = False
                        self.awaiting_custom_clause_index = clause_index
                        self.editing_mode = True
                        response = f"What should custom clause {clause_index + 1} now say? (Type 'delete' to remove it)"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse clause index: {e}")

            if matched_field == "custom_clauses":
                print("[DEBUG] User wants to add more custom clauses")
                self.awaiting_edit_field_selection = False
                self.awaiting_custom_clause = True
                response = "Would you like to add another custom clause? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            
            # Edit individual property_includes (e.g., "property_include_1")
            if matched_field.startswith("property_include_"):
                try:
                    index = int(matched_field.split("_")[-1]) - 1
                    if 0 <= index < len(self.slots.get("property_includes", [])):
                        print(f"[DEBUG] Editing property_includes[{index}]")
                        self.awaiting_edit_field_selection = False
                        self.awaiting_property_include_index = index
                        self.editing_mode = True
                        response = f"What should included space {index + 1} now say? (Type 'delete' to remove it)"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse property_include index: {e}")
            
            if matched_field == "property_includes":
                self.awaiting_edit_field_selection = False
                self.awaiting_property_include = True
                response = "Would you like to add another space included in the property? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            
            # Edit individual shared_areas_description (e.g., "shared_area_2")
            if matched_field.startswith("shared_area_"):
                try:
                    index = int(matched_field.split("_")[-1]) - 1
                    if 0 <= index < len(self.slots.get("shared_areas_description", [])):
                        print(f"[DEBUG] Editing shared_areas_description[{index}]")
                        self.awaiting_edit_field_selection = False
                        self.awaiting_shared_area_index = index
                        self.editing_mode = True
                        response = f"What should shared area {index + 1} now say? (Type 'delete' to remove it)"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse shared_area index: {e}")

            if matched_field == "shared_areas_description":
                self.awaiting_edit_field_selection = False
                self.awaiting_shared_area = True
                response = "Would you like to add another shared area? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            

            # Edit individual which_utilities_included (e.g., "utility_included_1")
            if matched_field.startswith("utility_included_"):
                try:
                    index = int(matched_field.split("_")[-1]) - 1
                    if 0 <= index < len(self.slots.get("which_utilities_included", [])):
                        print(f"[DEBUG] Editing which_utilities_included[{index}]")
                        self.awaiting_edit_field_selection = False
                        self.awaiting_utility_included_index = index
                        self.editing_mode = True
                        response = f"What should included utility {index + 1} now say? (Type 'delete' to remove it)"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse utility_included index: {e}")

            if matched_field == "which_utilities_included":
                self.awaiting_edit_field_selection = False
                self.awaiting_utility_included = True
                response = "Would you like to add another included utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            


            # Edit individual which_utilities_not_included (e.g., "utility_excluded_1")
            if matched_field.startswith("utility_excluded_"):
                try:
                    index = int(matched_field.split("_")[-1]) - 1
                    if 0 <= index < len(self.slots.get("which_utilities_not_included", [])):
                        print(f"[DEBUG] Editing which_utilities_not_included[{index}]")
                        self.awaiting_edit_field_selection = False
                        self.awaiting_which_utilities_not_included_index = index
                        self.editing_mode = True
                        response = f"What should excluded utility {index + 1} now say? (Type 'delete' to remove it)"
                        self.recent_messages[-1]["bot"] = response
                        return response
                except Exception as e:
                    print(f"[DEBUG] Failed to parse utility_excluded index: {e}")

            if matched_field == "which_utilities_not_included":
                self.awaiting_edit_field_selection = False
                self.awaiting_which_utilities_not_included = True
                response = "Would you like to add another excluded utility? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response


            # Check if user tried to edit a dynamic field that was never collected
            field_def = next(f for f in SCHEMAS[self.active_schema]["fields"] if f["name"] == matched_field)
            if "depends_on" in field_def and not self.evaluate_condition(field_def["depends_on"], self.slots):
                print(f"[DEBUG] Field '{matched_field}' was skipped earlier due to unmet condition — cannot edit.")
                response = f"That field wasn't part of this agreement due to how you answered earlier. If you'd like to revisit it, you may need to change related answers first."
                self.recent_messages[-1]["bot"] = response
                return response

            if matched_field in schema_fields:
                print(f"[DEBUG] Editing regular schema field: {matched_field}")
                self.current_field_index = next(
                    i for i, f in enumerate(SCHEMAS[self.active_schema]["fields"])
                    if f["name"] == matched_field
                )
                self.pending_confirmation_field = matched_field
                self.editing_mode = True
                self.awaiting_edit_field_selection = False
                response = self._current_question()
                self.recent_messages[-1]["bot"] = response
                return response
            
            if matched_field == "weekly_rent":
                print("[DEBUG] User is editing weekly_rent — clearing monthly_rent for recalculation.")
                self.slots["monthly_rent"] = None

            # If we got here, something's wrong
            print("[DEBUG] Matched field fell through all known categories")
            response = "Sorry, I understood your request but couldn't process it. Try again."
            self.recent_messages[-1]["bot"] = response
            return response


        # Handle confirmation of individual field ----------------------------------------------------------------------------------------------------------------------------------
        
        if self.awaiting_confirmation:
            print("[DEBUG] Entered confirmation block.")
            print(f"[DEBUG] Current confirmation target field: {self.pending_confirmation_field}")
            print(f"[DEBUG] User input for confirmation: {user_input}")

            # Safeguard against misfired confirmation state
            if not self.pending_confirmation_field:
                print("[WARN] No pending field set during confirmation. Exiting confirmation block.")
                self.awaiting_confirmation = False
                response = "I'm not sure what we're confirming. Let's go back to the question."
                self.recent_messages[-1]["bot"] = response
                return response

            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Interpreted user input as: {interpretation}")

            if interpretation == "yes":
                print(f"[DEBUG] Saving field '{self.pending_confirmation_field}' with value: {self.pending_confirmation_value}")
                self.slots[self.pending_confirmation_field] = self.pending_confirmation_value

                if self.pending_confirmation_field == "weekly_rent":
                    try:
                        new_weekly = float(self.pending_confirmation_value)
                        self.slots["monthly_rent"] = str(round(new_weekly * 52 / 12, 2))
                        print(f"[DEBUG] Recalculated monthly_rent after confirming weekly_rent: {self.slots['monthly_rent']}")
                    except ValueError:
                        print("[DEBUG] Failed to parse weekly_rent for monthly calculation. Skipping.")

                    if self.editing_mode:
                        print("[DEBUG] Weekly rent was edited — skipping field advancement and returning to summary.")
                        self.awaiting_confirmation = False
                        self.pending_confirmation_field = None
                        self.pending_confirmation_value = None
                        self.editing_mode = False
                        response = self._render_summary_and_ask_if_happy()
                        self.recent_messages[-1]["bot"] = response
                        return response

                    # CLEANUP + PROGRESSION
                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None

                    if self.current_field_index >= len(SCHEMAS[self.active_schema]["fields"]):
                        print("[DEBUG] All fields collected — rendering summary.")
                        self.all_information_gathered = True
                        response = self._render_summary_and_ask_if_happy()
                    else:
                        next_field = self._current_field()
                        response = next_field["question"]

                    self.recent_messages[-1]["bot"] = response
                    return response


                if self.pending_confirmation_field == "wants_custom_clauses" and self.pending_confirmation_value == "yes":
                    print("[DEBUG] User wants to add custom clauses. Starting clause collection.")
                    self.slots.setdefault("custom_clauses", [])
                    self.awaiting_custom_clause_entry = True

                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None

                    response = "What is the first special clause you'd like to include?"
                    self.recent_messages[-1]["bot"] = response
                    return response
                

                if self.pending_confirmation_field == "property_includes_confirmation" and self.pending_confirmation_value == "yes":
                    self.slots.setdefault("property_includes", [])
                    self.awaiting_property_include_entry = True
                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None
                    response = "Let’s start with the spaces included in the property.\nWhat is the first included feature or space (e.g. garden, garage)?"
                    self.recent_messages[-1]["bot"] = response
                    return response
                
                if self.pending_confirmation_field == "shared_areas" and self.pending_confirmation_value == "yes":
                    self.slots.setdefault("shared_areas_description", [])
                    self.awaiting_shared_area_entry = True
                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None
                    response = "Alright. What is the first shared area you'd like to list (e.g. lobby, lift, rooftop)?"
                    self.recent_messages[-1]["bot"] = response
                    return response
                

                if self.pending_confirmation_field == "utilities_included" and self.pending_confirmation_value == "yes":
                    print("[DEBUG] User confirmed utilities are included. Starting iterative utility collection.")
                    self.slots.setdefault("which_utilities_included", [])
                    self.awaiting_utility_included_entry = True
                    self.awaiting_confirmation = False
                    self.pending_confirmation_field = None
                    self.pending_confirmation_value = None
                    response = "Let’s begin collecting the utilities that are included in the rent.\nWhat is the first included utility?"
                    self.recent_messages[-1]["bot"] = response
                    return response

                try:
                    confirmed_index = SCHEMAS[self.active_schema]["fields"].index(
                        next(f for f in SCHEMAS[self.active_schema]["fields"] if f["name"] == self.pending_confirmation_field)
                    )
                except StopIteration:
                    print(f"[DEBUG] Field '{self.pending_confirmation_field}' not found in schema — treating as dynamic field.")
                    confirmed_index = None

                # Dependent recollection handling
                if self.editing_mode and confirmed_index is not None and confirmed_index != self.current_field_index:
                    print("[DEBUG] Reconfirmed dependent field — returning to summary.")
                    self.editing_mode = False
                    self.awaiting_final_confirmation = True
                    response = self._render_summary_and_ask_if_happy()
                    self.recent_messages[-1]["bot"] = response
                    return response

                self._prune_invalid_dependent_fields()

                if self.recollecting_dependent:
                    print("[DEBUG] Continuing dependent recollection.")
                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None

                    # Advance to next valid dependent field
                    self.current_field_index += 1
                    while self.current_field_index < len(SCHEMAS[self.active_schema]["fields"]):
                        f = SCHEMAS[self.active_schema]["fields"][self.current_field_index]
                        if "name" in f and "question" in f:
                            if "depends_on" not in f or self.evaluate_condition(f["depends_on"], self.slots):
                                if f["name"] not in self.slots:
                                    break
                        self.current_field_index += 1

                    if self.current_field_index >= len(SCHEMAS[self.active_schema]["fields"]):
                        print("[DEBUG] Finished all recollected dependents — returning to summary.")
                        self.recollecting_dependent = False
                        self.editing_mode = False
                        self.all_information_gathered = True
                        response = self._render_summary_and_ask_if_happy()
                    else:
                        response = self._current_question()

                    self.recent_messages[-1]["bot"] = response
                    return response

                if self.editing_mode:
                    print("[DEBUG] Confirmation came during editing mode — checking if more fields need to be recollected.")
                    self._reset_and_recollect_dependents(self.pending_confirmation_field)

                    self.awaiting_confirmation = False
                    self.pending_confirmation_value = None
                    self.pending_confirmation_field = None
                    self.editing_mode = False

                    # If _reset_and_recollect_dependents set recollection, it will flag it
                    if self.recollecting_dependent:
                        print(f"[DEBUG] Re-entering flow at dependent field index {self.current_field_index}")
                        response = self._current_question()
                        self.recent_messages[-1]["bot"] = response
                        return response
                    else:
                        print("[DEBUG] No child dependents recollected — returning to summary.")
                        self.editing_mode = False
                        response = self._render_summary_and_ask_if_happy()
                        self.recent_messages[-1]["bot"] = response
                        return response

                # Normal advancement
                self.awaiting_confirmation = False
                self.pending_confirmation_value = None
                self.pending_confirmation_field = None
                self.current_field_index += 1

                if self.current_field_index >= len(SCHEMAS[self.active_schema]["fields"]):
                    print("[DEBUG] All fields collected — rendering summary.")
                    self.all_information_gathered = True
                    response = self._render_summary_and_ask_if_happy()
                    self.recent_messages[-1]["bot"] = response
                    return response

                next_field = self._current_field()
                response = next_field["question"]
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User rejected the field value. Re-asking the question.")
                self.awaiting_confirmation = False
                response = f"Let's try again. {self._current_question()}"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked for clarification.")
                confirmation_prompt = f"Please confirm that the information you provided for '{self.pending_confirmation_field}' is correct."
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=self.pending_confirmation_field,
                    current_question=None,
                    context=confirmation_prompt,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nPlease confirm — is your answer correct? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User said something off topic instead of confirming.")
                confirmation_prompt = f"Please confirm that the information you provided for '{self.pending_confirmation_field}' is correct."
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=self.pending_confirmation_field,
                    current_question=None,
                    context=confirmation_prompt,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nLet’s get back to it: Please confirm — is your answer correct? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response
            
            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="terminate_session"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                print("[DEBUG] User input not recognized as yes/no/question.")
                response = "Sorry, could you clarify if that was a yes or no?"
                self.recent_messages[-1]["bot"] = response
                return response


        # Handle post-summary: Are you happy with this information? ----------------------------------------------------------------------------------------------------------------------------
        
        if self.awaiting_final_confirmation:
            print("[DEBUG] Entered final confirmation block.")
            print(f"[DEBUG] User input for final confirmation: {user_input}")

            classification = classify_confirmation_context(user_input)
            print(f"[DEBUG] Interpreted final confirmation input as: {classification}")

            if classification == "yes":
                print("[DEBUG] User is happy with collected information. Proceeding to generation prompt.")
                self.awaiting_final_confirmation = False
                self.awaiting_generate_confirmation = True
                response = "Would you like me to generate the document now? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "no":
                print("[DEBUG] User wants to make edits. Transitioning to field edit selection.")
                self.awaiting_final_confirmation = False
                self.awaiting_edit_field_selection = True
                response = "Which field would you like to change?"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "question":
                print("[DEBUG] User asked a question about the collected info.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nAre you happy with this information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "off_topic":
                print("[DEBUG] User went off-topic instead of confirming info.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nLet’s get back to it. Are you happy with this information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                print("[DEBUG] Input unrecognized — prompting user again.")
                response = "Let’s get back to it. Are you happy with this information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response


        # Handle "Do you want me to generate it now?" decision ----------------------------------------------------------------------------------------------------------------------------------------------------
       
        if self.awaiting_generate_confirmation:
            print("[DEBUG] Entered document generation confirmation block.")
            print(f"[DEBUG] User input for generation: {user_input}")

            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] Interpreted user input as: {interpretation}")

            if interpretation == "yes":
                print("[DEBUG] User confirmed generation. Finalizing document...")
                self.awaiting_generate_confirmation = False

                final_fields = self.finalize_document()["fields"]
                docx_path = generate_contract_from_template(final_fields)

                self.generated_contract = docx_path

                web_path = docx_path.replace("\\", "/")

                self.recent_messages[-1]["bot"] = (
                    "The document has been generated successfully.<br><br>"
                    f'<a href="/download?file={web_path}" download>Download Rental Agreement</a>'
                )
                return self.recent_messages[-1]["bot"]

            elif interpretation == "no":
                print("[DEBUG] User declined generation. Offering to review collected data again.")
                self.awaiting_generate_confirmation = False
                response = "Would you like to see the list of what I’ve collected again? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked a question at generation step.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nWould you like me to generate the document now? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "off_topic":
                print("[DEBUG] User said something off topic at generation step.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nLet’s get back to it — should I generate the document now? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                print("[DEBUG] Could not interpret input clearly — re-asking generation question.")
                response = "Sorry, I couldn’t tell if you’re ready to generate the document. Can you confirm?"
                self.recent_messages[-1]["bot"] = response
                return response

            
        # Handle tenant count collection --------------------------------------------------------------------------------------------------

        if self._current_field()["name"] == "tenant_count" and not self.awaiting_confirmation:
            print("[DEBUG] Tenant count field detected and not awaiting confirmation.")
            print(f"[DEBUG] Raw user input for tenant_count: {user_input}")

            classification = classify_field_input(user_input, "tenant_count", "How many tenants will there be?")
            print(f"[DEBUG] classify_field_input returned: {classification}")

            if classification == "answer":
                extracted_value = extract_field_value(user_input, "tenant_count", "How many tenants will there be?")
                try:
                    count = int("".join(filter(str.isdigit, extracted_value)))
                    print(f"[DEBUG] Parsed tenant count: {count}")

                    if count <= 0:
                        response = "There must be at least one tenant. How many tenants will there be?"
                        self.recent_messages[-1]["bot"] = response
                        return response

                    self.slots["tenant_count"] = count
                    self.slots["tenant_info"] = [{"name": None, "email": None, "phone": None} for _ in range(count)]
                    self.awaiting_tenant_name_index = 0
                    self.tenant_fields_order = ["name", "email", "phone"]
                    response = f"What is the name of tenant 1?"
                    self.recent_messages[-1]["bot"] = response
                    return response

                except ValueError:
                    print("[DEBUG] Could not parse a number even after extraction.")
                    response = "Please enter a valid number of tenants."
                    self.recent_messages[-1]["bot"] = response
                    return response

            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification in {"question", "off_topic"}:
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="tenant_count",
                    current_question="How many tenants will there be?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nHow many tenants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, I didn’t catch that. How many tenants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response
            

        # Handle addititonl occupant count collection --------------------------------------------------------------------------------------------------

        if self._current_field()["name"] == "additional_occupants_count" and not self.awaiting_confirmation:
            print("[DEBUG] Tenant count field detected and not awaiting confirmation.")
            print(f"[DEBUG] Raw user input for additional_occupants_count: {user_input}")

            classification = classify_field_input(user_input, "additional_occupants_count", "How many additional occupants will there be?")
            print(f"[DEBUG] classify_field_input returned: {classification}")

            if classification == "answer":
                extracted_value = extract_field_value(user_input, "additional_occupants_count", "How many additional occupants will there be?")
                try:
                    count = int("".join(filter(str.isdigit, extracted_value)))
                    print(f"[DEBUG] Parsed tenant count: {count}")

                    if count <= 0:
                        print("[DEBUG] User specified 0 additional occupants.")
                        self.slots["additional_occupants_count"] = 0
                        self.slots["additional_occupants"] = []
                        self.awaiting_additional_occupant_index = None
                        self.current_field_index += 1
                        response = self._current_question()
                        self.recent_messages[-1]["bot"] = response
                        return response

                    self.slots["additional_occupants_count"] = count
                    self.slots["additional_occupants"] = [None] * count
                    self.awaiting_additional_occupant_index = 0
                    response = f"What is the name of additional occupant 1?"
                    self.recent_messages[-1]["bot"] = response
                    return response

                except ValueError:
                    print("[DEBUG] Could not parse a number even after extraction.")
                    response = "Please enter a valid number of additional occupants."
                    self.recent_messages[-1]["bot"] = response
                    return response

            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification in {"question", "off_topic"}:
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="additional_occupants_count",
                    current_question="How many additional occupants will there be?",
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                response = f"{response}\n\nHow many additional occupants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response

            else:
                response = "Sorry, I didn’t catch that. How many additional occupants will there be?"
                self.recent_messages[-1]["bot"] = response
                return response

            

        # Handle individual custom clause editing ---------------------------------------------------------------------------------------------------------------------------------------------------------------

        if hasattr(self, "awaiting_custom_clause_index") and self.awaiting_custom_clause_index is not None:
            index = self.awaiting_custom_clause_index
            print(f"[DEBUG] Editing custom clause at index {index} with input: {user_input}")

            if user_input.strip().lower() in {"delete", "none"}:
                clause = self.slots["custom_clauses"].pop(index)
                print(f"[DEBUG] Deleted clause: {clause}")
                self.awaiting_custom_clause_index = None
                self.awaiting_final_confirmation = True
                self.editing_mode = False
                response = f"Removed custom clause {index + 1}. Here's your updated summary:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            # Reclassify the edited clause with a new tag
            updated_clause = {
                "text": user_input.strip(),
                "tag": classify_clause_tag(user_input.strip())
            }
            self.slots["custom_clauses"][index] = updated_clause
            print(f"[DEBUG] Updated clause {index + 1}: {updated_clause}")

            self.awaiting_custom_clause_index = None
            self.awaiting_final_confirmation = True
            self.editing_mode = False
            response = self._render_summary_and_ask_if_happy()
            self.recent_messages[-1]["bot"] = response
            return response
        

        # Handle individual property_includes editing -------------------------------------------------------------------------------------------------------------------------------------------

        if hasattr(self, "awaiting_property_include_index") and self.awaiting_property_include_index is not None:
            index = self.awaiting_property_include_index
            print(f"[DEBUG] Editing property include at index {index} with input: {user_input}")

            if user_input.strip().lower() in {"delete", "none"}:
                removed = self.slots["property_includes"].pop(index)
                print(f"[DEBUG] Deleted property include: {removed}")
                self.awaiting_property_include_index = None
                self.awaiting_final_confirmation = True
                self.editing_mode = False
                response = f"Removed included space {index + 1}. Here's your updated summary:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            # Update the specific item
            self.slots["property_includes"][index] = user_input.strip()
            print(f"[DEBUG] Updated property include {index + 1} to: {user_input.strip()}")

            self.awaiting_property_include_index = None
            self.awaiting_final_confirmation = True
            self.editing_mode = False
            response = self._render_summary_and_ask_if_happy()
            self.recent_messages[-1]["bot"] = response
            return response
        

        # Handle individual shared_areas_description editing -----------------------------------------------------------------------------------------------------------------------------------

        if hasattr(self, "awaiting_shared_area_index") and self.awaiting_shared_area_index is not None:
            index = self.awaiting_shared_area_index
            print(f"[DEBUG] Editing shared area at index {index} with input: {user_input}")

            if user_input.strip().lower() in {"delete", "none"}:
                removed = self.slots["shared_areas_description"].pop(index)
                print(f"[DEBUG] Deleted shared area: {removed}")
                self.awaiting_shared_area_index = None
                self.awaiting_final_confirmation = True
                self.editing_mode = False
                response = f"Removed shared area {index + 1}. Here's your updated summary:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            # Update the specific item
            self.slots["shared_areas_description"][index] = user_input.strip()
            print(f"[DEBUG] Updated shared area {index + 1} to: {user_input.strip()}")

            self.awaiting_shared_area_index = None
            self.awaiting_final_confirmation = True
            self.editing_mode = False
            response = self._render_summary_and_ask_if_happy()
            self.recent_messages[-1]["bot"] = response
            return response
        

        # Handle individual which_utilities_included edit -----------------------------------------------------------------------------------------------------------------------------------------------------

        if hasattr(self, "awaiting_utility_included_index") and self.awaiting_utility_included_index is not None:
            index = self.awaiting_utility_included_index
            print(f"[DEBUG] Editing included utility at index {index} with input: {user_input}")

            if user_input.strip().lower() in {"delete", "none"}:
                deleted = self.slots["which_utilities_included"].pop(index)
                print(f"[DEBUG] Deleted included utility: {deleted}")
                self.awaiting_utility_included_index = None
                self.awaiting_final_confirmation = True
                self.editing_mode = False
                response = f"Removed included utility {index + 1}. Here's your updated summary:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            # Update utility
            self.slots["which_utilities_included"][index] = user_input.strip()
            print(f"[DEBUG] Updated included utility {index + 1}: {user_input.strip()}")
            self.awaiting_utility_included_index = None
            self.awaiting_final_confirmation = True
            self.editing_mode = False
            response = self._render_summary_and_ask_if_happy()
            self.recent_messages[-1]["bot"] = response
            return response
        

        # Handle individual which_utilities_not_included edit -----------------------------------------------------------------------------------------------------------------------------------------------------------

        if hasattr(self, "awaiting_which_utilities_not_included_index") and self.awaiting_which_utilities_not_included_index is not None:
            index = self.awaiting_which_utilities_not_included_index
            print(f"[DEBUG] Editing excluded utility at index {index} with input: {user_input}")

            if user_input.strip().lower() in {"delete", "none"}:
                deleted = self.slots["which_utilities_not_included"].pop(index)
                print(f"[DEBUG] Deleted excluded utility: {deleted}")
                self.awaiting_which_utilities_not_included_index = None
                self.awaiting_final_confirmation = True
                self.editing_mode = False
                response = f"Removed excluded utility {index + 1}. Here's your updated summary:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            self.slots["which_utilities_not_included"][index] = user_input.strip()
            print(f"[DEBUG] Updated excluded utility {index + 1}: {user_input.strip()}")
            self.awaiting_which_utilities_not_included_index = None
            self.awaiting_final_confirmation = True
            self.editing_mode = False
            response = self._render_summary_and_ask_if_happy()
            self.recent_messages[-1]["bot"] = response
            return response


        # Handle field input during editing mode -------------------------------------------------------------------------------------------------------------------------------------------------------
       
        if self.editing_mode and not self.awaiting_confirmation:
            print("[DEBUG] Entered editing_mode block — not awaiting confirmation.")
            expected_field = self._current_field()
            print(f"[DEBUG] Currently editing field: {expected_field['name']}")
            print(f"[DEBUG] Field question: {expected_field['question']}")
            print(f"[DEBUG] User input: {user_input}")

            classification = classify_field_input(user_input, expected_field["name"], expected_field["question"])
            print(f"[DEBUG] [EDITING] classify_field_input returned: {classification} for input: {user_input}")

            if classification == "answer":
                print(f"[DEBUG] [EDITING] Storing new value: {user_input} for field: {expected_field['name']}")

                raw_value = extract_field_value(user_input, expected_field["name"], expected_field["question"])
                extracted_value = self.strip_wrapping_quotes(raw_value)

                if expected_field["name"] == "weekly_rent":
                    try:
                        weekly_rent = float(extracted_value)
                        monthly_rent = round(weekly_rent * 52 / 12, 2)
                        self.pending_confirmation_value = str(weekly_rent)
                        self.pending_confirmation_field = expected_field["name"]
                        self.awaiting_confirmation = True

                        response = (
                            f"Saving £{weekly_rent:.2f} per week. "
                            f"That works out to approximately £{monthly_rent:.2f} per month.\n"
                            f"Is this correct? (yes/no)"
                        )
                        self.recent_messages[-1]["bot"] = response
                        return response
                    except ValueError:
                        print("[DEBUG] Could not parse weekly rent input.")
                        response = "That doesn't look like a valid number for weekly rent. Try again?"
                        self.recent_messages[-1]["bot"] = response
                        return response


                print(f"[DEBUG] Extracted value for {expected_field['name']}: {extracted_value}")
                self.pending_confirmation_value = extracted_value

                self.pending_confirmation_field = expected_field["name"]
                self.awaiting_confirmation = True
                response = f"Saving \"{extracted_value}\" for \"{expected_field['name']}\". Is this correct? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "question":
                print("[DEBUG] [EDITING] User asked a question related to the field.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=expected_field["name"],
                    current_question=expected_field["question"],
                    context=expected_field.get("context"),
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nLet's get back to it: {expected_field['question']}"

            elif classification == "off_topic":
                print("[DEBUG] [EDITING] User input was off-topic.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=expected_field["name"],
                    current_question=expected_field["question"],
                    context=expected_field.get("context"),
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nLet's get back to it: {expected_field['question']}"

            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=classification
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"

            else:
                print(f"[DEBUG] [EDITING] Could not interpret user input for field '{expected_field['name']}'.")
                response = f"I didn’t understand your answer for {expected_field['name']}. Could you rephrase it?"
                self.recent_messages[-1]["bot"] = response
                return response


        # Handle "Would you like to see the collected info again?" --------------------------------------------------------------------------------------------------------------------------------------
       
        if self.all_information_gathered and not self.awaiting_final_confirmation:
            print("[DEBUG] Entered all_information_gathered block.")
            print(f"[DEBUG] User input: {user_input}")

            interpretation = classify_confirmation_context(user_input)
            print(f"[DEBUG] classify_confirmation_context returned: {interpretation}")

            if interpretation == "yes":
                print("[DEBUG] User confirmed they want to review the collected summary.")
                response = self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "no":
                print("[DEBUG] User declined — triggering full restart.")
                self.reset()
                self.state = "doc_selection"
                response = "Okay, starting over. What kind of document would you like to generate?\n" + self._list_doc_options()
                self.recent_messages[-1]["bot"] = response
                return response

            elif interpretation == "question":
                print("[DEBUG] User asked a question while reviewing collected info.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nAre you happy with this information? (yes/no)"
            
            elif interpretation == "off_topic":
                print("[DEBUG] User went off-topic while reviewing collected info.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field=None,
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nLet’s stay on track — are you happy with this information? (yes/no)"
            
            elif interpretation == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                self.recent_messages[-1]["bot"] = response
                return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"

            else:
                print("[DEBUG] Could not interpret input, defaulting to re-showing summary.")
                response = "I wasn’t sure how to interpret that. Here’s what I’ve collected again:\n\n" + self._render_summary_and_ask_if_happy()
                self.recent_messages[-1]["bot"] = response
                return response


        # Normal flow — handle answer to a field ------------------------------------------------------------------------------------------------------------------------------------------------------------

        expected_field = self._current_field()
        classification = classify_field_input(user_input, expected_field["name"], expected_field["question"])
        print(f"[DEBUG] classify_field_input returned: {classification} for input: {user_input}")

        if classification == "question":
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                current_field=expected_field["name"],
                current_question=expected_field["question"],
                context=expected_field["context"],
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state=classification
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            print(f"[DEBUG] classify_field_input: classification={classification}")
            print(f"[DEBUG] Calling classify_field_input with: user_input={user_input}, expected_field={expected_field['name']}")
            self.recent_messages[-1]["bot"] = response
            return f"{response}\n\nLet's get back to it: {expected_field['question']}"

        elif classification == "off_topic":
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                current_field=expected_field["name"],
                current_question=expected_field["question"],
                context=expected_field["context"],
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state=classification
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            print(f"[DEBUG] classify_field_input:  classification={classification}")
            print(f"[DEBUG] Calling classify_field_input with: user_input={user_input}, expected_field={expected_field['name']}")
            self.recent_messages[-1]["bot"] = response
            return f"{response}\n\nLet's get back to it: {expected_field['question']}"

        elif classification == "terminate_session":
            print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                current_field="exit_confirmation",
                current_question=None,
                context=None,
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state=classification
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            self.awaiting_exit_confirmation = True
            self.saved_context_before_exit = {
                "current_question": self._current_question()
            }
            self.recent_messages[-1]["bot"] = response
            return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"

        elif classification == "answer":
            print(f"[DEBUG] User input classified as ANSWER for field: {expected_field['name']}")

            # Special yes/no classification for certain fields
            if expected_field["name"] in {"has_break_clause", "furnished", "wants_custom_clauses", "shared_areas", "utilities_included"}:
                yn_result = classify_confirmation_context(user_input) #expected_field["name"], expected_field["question"])
                print(f"[DEBUG] classify_confirmation_context for special fields: {yn_result}")

                if yn_result in {"yes", "no"}:
                    self.pending_confirmation_value = yn_result
                    self.pending_confirmation_field = expected_field["name"]
                    self.awaiting_confirmation = True
                    response = f"Saving \"{yn_result}\" for \"{expected_field['name']}\". Is this correct? (yes/no)"
                    self.recent_messages[-1]["bot"] = response
                    return response
                
                elif yn_result in {"off_topic", "question"}:
                    print("[DEBUG] User went off-topic or asked a question while answering yes/no field.")
                    response = llama_answer(
                        user_input=user_input,
                        active_schema=self.active_schema,
                        current_field=expected_field["name"],
                        current_question=expected_field["question"],
                        context=expected_field["context"],
                        recent_messages=self.recent_messages,
                        slots=self.slots,
                        user_state=yn_result
                    )
                    self.recent_messages[-1]["bot"] = f"{response}\n\nLet's get back to it: {expected_field['question']}"
                    return f"{response}\n\nLet's get back to it: {expected_field['question']}"

                else:
                    response = "Sorry, I didn’t quite catch that. Is the answer yes or no?"
                    self.recent_messages[-1]["bot"] = response
                    return response
                
            if expected_field["name"] in {"break_clause_notice"}:
                value = extract_field_value(user_input, expected_field["name"], expected_field["question"]) #expected_field["name"], expected_field["question"])
                print(f"[DEBUG] extract_field_value for break clause notice period: {value}")

                if value < 2:
                    warning_msg = (
                        "Under the Housing Act 1988, break clause notice must be at least **2 months**.\n\n"
                        "Please enter a number **greater than or equal to 2** for the notice period."
                    )
                    self.recent_messages[-1]["bot"] = f"{warning_msg}\n\n{expected_field['question']}"
                    return f"{warning_msg}\n\n{expected_field['question']}"

                # Valid value — proceed with confirmation
                self.pending_confirmation_value = str(value)
                self.pending_confirmation_field = expected_field["name"]
                self.awaiting_confirmation = True
                response = f'Saving "{value}" months for "{expected_field["name"]}". Is this correct? (yes/no)'
                self.recent_messages[-1]["bot"] = response
                return response

            # had to make a tool for fields that cannot be answered with a "no"
            if expected_field["name"] in {"property_includes_confirmation"}: 
                yn_result = classify_confirmation_context(user_input)
                print(f"[DEBUG] classify_confirmation_context for required-yes field '{expected_field['name']}': {yn_result}")

                if yn_result == "yes":
                    self.pending_confirmation_value = "yes"
                    self.pending_confirmation_field = expected_field["name"]
                    self.awaiting_confirmation = True
                    response = f'Great. We’ll begin collecting details for "{expected_field["name"]}".\nSaving "yes" for "{expected_field["name"]}". Is this correct? (yes/no)'
                    self.recent_messages[-1]["bot"] = response
                    return response

                elif yn_result == "no":
                    response = (
                        f"Sorry, the field \"{expected_field['name']}\" is required for this agreement.\n"
                        f"Please confirm you're ready to provide this information. (yes)"
                    )
                    self.recent_messages[-1]["bot"] = response
                    return response

                elif yn_result == "off_topic":
                    print(f"[DEBUG] User went off-topic while answering required-yes field '{expected_field['name']}'.")
                    response = llama_answer(
                        user_input=user_input,
                        active_schema=self.active_schema,
                        current_field=expected_field["name"],
                        current_question=expected_field["question"],
                        context=expected_field["context"],
                        recent_messages=self.recent_messages,
                        slots=self.slots,
                        user_state="off_topic"
                    )
                    response = f"{response}\n\nLet's get back to it: {expected_field['question']}"
                    self.recent_messages[-1]["bot"] = response
                    return response

                elif yn_result == "question":
                    print(f"[DEBUG] User asked a question while answering required-yes field '{expected_field['name']}'.")
                    response = llama_answer(
                        user_input=user_input,
                        active_schema=self.active_schema,
                        current_field=expected_field["name"],
                        current_question=expected_field["question"],
                        context=expected_field["context"],
                        recent_messages=self.recent_messages,
                        slots=self.slots,
                        user_state="question"
                    )
                    response = f"{response}\n\nLet's get back to it: {expected_field['question']}"
                    self.recent_messages[-1]["bot"] = response
                    return response

                elif yn_result == "terminate_session":
                    print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                    response = llama_answer(
                        user_input=user_input,
                        active_schema=self.active_schema,
                        current_field="exit_confirmation",
                        current_question=None,
                        context=None,
                        recent_messages=self.recent_messages,
                        slots=self.slots,
                        user_state=yn_result
                    )
                    self.awaiting_exit_confirmation = True
                    self.saved_context_before_exit = {"current_question": self._current_question()}
                    response = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                    self.recent_messages[-1]["bot"] = response
                    return response

                else:
                    response = f"Sorry, I didn’t quite catch that. Please confirm you're ready to begin answering \"{expected_field['name']}\". (yes)"
                    self.recent_messages[-1]["bot"] = response
                    return response
                
            if expected_field["name"] in {"rent_review_type"}: 
                result = classify_rent_input(user_input)
                print(f"[DEBUG] classify_rent_input for rent_review_type: {result}")

                if result in {"fixed", "fixed_percentage", "cpi_indexed", "fixed_increase"}:
                    self.pending_confirmation_value = result
                    self.pending_confirmation_field = expected_field["name"]
                    self.awaiting_confirmation = True
                    response = f'Saving "{result}" as the rent review type. Is this correct? (yes/no)'
                    self.recent_messages[-1]["bot"] = response
                    return response
                
                else:
                    response = "Sorry, I didn’t understand that. Please describe how the rent changes: does it stay fixed, increase by a fixed percentage, or follow inflation (CPI)?"
                    self.recent_messages[-1]["bot"] = response
                    return response
                
            if expected_field["name"] == "weekly_rent":
                result = extract_field_value(user_input, expected_field["name"], expected_field["question"])
                extracted_value = self.strip_wrapping_quotes(result)

                try:
                    weekly_rent = float(extracted_value)
                    if weekly_rent <= 0:
                        raise ValueError

                    monthly_rent = round(weekly_rent * 52 / 12, 2)
                    print(f"[DEBUG] Calculated monthly_rent from weekly_rent={weekly_rent}: {monthly_rent}")

                    # Store monthly rent silently
                    self.slots["monthly_rent"] = str(monthly_rent)

                    # Proceed with normal confirmation flow for weekly_rent
                    self.pending_confirmation_value = str(weekly_rent)
                    self.pending_confirmation_field = "weekly_rent"
                    self.awaiting_confirmation = True
                    response = (
                        f'Saving £{weekly_rent:.2f} per week. '
                        f'That works out to approximately £{monthly_rent:.2f} per month.\n'
                        f'Is this correct? (yes/no)'
                    )
                    self.recent_messages[-1]["bot"] = response
                    return response

                except ValueError:
                    response = "That doesn’t seem like a valid rent amount. Please enter a number (e.g., 300)."
                    self.recent_messages[-1]["bot"] = response
                    return response

            # Default field handling
            raw_value = extract_field_value(user_input, expected_field["name"], expected_field["question"])
            extracted_value = self.strip_wrapping_quotes(raw_value)
            print(f"[DEBUG] Extracted value for {expected_field['name']}: {extracted_value}")
            self.pending_confirmation_value = extracted_value
            self.pending_confirmation_field = expected_field["name"]
            self.awaiting_confirmation = True
            response = f"Saving \"{extracted_value}\" for \"{expected_field['name']}\". Is this correct? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response

        else:
            print(f"[DEBUG] Unexpected classification result during editing for field '{expected_field['name']}': {classification}")
            print(f"[DEBUG] Raw user input: {user_input}")
            response = f"I didn’t understand your answer for {expected_field['name']}. Could you rephrase it?"
            self.recent_messages[-1]["bot"] = response
            return response


    
    # ─────────────────────────────────────────────────────────────
    # Helper Functions
    # ─────────────────────────────────────────────────────────────

    def evaluate_condition(self, condition: str, slots: Dict[str, Any]) -> bool:
        try:
            # Use slots directly in eval's local scope, but validate allowed variable names
            safe_slots = {k: v for k, v in slots.items() if isinstance(k, str)}
            return eval(condition, {}, safe_slots)
        except Exception as e:
            print(f"[DEBUG] Condition eval error for '{condition}': {e}")
            return False
        
        
    def _prune_invalid_dependent_fields(self):
        print("[DEBUG] Pruning stale fields that are no longer valid.")
        all_fields = SCHEMAS[self.active_schema]["fields"]
        for field in all_fields:
            if "depends_on" in field and field["name"] in self.slots:
                if not self.evaluate_condition(field["depends_on"], self.slots):
                    print(f"[DEBUG] Removing invalidated field: {field['name']}")
                    del self.slots[field["name"]]
        
        # Phantom field pruning — these are not part of SCHEMAS, so we handle them manually
        if self.slots.get("wants_custom_clauses") != "yes":
            if "custom_clauses" in self.slots:
                print("[DEBUG] Removing phantom field: custom_clauses")
                del self.slots["custom_clauses"]

        if self.slots.get("shared_areas") != "yes":
            if "shared_areas_description" in self.slots:
                print("[DEBUG] Removing phantom field: shared_areas_description")
                del self.slots["shared_areas_description"]

        if self.slots.get("utilities_included") != "yes":
            for phantom in ("which_utilities_included", "which_utilities_not_included"):
                if phantom in self.slots:
                    print(f"[DEBUG] Removing phantom field: {phantom}")
                    del self.slots[phantom]

        if self.slots.get("property_includes_confirmation") != "yes":
            if "property_includes" in self.slots:
                print("[DEBUG] Removing phantom field: property_includes")
                del self.slots["property_includes"]


    def get_editable_fields(self):
        editable_fields = []
        for f in SCHEMAS[self.active_schema]["fields"]:
            if "depends_on" not in f or self.evaluate_condition(f["depends_on"], self.slots):
                editable_fields.append(f["name"])
        return editable_fields

    def _render_summary_and_ask_if_happy(self) -> str:
        print("[DEBUG] Rendering summary for user confirmation")
        self.awaiting_final_confirmation = True

        lines = []

        for key, value in self.slots.items():
            if key == "tenant_info":
                lines.append("- tenant_info:")
                for i, name in enumerate(value, 1):
                    lines.append(f"  {i}. {name}")
            elif key == "custom_clauses":
                lines.append("- custom_clauses:")
                for i, clause in enumerate(value, 1):
                    if isinstance(clause, dict):
                        lines.append(f"  {i}. [{clause.get('tag', 'general')}] {clause.get('text')}")
                    else:
                        lines.append(f"  {i}. {clause}")  # fallback for legacy format
            else:
                lines.append(f"- {key}: {value}")

        summary = "\n".join(lines)
        response = f"All required information has been collected:\n{summary}\n\nAre you happy with this information? (yes/no)"

        self.recent_messages[-1]["bot"] = response

        return response

    
    def _current_field(self) -> dict:
        while self.current_field_index < len(SCHEMAS[self.active_schema]["fields"]):
            field = SCHEMAS[self.active_schema]["fields"][self.current_field_index]
            print(f"[DEBUG] Checking field at index {self.current_field_index}: {field['name']}")

            # Skip the dynamic tenant_info field entirely
            if field["name"] == "tenant_info":
                self.current_field_index += 1
                continue

            if field["name"] == "monthly_rent" and "weekly_rent" in self.slots:
                self.current_field_index += 1
                continue

            # Skip fields with unmet conditions
            if "depends_on" in field and not self.evaluate_condition(field["depends_on"], self.slots):
                print(f"[DEBUG] _current_field: Skipping '{field['name']}' due to condition: {field['depends_on']}")
                self.current_field_index += 1
                continue

            # Skip fields without a 'question' key (e.g. derived fields)
            if "question" not in field:
                print(f"[DEBUG] _current_question: Skipping derived/non-question field: {field['name']}")
                self.current_field_index += 1
                continue

            print(f"[DEBUG] _current_field: index={self.current_field_index}, field_name={field['name']}")
            return field

        return {"name": "done"}  # fallback if at end
    
    def strip_wrapping_quotes(self, value: str) -> str:
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value
    

    def _reset_and_recollect_dependents(self, updated_field: str):
        print(f"[DEBUG] Checking for dependent fields of: {updated_field}")
        schema_fields = SCHEMAS[self.active_schema]["fields"]
        recollect_index = None

        def recurse_dependents(parent_field):
            nonlocal recollect_index
            for i, field in enumerate(schema_fields):
                if "depends_on" in field and parent_field in field["depends_on"]:
                    field_name = field["name"]
                    try:
                        valid = self.evaluate_condition(field["depends_on"], self.slots)
                    except Exception as e:
                        print(f"[DEBUG] Failed to eval condition: {field['depends_on']}. Error: {e}")
                        valid = False

                    if not valid:
                        print(f"[DEBUG] Resetting invalidated dependent: {field_name}")
                        self.slots.pop(field_name, None)
                    elif field_name not in self.slots and "question" in field:
                        print(f"[DEBUG] Will recollect field: {field_name}")
                        if recollect_index is None or i < recollect_index:
                            recollect_index = i
                        recurse_dependents(field_name)  # Recursively go deeper

        recurse_dependents(updated_field)

        if recollect_index is not None:
            print(f"[DEBUG] Re-entering flow at dependent field index {recollect_index}")
            self.current_field_index = recollect_index
            self.awaiting_confirmation = False
            self.pending_confirmation_field = None
            self.pending_confirmation_value = None
            self.editing_mode = True
            self.awaiting_final_confirmation = False
            self.all_information_gathered = False
            self.recollecting_dependent = True

        return recollect_index



    def _current_question(self) -> str:
        return SCHEMAS[self.active_schema]["fields"][self.current_field_index]["question"]

    def _is_relevant_to_field(self, user_input: str, field: dict) -> bool:
        return len(user_input.strip()) <= 50
    

    

    # ─────────────────────────────────────────────────────────────
    # CONFIRMATION ROUTER (between states)
    # ─────────────────────────────────────────────────────────────

    def confirm_document_selection(self, user_input: str) -> str:
        if getattr(self, "awaiting_exit_confirmation", False):
            interpretation = classify_field_input(user_input, "exit_confirmation", "Do you want to abandon the session?") # classify user inpt as an answer or otherwise
            print(f"[DEBUG] Classifying user input: {user_input}")
            print(f"[DEBUG] Classification: {interpretation}")

            if interpretation == "answer":
                classification = classify_confirmation_context(user_input) # if the user's input was recognized as an answer, what kind?
                print(f"[DEBUG] Identifying user input: {user_input}")
                print(f"[DEBUG] Identified: {classification}")

                if classification == "yes":
                    response = "Session aborted. Thank you for using the assistant."
                    self.reset()
                    self.recent_messages[-1]["bot"] = response
                    return response

                elif classification == "no":
                    response = "Okay, let's continue."
                    self.awaiting_exit_confirmation = False
                    self.recent_messages[-1]["bot"] = response
                    return response
                
                elif classification in {"question", "off_topic"}: # if the user's response was recognized as an asnwer, but on second inspection it was not a yes or no, then it falls into off_topic or question
                    print(f"[DEBUG] User asked a question or went off-topic during exit confirmation.")
                    confirmation_prompt = "The user is deciding whether to abandon the session and discard all collected information. Help clarify if they really want to exit."
                    response = llama_answer(
                        user_input=user_input,
                        active_schema=self.active_schema,
                        current_field="exit_confirmation",
                        current_question=confirmation_prompt,
                        context=None,
                        recent_messages=self.recent_messages,
                        slots=self.slots,
                        user_state=classification
                    )
                    print("[DEBUG] Recent messages history:", self.recent_messages)
                    self.recent_messages[-1]["bot"] = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all information? (yes/no)"
                    return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all information? (yes/no)"

            elif interpretation in {"question", "off_topic"}:
                print(f"[DEBUG] User asked a question or went off-topic during exit confirmation.")
                confirmation_prompt = "The user is deciding whether to abandon the session and discard all collected information. Help clarify if they really want to exit."
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=confirmation_prompt,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state=interpretation
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all information? (yes/no)"
                return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all information? (yes/no)"

            else:
                response = "Please confirm — do you want to exit? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

        # Normal document selection confirmation flow
        interpretation = classify_field_input(user_input, "document_selection", "Which document would you like to generate?")# classify user inpt as an answer or otherwise
        print(f"[DEBUG] confirm_document_selection called with input: {user_input}")
        print(f"[DEBUG] Interpretation: {interpretation}")


        if interpretation == "answer":
            classification = classify_confirmation_context(user_input) # if the user's input was recognized as an answer, what kind?
            print(f"[DEBUG] Identifying user input: {user_input}")
            print(f"[DEBUG] Identified: {classification}")

            if classification == "yes":
                self.active_schema = self._pending_schema
                self._pending_schema = None
                self.awaiting_doc_type_confirmation = False
                self.state = "info_retrieval"
                self.current_field_index = 0
                response = f"Great! Let's begin.\n{self._current_question()}"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "no":
                self.awaiting_doc_type_confirmation = False
                self.active_schema = None
                response = f"Okay, let's try again.\nWhat kind of document would you like to generate?\n{self._list_doc_options()}"
                self.recent_messages[-1]["bot"] = response
                return response

            elif classification == "question":
                print("[DEBUG] User asked a question during document selection confirmation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="question"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = f"{response}\n\nWould you like to proceed with this document type? (yes/no)"
                return f"{response}\n\nWould you like to proceed with this document type? (yes/no)"

            elif classification == "off_topic":
                print("[DEBUG] User gave an off-topic response during document selection confirmation.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="off_topic"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.recent_messages[-1]["bot"] = f"{response}\n\nWould you like to continue with {self._pending_schema}? (yes/no)"
                return f"{response}\n\nWould you like to continue with {self._pending_schema}? (yes/no)"
            
            elif classification == "terminate_session":
                print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
                response = llama_answer(
                    user_input=user_input,
                    active_schema=self.active_schema,
                    current_field="exit_confirmation",
                    current_question=None,
                    context=None,
                    recent_messages=self.recent_messages,
                    slots=self.slots,
                    user_state="terminate_session"
                )
                print("[DEBUG] Recent messages history:", self.recent_messages)
                self.awaiting_exit_confirmation = True
                self.saved_context_before_exit = {
                    "current_question": self._current_question()
                }
                self.recent_messages[-1]["bot"] = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
                return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
            
            else:
                response = "Could you clarify if you'd like to proceed with that document type? (yes/no)"
                self.recent_messages[-1]["bot"] = response
                return response

        elif interpretation == "question":
            print("[DEBUG] User asked a question during document selection confirmation.")
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state="question"
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            self.recent_messages[-1]["bot"] = f"{response}\n\nWould you like to proceed with this document type? (yes/no)"
            return f"{response}\n\nWould you like to proceed with this document type? (yes/no)"

        elif interpretation == "off_topic":
            print("[DEBUG] User gave an off-topic response during document selection confirmation.")
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state="off_topic"
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            self.recent_messages[-1]["bot"] = f"{response}\n\nWould you like to continue with {self._pending_schema}? (yes/no)"
            return f"{response}\n\nWould you like to continue with {self._pending_schema}? (yes/no)"

        elif interpretation == "terminate_session":
            print("[DEBUG] User indicated a desire to exit — confirming exit explicitly.")
            response = llama_answer(
                user_input=user_input,
                active_schema=self.active_schema,
                current_field="exit_confirmation",
                current_question=None,
                context=None,
                recent_messages=self.recent_messages,
                slots=self.slots,
                user_state="terminate_session"
            )
            print("[DEBUG] Recent messages history:", self.recent_messages)
            self.awaiting_exit_confirmation = True
            self.saved_context_before_exit = {
                "current_question": self._current_question()
            }
            self.recent_messages[-1]["bot"] = f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"
            return f"{response}\n\nJust to confirm — do you want to abandon this session and discard all collected information? (yes/no)"

        else:
            response = "Could you clarify if you'd like to proceed with that document type? (yes/no)"
            self.recent_messages[-1]["bot"] = response
            return response


    def finalize_document(self) -> dict:
        final_fields = self.slots.copy()  # Start with user-provided fields

        # Add derived fields if their conditions are met
        for field in SCHEMAS[self.active_schema]["fields"]:
            if field.get("derived"):
                condition = field.get("condition", "true")
                if self.evaluate_condition(condition, final_fields):
                    final_fields[field["name"]] = field["text"]
                    print(f"[DEBUG] Added derived field: {field['name']}")

        return {
            "status": "complete",
            "document_type": self.active_schema,
            "fields": final_fields
        }
