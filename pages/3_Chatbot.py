
import streamlit as st

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from google.genai.types import HttpRetryOptions

st.set_page_config(
    page_title="Trade Insights Chatbot",
    page_icon="🌍",
    layout="wide"
)
st.title("🌍 Trade Insights Chatbot")

st.write(
    "Ask questions about international trade, imports, "
    "exports, trade balances, and economic development."
)

try:
    api_key = st.secrets["GOOGLE_API_KEY"]

    if not api_key or not api_key.strip():
        raise ValueError("Google API key is empty.")

except Exception as error:

    st.error("Could not load your Google API key.")

    with st.expander("Technical error details"):
        st.code(f"{type(error).__name__}: {error}")

    st.stop()

try:

    retry_options = HttpRetryOptions(
        attempts=3,
        initial_delay=1.0,
        max_delay=8.0,
        http_status_codes=[503, 504]
    )

    provider = GoogleProvider(
        api_key=api_key,
        retry_options=retry_options
    )

    model = GoogleModel(
        "gemini-3.5-flash-lite",
        provider=provider
    )


    agent = Agent(
        model,
        instructions="""
        You are an AI assistant for Global Trade Insights.

        Your main topics are:
        - International trade
        - Merchandise imports and exports
        - Trade balances
        - Trade surpluses and deficits
        - International economics
        - Economic development

        Explain economic concepts clearly and provide
        examples when helpful.

        Stay focused on international trade and economics.
        If a question is unrelated, politely guide the user
        back to the main subject.

        You do not have access to APIs, datasets,
        live data, or external sources.

        Never invent statistics or pretend to retrieve data.

        If a user asks for exact or current trade figures,
        explain that you cannot look them up.

        Remember relevant information shared by the user
        during the conversation and use it in later answers.
        """
    )

except Exception as error:

    st.error("Could not initialize the Gemini chatbot.")

    with st.expander("Technical error details"):
        st.code(f"{type(error).__name__}: {error}")

    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_history" not in st.session_state:
    st.session_state.message_history = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input(
    "Ask a question about international trade..."
)

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    try:

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                result = agent.run_sync(
                    prompt,
                    message_history=st.session_state.message_history
                )

                answer = result.output

                st.write(answer)

        # Save conversation history
        st.session_state.message_history.extend(
            result.new_messages()
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as error:

        error_message = (
            "Sorry, something went wrong. "
            "Please try again later."
        )

        with st.chat_message("assistant"):

            st.error(error_message)

            with st.expander("Technical error details"):

                st.write(
                    "Error type:",
                    type(error).__name__
                )

                st.code(str(error))

                if error.__cause__ is not None:
                    st.write("Original error:")
                    st.code(str(error.__cause__))

        st.session_state.messages.append({
            "role": "assistant",
            "content": error_message
        })

if st.button("Clear Conversation"):

    st.session_state.messages = []
    st.session_state.message_history = []

    st.rerun()


