"""
Evaluation Dataset
====================
Test cases for our agents. Each case has a question, which agent/route
should handle it, and the key facts a correct answer must contain.
"""

EVAL_CASES = [
    {
        "id": "vacation_policy_basic",
        "question": "How many vacation days do I get per year?",
        "expected_route": "knowledge",
        "expected_facts": ["15", "PTO", "accrue"],
    },
    {
        "id": "vacation_policy_rephrased",
        "question": "How many days off do I get annually?",
        "expected_route": "knowledge",
        "expected_facts": ["15 days", "accrue"],
    },
    {
        "id": "onboarding_basic",
        "question": "What happens when a new employee joins?",
        "expected_route": "knowledge",
        "expected_facts": ["IT setup", "HR paperwork", "security training"],
    },
    {
        "id": "incident_response_basic",
        "question": "How fast do we need to report a security incident?",
        "expected_route": "knowledge",
        "expected_facts": ["1 hour", "SOC"],
    },
    {
        "id": "ticket_status_basic",
        "question": "What's the status of TICKET-101?",
        "expected_route": "it_support",
        "expected_facts": ["Open", "network", "VPN"],
    },
    {
        "id": "ticket_status_resolved",
        "question": "Is TICKET-102 resolved?",
        "expected_route": "it_support",
        "expected_facts": ["Resolved", "password"],
    },
]