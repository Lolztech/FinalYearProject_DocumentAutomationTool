SCHEMAS = {
    "rental_agreement": {
        "display_name": "Rental Agreement",
        "fields": [
            # Had to add section sub-fields in all fields cuz the conversation logic would start throwing a tantrum if it found a "section" field withot a "name" or "question" sub-field in it, and I cant be bothered to go to the conversation.py and uproot all the logic again, ive done it so many times now that I dont even know how many checks there are that would need to change 
            # Tenant Details
            {
                "section": "Tenant Details",
                "name": "tenant_count",
                "question": "How many tenants will there be?",
                "context": "This sets how many people are signing as tenants. This affects liability, joint responsibility, and names on the contract. Example: 2."
            },
            {
                "section": "Tenant Details",
                "name": "additional_occupants_check",
                "question": "Will there be any other occupants to the property who are not paying tenants? (yes/no)",
                "context": "This checks if there are other adults or children living in the property who are not named tenants. This affects legal obligations and potential overcrowding."
            },
            {
                "section": "Tenant Details",
                "name": "additional_occupants_count",
                "question": "How many additional occupants, who are not tenants, will there be?",
                "depends_on": "additional_occupants_check == 'yes'",
                "context": "This helps identify who else will live in the property and may be used in checks around overcrowding or housing compliance."
            },

            # Landlord Contact Information
            {
                "section": "Landlord Contact Information",
                "name": "landlord_name",
                "question": "What is the landlord's name?",
                "context": "The legal full name of the landlord. Must be included to identify the party granting the tenancy."
            },
            {
                "section": "Landlord Contact Information",
                "name": "landlord_address",
                "question": "What is the landlord’s contact address?",
                "context": "Used for service of documents and notices. Must be a valid address where the landlord can be contacted."
            },
            {
                "section": "Landlord Contact Information",
                "name": "landlord_email",
                "question": "What is the landlord’s email address?",
                "context": "For electronic correspondence. Optional for service of legal notices unless explicitly permitted."
            },
            {
                "section": "Landlord Contact Information",
                "name": "landlord_phone",
                "question": "What is the landlord’s phone number?",
                "context": "Useful for communication. Not required by law but improves clarity between parties."
            },

            # Notice Service Details
            {
                "section": "Notice Service Details",
                "name": "notice_service_same_as_landlord",
                "question": "Should formal notices be served to the landlord's contact address and email? (yes/no)",
                "context": "Establishes whether the default landlord contact details are acceptable for formal legal notices."
            },
            {
                "section": "Notice Service Details",
                "name": "notice_service_address",
                "question": "What postal address should be used for serving formal notices?",
                "depends_on": "notice_service_same_as_landlord == 'no'",
                "context": "Alternative postal address for service if not using landlord’s default address."
            },
            {
                "section": "Notice Service Details",
                "name": "notice_service_email_allowed",
                "question": "Will you accept formal legal notices via email? (yes/no)",
                "depends_on": "notice_service_same_as_landlord == 'no'",
                "context": "Determines if notices (e.g., Section 21) can be legally sent by email. Must be clearly agreed."
            },
            {
                "section": "Notice Service Details",
                "name": "notice_service_email",
                "question": "What email address should be used for serving formal notices?",
                "depends_on": "notice_service_same_as_landlord == 'no' and notice_service_email_allowed == 'yes'",
                "context": "Only used if both conditions above are met. This will be the address for formal legal email correspondence."
            },

            # Property Description
            {
                "section": "Property Description",
                "name": "property_address",
                "question": "Please provide the full property address including the postal address (e.g. 808 Caspian House, 9 Violet Road, W3 3NV):",
                "context": "The legal address of the rental premises. This is the subject of the agreement and must be precise."
            },
            {
                "section": "Property Description",
                "name": "property_description",
                "question": "Please provide a brief description of the property (e.g., How many rooms, flat or house, etc. (one ensuite bedroom in a communal flat)):",
                "context": "Provides additional clarity on the size and nature of the property. Can include layout or number of bedrooms."
            },
            {
                "section": "Property Description",
                "name": "property_includes_confirmation",
                "question": "We will need a list of spaces included in the property (e.g. Garage, Terrace, Gardens, Balconies, etc.) are you ready? (yes/no)",
                "context": "Initiates the collection of specific areas or facilities exclusively included in the tenancy."
            },
            {
                "section": "Property Description",
                "name": "shared_areas",
                "question": "Are there shared facilities (hallways, stairs, kitchen, bathrooms, lobbies, etc.)? (yes/no)",
                "context": "Clarifies if the tenant will share any parts of the building with others, important in HMOs or flats."
            },
            {
                "section": "Property Description",
                "name": "furnished",
                "question": "Is the property furnished? (yes/no)",
                "context": "Furnished properties include items like beds, sofas, tables. This affects deposits and inventory."
            },
            {
                "section": "Property Description",
                "name": "mortgage_check",
                "question": "Is the property mortgaged? (yes/no)",
                "context": "Checks whether lender consent may be needed for the tenancy."
            },

            # Rent Terms
            {
                "section": "Rent Terms",
                "name": "rent_review_type",
                "question": "Will the rent remain fixed throughout the tenancy, or is there a provision for annual increases (e.g., by a fixed percentage or linked to inflation)? Please explain how rent changes over time, if at all.",
                "context": "Defines how rent changes over time. Fixed rent is stable, but CPI or fixed % increases are common in long lets."
            },
            {
                "section": "Rent Terms",
                "name": "fixed_percentage_increase",
                "question": "By what percentage will the rent be increased each term?",
                "depends_on": "rent_review_type == 'fixed_percentage'",
                "context": "Common values: 3–5% per annum."
            },
            {
                "section": "Rent Terms",
                "name": "fixed_value_increase",
                "question": "By what value will the rent be increased each term?",
                "depends_on": "rent_review_type == 'fixed_increase'",
                "context": "This denotes an increase to the rent by a vixed value. Answer can be £300, or any other fixed value."
            },
            {
                "section": "Rent Terms",
                "name": "weekly_rent",
                "question": "How much is the weekly rent?",
                "context": "Used if rent is calculated weekly instead of monthly. Important for housing benefit and universal credit assessments."
            },            
            {
                "section": "Rent Terms",
                "name": "monthly_rent",
            },
            # Payment Information
            {
                "section": "Payment Information",
                "name": "payment_method",
                "question": "What method of payment will be used by the tenants for the rent (e.g. standing order / direct debit / cheque / cash)?",
                "context": "Indicates how rent will be paid. Standing order is most common."
            },
            {
                "section": "Payment Information",
                "name": "payment_day",
                "question": "What day of the month or week should rent be paid regularly? (e.g., 1st of the month, every Monday, last Friday, etc.)",
                "context": "This sets the recurring due date for rent payments. Important for tracking arrears."
            },
            {
                "section": "Payment Information",
                "name": "first_payment_amount",
                "question": "What is the amount of the first rent payment?",
                "context": "The amount paid before or at move-in. May differ from regular monthly rent due to proration."
            },
            {
                "section": "Payment Information",
                "name": "first_payment_due_date",
                "question": "When is the first payment due?",
                "context": "Sets the deadline for the initial payment. Often the tenancy start date."
            },

            # Deposit and Protection
            {
                "section": "Deposit and Protection",
                "name": "deposit_amount",
                "question": "What is the deposit amount?",
                "context": "Legally capped (e.g., 5 weeks’ rent if rent under £50,000/year). Protects against damage or unpaid rent."
            },
            {
                "section": "Deposit and Protection",
                "name": "deposit_protection_scheme",
                "question": "Which deposit protection scheme will be used? (only three available schemes in England and Wales: Deposit Protection Service, MyDeposits, Tenancy Deposit Scheme)",
                "context": "In England and Wales, deposits must be protected. Choose one of the 3 government-backed schemes."
            },

            # Lease Duration
            {
                "section": "Lease Duration",
                "name": "start_date",
                "question": "What is the start date of the tenancy?",
                "context": "When the tenancy begins. Usually the move-in date."
            },
            {
                "section": "Lease Duration",
                "name": "end_date",
                "question": "What is the end date of the tenancy?",
                "context": "When the fixed term expires. Can roll into periodic tenancy if not renewed."
            },
            {
                "section": "Lease Duration",
                "name": "has_break_clause",
                "question": "Is there a break clause in the agreement? (yes/no)",
                "context": "A break clause allows early termination by either party. Common after 6 months with 2 months’ notice."
            },
            {
                "section": "Lease Duration",
                "name": "break_clause_notice",
                "question": "How much notice must be given to activate the break clause? (Please note that under the Housing Act 1988 a break clause notice cannot be under 2 months)",
                "depends_on": "has_break_clause == 'yes'",
                "context": "Under the Housing Act 1988, a break clause must provide at least 2 months' notice. This ensures fairness and legal validity."
            },

            # Responsibilities and Utilities
            {
                "section": "Responsibilities and Utilities",
                "name": "council_tax_included",
                "question": "Is the council tax included in the rent?",
                "context": "Clarifies responsibility. Often excluded in HMOs, sometimes included in student lets."
            },
            {
                "section": "Responsibilities and Utilities",
                "name": "utilities_included",
                "question": "Are any utilities included in the rent (e.g. gas, water, electricity)? (yes/no)",
                "context": "Used to determine which services the tenant pays for. Affects budgeting and affordability."
            },
            {
                "section": "Responsibilities and Utilities",
                "name": "key_handover_date",
                "question": "On what date will the keys be handed over to the tenant?",
                "context": "This should be on or just before the tenancy start date. Important for legal possession and practical access."
            },
            {
                "section": "Responsibilities and Utilities",
                "name": "tenant_absence",
                "question": "How many days should have to pass before the tenant is expected to give written notice of prolonged absence? (e.g. 14 days, 28 days, etc.)",
                "context": "Used in clauses relating to abandonment or security. Typical period: 14–28 days."
            },

            # Optional Permissions
            {
                "section": "Optional Permissions",
                "name": "alterations_permitted",
                "question": "Are the tenants permitted to make minor alterations to the property (Hang paintings, install shelving, nail items to the wall, etc.)? (yes/no)",
                "context": "Defines what minor changes are allowed. Can include decorations or fixtures."
            },
            {
                "section": "Optional Permissions",
                "name": "pets_allowed",
                "question": "Are pets allowed? (yes/no)",
                "context": "Landlords may prohibit or limit pets. Important for legal compliance with pet clauses and property condition."
            },
            {
                "section": "Optional Permissions",
                "name": "subletting_allowed",
                "question": "Is subletting allowed? (yes/no)",
                "context": "Establishes whether tenants can rent out the property (or part of it) to others."
            },
            {
                "section": "Optional Permissions",
                "name": "is_deed",
                "question": "Is the contract meant to be signed as a deed or not? (yes/no)",
                "context": "Deeds allow longer limitation periods (12 years vs 6). Required in some cases where no consideration is exchanged."
            },
            {
                "section": "Optional Permissions",
                "name": "business_use_allowed",
                "question": "Is running a business from the property allowed? (yes/no)",
                "context": "Some landlords prohibit business use due to mortgage or lease restrictions."
            },

            # Special Clauses — Always Last
            {
                "section": "Special Clauses",
                "name": "wants_custom_clauses",
                "question": "Would you like to add any special or unique terms to the contract? These can range from adding a no smoking clause, to other uinque requirements you might have. (yes/no)",
                "context": "Allows the tenant or landlord to include extra clauses specific to their needs."
            }
        ]
    },

# left to work on after FYP - Software can be expanded to handle more than just ASTs
    "nda": {
        "display_name": "Non-Disclosure Agreement (NDA)",
        "fields": [
            {"name": "disclosing_party", "question": "Who is the disclosing party?"},
            {"name": "receiving_party", "question": "Who is the receiving party?"},
            {"name": "purpose", "question": "What is the purpose of the NDA?"}
        ]
    }
}
