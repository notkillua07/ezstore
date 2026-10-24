"""EZStore Sales Advisor: answers sales questions from the OKF knowledge bundle and hands quotation work to
the quotation agent over the A2A protocol.

    sales_advisor (LlmAgent)
      ├─ tools: list_knowledge / search_knowledge / read_concept   (OKF bundle in advisor/knowledge/ezstore)
      └─ sub-agent: quotation_agent (RemoteA2aAgent → http://<quotation agent>/a2a/quotation_agent)
"""

import os

from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .knowledge import list_knowledge, read_concept, search_knowledge

APP_NAME = "sales_advisor"
MODEL = os.environ.get("ADVISOR_MODEL") or os.environ.get("AGENT_MODEL", "gemini-3.8-flash")
# Must match the origin the quotation agent advertises in its agent card (its APP_URL); A2A rejects a mismatch.
QUOTATION_AGENT_URL = os.environ.get("QUOTATION_AGENT_URL", "http://127.0.0.1:8001")

quotation_agent = RemoteA2aAgent(
    name="quotation_agent",
    description=(
        "EZStore quotation agent, reached over A2A. It performs operations on real quotations: look up a "
        "quotation, list a customer's quotations, duplicate, change the pricing factor, change the total price, "
        "convert to an order."
    ),
    # Local: fetch the card over loopback http. Docker: read a card file (a2a/quotation_agent_card.json), because
    # ADK only fetches cards over https or loopback, while a card from a local file is trusted by the deployer.
    agent_card=os.environ.get("QUOTATION_AGENT_CARD")
    or f"{QUOTATION_AGENT_URL}/a2a/quotation_agent{AGENT_CARD_WELL_KNOWN_PATH}",
)

INSTRUCTION = """\
You are the EZStore Sales Advisor (業務顧問) for the sales team of an office-supplies company.

Knowledge questions (policies, customer levels, pricing rules, quotation and order statuses, products and prices):
- Always look the answer up first: call search_knowledge, then read_concept on the best match. Never answer from memory.
- Answer only with what the concepts say. If the knowledge bundle does not cover it, say so plainly.
- End the answer with the concepts you used, as plain text, for example: 來源：policies/customer-levels
- When you calculate a price, show the formula and numbers (unit price = list price × pricing factor).

Quotation operations on real data (look up a quotation, list a customer's quotations, duplicate, change the pricing
factor, change the total price, convert to an order): transfer to quotation_agent. Pass the user's request on with
the quotation number and values unchanged. Do not invent quotation numbers.

Everything else (weather, chit-chat, editing customers or products): politely say you only help with EZStore sales
knowledge and quotation work.

Reply in the user's language (Traditional Chinese or English). Write links as plain URLs, never Markdown [text](url).
"""

root_agent = Agent(
    name=APP_NAME,
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=1.0, max_delay=16.0, exp_base=2.0),
    ),
    description="EZStore sales advisor: answers from the OKF knowledge bundle, delegates quotation work over A2A.",
    instruction=INSTRUCTION,
    tools=[list_knowledge, search_knowledge, read_concept],
    sub_agents=[quotation_agent],
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

app = App(root_agent=root_agent, name=APP_NAME)
