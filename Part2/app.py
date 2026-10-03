import hashlib
import os
from typing import Annotated, TypedDict
from uuid import uuid4
import certifi
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv()

class ChatState(TypedDict):
	messages: Annotated[list[BaseMessage], add_messages]

@st.cache_resource
def get_chatbot() -> object:
	"""Build one in-memory graph so its checkpoint store is shared by sessions."""
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY is not configured.")

	model = ChatOpenAI(
		model=os.getenv("OPENAI_MODEL", "gpt-4.1-nano-2025-04-14"),
		temperature=0.7,
		max_tokens=1000,
		api_key=api_key,
	)

	def chat_node(state: ChatState) -> dict[str, list[AIMessage]]:
		response = model.invoke(state["messages"])
		return {"messages": [response]}

	graph = StateGraph(ChatState)
	graph.add_node("chat", chat_node)
	graph.add_edge(START, "chat")
	graph.add_edge("chat", END)
	return graph.compile(checkpointer=MemorySaver())

def make_thread_id(user_id: str) -> str:
	"""Keep user-provided identifiers private and valid as checkpoint keys."""
	return hashlib.sha256(user_id.encode("utf-8")).hexdigest()

def get_history(chatbot: object, thread_id: str) -> list[BaseMessage]:
	try:
		state = chatbot.get_state({"configurable": {"thread_id": thread_id}})
		return list(state.values.get("messages", []))
	except Exception:
		return []

st.set_page_config(
	page_title="LangGraph Chat",
	page_icon="💬",
	layout="centered",
)

st.markdown(
	"""
	<style>
	.stApp { background: radial-gradient(circle at 10% 0%, #163b46 0%, #081216 42%, #050708 100%); }
	[data-testid="stHeader"] { background: transparent; }
	.block-container { max-width: 860px; padding-top: 2.5rem; }
	.hero h1 { color: #e6f7f4; font-size: 2.8rem; letter-spacing: -0.04em; margin-bottom: 0.25rem; }
	.hero p { color: #9db7b6; margin-bottom: 2rem; }
	[data-testid="stSidebar"] { background: #0a171b; border-right: 1px solid #1d3438; }
	.stChatMessage { border: 1px solid rgba(132, 196, 188, 0.12); }
	</style>
	""",
	unsafe_allow_html=True,
)

st.markdown(
	'<div class="hero"><h1>Chat, with memory.</h1><p>A calm LangGraph conversation that remembers where you left off.</p></div>',
	unsafe_allow_html=True,
)

with st.sidebar:
	st.subheader("Conversation")
	user_id = st.text_input("User ID", value="guest", max_chars=80).strip() or "guest"
	st.caption("Your ID selects your saved conversation in this running app.")
	if st.button("Start fresh", use_container_width=True):
		st.session_state["conversation_nonce"] = uuid4().hex
		st.rerun()

conversation_nonce = st.session_state.setdefault("conversation_nonce", "default")
thread_id = make_thread_id(f"{user_id}:{conversation_nonce}")
st.session_state["last_thread_id"] = thread_id

try:
	chatbot = get_chatbot()
except Exception as error:
	st.error(f"Chatbot setup failed: {error}")
	st.info("Add OPENAI_API_KEY to .env, then restart Streamlit.")
	st.stop()

for message in get_history(chatbot, thread_id):
	if isinstance(message, HumanMessage):
		role = "user"
	elif isinstance(message, AIMessage):
		role = "assistant"
	else:
		continue
	with st.chat_message(role):
		st.markdown(message.content)

prompt = st.chat_input("Ask anything...")
if prompt:
	with st.chat_message("user"):
		st.markdown(prompt)
	with st.chat_message("assistant"):
		with st.spinner("Thinking..."):
			try:
				result = chatbot.invoke(
					{"messages": [HumanMessage(content=prompt)]},
					config={"configurable": {"thread_id": thread_id}},
				)
				response = result["messages"][-1].content
				st.markdown(response)
			except Exception as error:
				st.error("I could not complete that message.")
				st.caption(f"Details: {error}")