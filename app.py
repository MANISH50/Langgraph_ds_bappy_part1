import os
import certifi
import streamlit as st

from dotenv import load_dotenv
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI


# ============================================================
# CONFIG
# ============================================================

os.environ["SSL_CERT_FILE"] = certifi.where()

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LangGraph AI Chatbot",
    page_icon="🤖",
    layout="centered"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at top right,
                #20204a 0%,
                #0b0b12 35%,
                #050509 100%
            );
        color: white;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
    }

    .title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(
            90deg,
            #8b9cff,
            #c084fc,
            #67e8f9
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        text-align: center;
        color: #9093a5;
        margin-bottom: 30px;
    }

    .chat-container {
        background: rgba(20,20,32,0.75);
        border: 1px solid #29293d;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .user-message {
        background: #25254a;
        border-radius: 16px;
        padding: 13px 17px;
        margin: 8px 0 8px auto;
        max-width: 80%;
        color: white;
    }

    .assistant-message {
        background: #151520;
        border: 1px solid #29293d;
        border-radius: 16px;
        padding: 13px 17px;
        margin: 8px auto 8px 0;
        max-width: 80%;
        color: #eeeeF5;
    }

    .status-box {
        background: #11111a;
        border: 1px solid #29293d;
        border-radius: 14px;
        padding: 14px;
        margin: 10px 0;
        color: #a7a9b8;
    }

    .status-active {
        color: #a78bfa;
    }

    .status-complete {
        color: #4ade80;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🤖 LangGraph AI Chatbot</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Question → Answer → Refine → Response</div>',
    unsafe_allow_html=True
)


# ============================================================
# CHECK API KEY
# ============================================================

if not OPENAI_API_KEY:

    st.error(
        "OPENAI_API_KEY is missing. "
        "Please add it to your .env file."
    )

    st.stop()


# ============================================================
# OPENAI MODEL
# ============================================================

model = ChatOpenAI(
    model="gpt-4.1-nano-2025-04-14",
    temperature=0,
    api_key=OPENAI_API_KEY
)


# ============================================================
# LANGGRAPH STATE
# ============================================================

class QuestionAnswerState(TypedDict):

    question: str
    answer: str
    temp: str


# ============================================================
# NODE 1
# ============================================================

def question_answer_node(
    state: QuestionAnswerState
) -> QuestionAnswerState:

    question = state["question"]

    prompt = f"""
Answer the following question:

{question}

If the input contains offensive content or any misleading sentences,
respond exactly with:

It is not a question.
"""

    response = model.invoke(prompt)

    answer = response.content

    state["answer"] = answer
    state["temp"] = answer

    return state


# ============================================================
# NODE 2
# ============================================================

def refine_answer(
    state: QuestionAnswerState
) -> QuestionAnswerState:

    answer = state["answer"]

    if answer == "It is not a question.":

        return state

    prompt = f"""
Refine the following answer.

Requirements:
- Use simple English.
- Keep the answer concise.
- Maximum 20 words.
- Keep the meaning correct.

Text:

{answer}
"""

    response = model.invoke(prompt)

    state["answer"] = response.content

    return state


# ============================================================
# BUILD LANGGRAPH
# ============================================================

graph = StateGraph(QuestionAnswerState)

graph.add_node(
    "question_answer",
    question_answer_node
)

graph.add_node(
    "refining_answer",
    refine_answer
)

graph.add_edge(
    START,
    "question_answer"
)

graph.add_edge(
    "question_answer",
    "refining_answer"
)

graph.add_edge(
    "refining_answer",
    END
)

workflow = graph.compile()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    if message["role"] == "user":

        st.markdown(
            f"""
            <div class="user-message">
                👤 {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="assistant-message">
                🤖 {message["content"]}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask me anything..."
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    # Store user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    st.markdown(
        f"""
        <div class="user-message">
            👤 {question}
        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # PROCESSING STATUS
    # --------------------------------------------------------

    status = st.empty()


    # Step 1

    status.markdown(
        """
        <div class="status-box status-active">
            🧠 <b>Step 1/2</b> — Generating answer...
        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # RUN LANGGRAPH
    # --------------------------------------------------------

    initial_state = {
        "question": question,
        "answer": "",
        "temp": ""
    }

    try:

        final_state = workflow.invoke(
            initial_state
        )


        # Step 2

        status.markdown(
            """
            <div class="status-box status-active">
                ✨ <b>Step 2/2</b> — Refining answer...
            </div>
            """,
            unsafe_allow_html=True
        )


        answer = final_state["answer"]


        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        status.markdown(
            """
            <div class="status-box status-complete">
                ✅ <b>Completed</b> — LangGraph workflow finished
            </div>
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # ASSISTANT RESPONSE
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="assistant-message">
                🤖 {answer}
            </div>
            """,
            unsafe_allow_html=True
        )


        # Store response

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


    except Exception as e:

        status.error(
            "❌ Something went wrong."
        )

        st.exception(e)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🤖 LangGraph"
    )

    st.markdown(
        """
        **Workflow**

        🟢 START

        ↓

        🧠 Question Answer

        ↓

        ✨ Refine Answer

        ↓

        🔴 END
        """
    )

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()