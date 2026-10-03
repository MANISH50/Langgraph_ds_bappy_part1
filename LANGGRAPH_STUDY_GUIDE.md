# LangGraph Study Guide

A quick-reference guide based on the notebooks in this project.

Covered notebooks:

- `1_Temperature_Conversion_Workflow.ipynb`
- `2_Question_and_Answer.ipynb`
- `3_BlogCreation.ipynb`
- `5_Essay_Workflow.ipynb`
- `6_Conditional_Workflows.ipynb`
- `7_Conditional_WorkFlow_2.ipynb`
- `8_Iterative_workflow.ipynb`
- `Part2/1_Chatworkflow.ipynb`
- `Part2/2_Chatworkflow.ipynb`
- `Part2/3_MemoryPersist.ipynb`

---

## 1. LangGraph In One Picture

LangGraph is a way to build applications as graphs.

- The **state** stores the current data.
- A **node** performs one task.
- An **edge** decides what runs next.
- The graph moves through nodes until it reaches `END`.
- A node can update part of the state.
- Later nodes can use those updates.
- A checkpointer can save state between calls.

Simple flow:

```text
Input state -> Node A -> Node B -> Node C -> Final state
```

A useful mental model:

```text
State = shared memory
Node = worker
Edge = route
Graph = complete workflow
```

### Standard pattern used in this guide

Every concept in this guide follows the same structure:

1. What it is
2. Why it matters
3. How it is used
4. Example code
5. Rule to remember

This keeps the explanations consistent and easier to study.

> Rule to memorize: If a workflow must remember context, persist it. If multiple users or threads run at the same time, separate them with a unique `thread_id`.
>
> Short version: persist state + isolate thread state.
>
> Final rule: Persist state when memory is needed, and use a unique `thread_id` for every separate conversation or workflow instance.

### Standardized code style

Use clean, consistent, readable Python formatting. Avoid hidden line-break escapes and keep each example easy to scan.

```python
import tkinter as tk

root = tk.Tk()
root.title("Dark Mode Example")
root.geometry("300x200")

dark_bg = "#222222"
light_fg = "#F5F5F5"

root.configure(bg=dark_bg)

label = tk.Label(
    root,
    text="Hello, Dark Mode!",
    bg=dark_bg,
    fg=light_fg,
    font=("Arial", 14),
)
label.pack(pady=20)

root.mainloop()
```

This is the format used across the guide: clean indentation, clear names, single purpose per block, and no confusing escaped line breaks.

---

## 2. The Most Important Import

```python
from langgraph.graph import StateGraph, START, END
```

### `StateGraph`

Purpose:

- Creates a graph that works with a defined state shape.
- Stores the nodes and edges of the workflow.
- Makes the workflow readable as a sequence or decision tree.

How it is used:

```python
graph = StateGraph(TemperatureState)
graph.add_node("convert_temp", convert_temp)
graph.add_edge(START, "convert_temp")
graph.add_edge("convert_temp", END)
workflow = graph.compile()
```

Real-world uses:

- Customer support workflows.
- Document processing pipelines.
- Approval systems.
- Research agents.
- Content generation and review.
- Multi-step data transformation.

### `START`

Purpose:

- Special marker for the beginning of a graph.
- It is not a normal node written by you.

Example:

```python
graph.add_edge(START, "create_outline")
```

Meaning:

- Start the graph at `create_outline`.

### `END`

Purpose:

- Special marker for the end of a graph.
- It tells LangGraph that no more nodes should run.

Example:

```python
graph.add_edge("create_blogtext", END)
```

Meaning:

- Finish after the blog text is created.

---

## 3. State

State is the shared data object passed through the graph.

Example from the temperature workflow:

```python
class TemperatureState(TypedDict):
    temperature_celsius: float
    temperature_fahrenheit: float
    label_weather: str
```

The state has three fields:

- `temperature_celsius`: input value.
- `temperature_fahrenheit`: calculated value.
- `label_weather`: final category.

The graph flow is:

```text
temperature_celsius
        |
        v
convert_temp
        |
        v
temperature_fahrenheit
        |
        v
label_weather
        |
        v
label_weather
```

### Why state matters

- Nodes do not need to pass many separate arguments.
- Every node receives the same workflow context.
- One node can produce data for another node.
- The final state contains the workflow result.

### State design rule

Keep state focused.

Good:

```python
class BlogCreator(TypedDict):
    content: str
    outline: str
    blogtext: str
```

Avoid:

- Unused fields.
- Duplicate values.
- Fields with unclear names.
- Mixing unrelated workflows in one state.

### `TypedDict`

Import:

```python
from typing import TypedDict
```

Purpose:

- Describes expected state keys and their Python types.
- Helps editors and type checkers understand the workflow.
- Makes the graph easier to read.

Important:

- `TypedDict` is mainly a type description.
- It does not fully validate values at runtime.
- A wrong value can still enter the state unless you validate it yourself.

---

## 4. Nodes

A node is a Python function registered in the graph.

Example:

```python
def convert_temp(state: TemperatureState) -> TemperatureState:
    celsius = state["temperature_celsius"]
    fahrenheit = (celsius * 9 / 5) + 32
    return {"temperature_fahrenheit": round(fahrenheit, 2)}
```

Register it:

```python
graph.add_node("convert_temp", convert_temp)
```

### What a node does

- Receives the current state.
- Performs one clear task.
- Returns new or changed state values.

Common node tasks in your notebooks:

- Convert a temperature.
- Label weather.
- Ask an LLM a question.
- Refine an answer.
- Create a blog outline.
- Create blog text.
- Evaluate essay language.
- Analyze a review.
- Approve, reject, or flag content.
- Generate, evaluate, and improve a social media post.

### Node naming

Use names that describe actions:

- `create_outline`
- `analyze_post`
- `run_diagnosis`
- `final_evaluation`

Avoid unclear names such as:

- `step1`
- `process`
- `worker`

### Return updates instead of mutating state

Your notebooks often mutate state directly:

```python
state["answer"] = answer
return state
```

A clearer pattern is:

```python
return {"answer": answer}
```

Benefits:

- Shows exactly what the node changed.
- Reduces accidental changes to unrelated fields.
- Works better when several branches update the state.

---

## 5. Edges

An edge connects one graph point to another.

### `add_edge`

Import:

```python
from langgraph.graph import StateGraph, START, END
```

Usage:

```python
graph.add_edge("create_outline", "create_blogtext")
```

Meaning:

- Run `create_blogtext` after `create_outline`.

### Sequential edges

A sequential workflow runs in a fixed order:

```python
graph.add_edge(START, "convert_temp")
graph.add_edge("convert_temp", "label_weather")
graph.add_edge("label_weather", END)
```

Flow:

```text
START -> convert_temp -> label_weather -> END
```

Examples in the notebooks:

```text
START -> question_answer -> refining_answer -> END
START -> create_outline -> create_blogtext -> END
```

Real-world example:

```text
Receive invoice -> Extract fields -> Validate fields -> Save invoice
```

---

## 6. Compile and Invoke

### `compile`

Usage:

```python
workflow = graph.compile()
```

Purpose:

- Validates the graph structure.
- Converts the graph builder into an executable graph.
- Prepares the workflow to run.

With memory:

```python
chatbot = graph.compile(checkpointer=checkpoint)
```

Compile once when possible.

### `invoke`

Usage:

```python
result = workflow.invoke({"temperature_celsius": 25})
```

Purpose:

- Starts a graph run.
- Sends the initial state into the graph.
- Returns the final state after the graph finishes.

LLM usage also uses `invoke`:

```python
response = model.invoke(prompt)
```

There are two different operations:

- `model.invoke(...)`: ask the language model for a response.
- `workflow.invoke(...)`: run the complete LangGraph workflow.

---

## 7. LLM Nodes

Your LLM workflows use `ChatOpenAI`.

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
)
```

### `ChatOpenAI`

Purpose:

- Creates a chat model connection.
- Sends prompts or message lists to an OpenAI model.
- Returns a LangChain message object.

Common settings:

- `model` or `model_name`: model identifier.
- `temperature`: creativity level.
- `max_tokens`: response size limit.
- `api_key`: authentication value.

### Model response

```python
response = model.invoke(prompt)
answer = response.content
```

- `response` is a message object.
- `response.content` is normally the text.

### LLM node example

```python
def chat_node(state: ChatState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}
```

The node:

- Reads all messages from state.
- Sends them to the model.
- Returns the new AI message.

Real-world use:

- A support node reads the ticket history.
- It asks the model for a response.
- It adds the response to the workflow state.

---

## 8. Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()
```

Purpose:

- Loads values from a `.env` file.
- Keeps secrets such as API keys outside source code.

Typical `.env` value:

```text
OPENAI_API_KEY=your-key-here
```

Good practice:

- Do not commit `.env` to Git.
- Check that the key exists before creating the model.
- Show a useful configuration error instead of crashing.

---

## 9. Chat Messages

Your chat notebooks use:

```python
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
```

### `BaseMessage`

- Common parent type for LangChain messages.
- Useful in type annotations.

### `HumanMessage`

- Represents a user message.

```python
HumanMessage(content="Hello")
```

### `AIMessage`

- Represents a model response.
- Usually returned by a chat model.

### `SystemMessage`

- Gives the model high-level behavior instructions.

```python
SystemMessage(content="You are a helpful reviewer.")
```

### Message list

```python
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Explain LangGraph."),
]
response = model.invoke(messages)
```

Use messages when the model needs roles and conversation structure.

Use a string prompt when one simple instruction is enough.

---

## 10. Reducers

A reducer controls how a new node update combines with the old state.

Without a reducer, an update normally replaces the old value.

Example without a reducer:

```python
class State(TypedDict):
    answer: str
```

If a node returns a new `answer`, the previous answer is replaced.

### `Annotated`

```python
from typing import Annotated
import operator

class EssayEvaluation(TypedDict):
    score: Annotated[list[int], operator.add]
```

It adds extra instructions to the type.

In LangGraph, those extra instructions are often a reducer.

This means:

- the field is still a Python list
- but when multiple nodes update it, LangGraph should combine values using `operator.add`

### What does `operator.add` do?

```python
import operator
```

For lists, `operator.add` means: add items together instead of replacing the old list.

Example:

```python
class EssayEvaluation(TypedDict):
    score: Annotated[list[int], operator.add]
```

If three nodes return:

```python
{"score": [7]}
{"score": [8]}
{"score": [9]}
```

The final result becomes:

```python
[7, 8, 9]
```

Without the reducer, the later update would usually overwrite the earlier list.

So the real idea is:

- `Annotated` = "this type has special merging behavior"
- `operator.add` = "merge lists by adding items"
- `add_messages` = "merge message lists like chat history"

### `add_messages`

Import:

```python
from langgraph.graph.message import add_messages
```

Usage:

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

Purpose:

- Combines new chat messages with existing messages.
- Keeps the conversation list growing.
- Is designed for LangChain message objects.

This is the key reducer in the chat workflow.

---

## 11. Parallel Workflows

The essay workflow evaluates different parts of an essay separately.

Conceptual flow:

```text
                 -> language_feedback --
START            -> analysis_feedback  ---> final_evaluation -> END
                 -> clarity_feedback  --
```

The three evaluation nodes can work independently:

- Language quality.
- Depth of analysis.
- Clarity of thought.

The final node combines their results.

### Why use parallel branches

- Independent work can run separately.
- Large tasks become easier to organize.
- Different experts can evaluate different dimensions.
- The final node can produce one combined result.

### Fan-out and fan-in

- **Fan-out**: one point starts several branches.
- **Fan-in**: several branches join at one node.

### Important reducer rule

If multiple branches update the same state field, add a reducer.

Example:

```python
score: Annotated[list[int], operator.add]
```

For different fields, a reducer is not usually needed:

```python
{
    "language_feedback": "...",
    "analysis_feedback": "...",
    "clarity_feedback": "...",
}
```

Real-world examples:

- Run legal, security, and quality checks on one document.
- Ask several agents to research different parts of a topic.
- Validate an application using several independent rules.

---

## 12. Conditional Workflows

A conditional workflow chooses a path based on state.

### `add_conditional_edges`

Usage:

```python
graph.add_conditional_edges(
    "analyze_post",
    decide_the_node,
)
```

Meaning:

- After `analyze_post`, call `decide_the_node`.
- Use its returned value to choose the next node.

### Router function

```python
def decide_the_node(state: ModerationState):
    if state["content_flag"] == "approve":
        return "approve_post"
    elif state["content_flag"] == "review":
        return "flag_for_review"
    return "reject_post"
```

The router should:

- Read state.
- Make a decision.
- Return a valid next node name or `END`.
- Avoid doing large work itself.

### Moderation workflow

```text
format_post -> analyze_post
                         -> approve_post
                         -> flag_for_review
                         -> reject_post
```

Possible real-world uses:

- Approve, review, or reject a user post.
- Route a support ticket to billing or technical support.
- Choose a document approval path.
- Send urgent cases to a human.

### Explicit route mapping

A mapping is useful when returned values differ from node names:

```python
graph.add_conditional_edges(
    "evaluate",
    route_evaluation,
    {
        "approved": END,
        "needs_improvement": "optimize",
    },
)
```

The router returns a business value:

```python
"approved"
```

The mapping translates it into a graph destination:

```text
approved -> END
needs_improvement -> optimize
```

### `Literal`

Import:

```python
from typing import Literal
```

Usage:

```python
def decide_the_node(
    state: ModerationState,
) -> Literal["approve_post", "flag_for_review", "reject_post"]:
    ...
```

Purpose:

- Documents the allowed values.
- Helps editors and type checkers catch spelling mistakes.
- Makes the router contract clear.

`Literal` does not itself perform runtime validation.

---

## 13. Structured Output

Normal model output is free-form text.

Structured output asks the model for a predictable shape.

### Pydantic `BaseModel`

```python
from pydantic import BaseModel, Field

class EvolutionSchema(BaseModel):
    feedback: str = Field(description="Feedback for the evolution")
    score: int = Field(
        description="Score for the evolution up to 10",
        ge=0,
        le=10,
    )
```

This describes:

- A `feedback` string.
- A `score` integer.
- A score between `0` and `10`.

### `Field`

`Field` can add:

- A description for the model.
- Minimum or maximum values.
- Other Pydantic validation rules.

### `with_structured_output`

```python
structured_output = model.with_structured_output(EvolutionSchema)
result = structured_output.invoke(prompt)
```

Purpose:

- Wraps the model with a schema.
- Parses the model response into that schema.
- Makes fields easier to use in code.

Example:

```python
print(result.feedback)
print(result.score)
```

Real-world uses:

- Extract fields from invoices.
- Classify support tickets.
- Return sentiment and urgency.
- Evaluate content with a score.
- Extract a person's name, date, and category.

### `model_dump`

```python
diagnosis = result.model_dump()
```

Purpose:

- Converts a Pydantic object into a normal dictionary.

Example result:

```python
{
    "issue_type": "Bugs",
    "tone": "frustrated",
    "urgency": "high",
}
```

Use a dictionary when the next state field expects dictionary data.

Use `.content` when the next state field expects text.

---

## 14. Review Workflow

The review notebook uses structured output to classify a review.

Schemas:

```python
class SentimentSchema(BaseModel):
    sentiment: Literal["positive", "negative"]

class DiagnosisNotes(BaseModel):
    issue_type: Literal["UX", "Bugs", "Performance", "Support", "Other"]
    tone: Literal["angry", "calm", "excited", "frustrated", "neutral", "happy", "satisfied"]
    urgency: Literal["low", "medium", "high"]
```

Workflow idea:

```text
Review -> find_sentiment
                 -> positive_response -> END
                 -> run_diagnosis -> negative_response -> END
```

Meaning:

- Positive reviews receive a warm response.
- Negative reviews receive diagnosis first.
- The diagnosis helps create an empathetic support response.

Useful design lesson:

- First classify.
- Then gather extra information only when needed.
- Then create the correct response.

---

## 15. Iterative Workflows

An iterative workflow repeats a part of the graph until the result is good enough.

Your post workflow follows this idea:

```text
generate -> evaluate
              |
       approved? ---- yes ----> END
              |
              no
              v
          optimize
              |
              v
          evaluate
```

### Why use a loop

- The first model result may not be good enough.
- An evaluator can provide feedback.
- An optimizer can improve the result.
- The process can repeat automatically.

### Iteration state

```python
class PostState(TypedDict):
    topic: str
    post: str
    evaluation: Literal["approved", "needs_improvement"]
    feedback: str
    iteration: int
    max_iteration: int
    post_history: Annotated[list[str], operator.add]
    feedback_history: Annotated[list[str], operator.add]
```

Important fields:

- `topic`: what to write about.
- `post`: current version.
- `evaluation`: current quality decision.
- `feedback`: current improvement advice.
- `iteration`: current loop count.
- `max_iteration`: hard safety limit.
- `post_history`: every generated version.
- `feedback_history`: every evaluator response.

### Termination conditions

A loop must always have a safe exit.

Typical conditions:

```python
if state["evaluation"] == "approved":
    return END

if state["iteration"] >= state["max_iteration"]:
    return END
```

Why the maximum matters:

- A model may never approve its own output.
- A bad route can create an endless loop.
- API calls cost money and time.
- Production systems need predictable limits.

Real-world examples:

- Draft and review a legal document.
- Generate and test code.
- Create and grade quiz questions.
- Improve a marketing message.
- Generate a plan and validate it repeatedly.

---

## 16. Checkpointing and Conversation Memory

The checkpointed chat notebook uses:

```python
from langgraph.checkpoint.memory import MemorySaver
```

Create the checkpointer:

```python
checkpoint = MemorySaver()
```

Compile with it:

```python
chatbot = graph.compile(checkpointer=checkpoint)
```

### `MemorySaver`

Purpose:

- Saves graph state in memory.
- Allows a later call to continue from a previous state.
- Keeps message history for a conversation thread.

Important limitation:

- Data is stored only in RAM.
- History disappears when the application stops.
- It is useful for learning and small demos.
- A production system needs durable storage.

### `thread_id`

Each conversation needs an identifier:

```python
config = {
    "configurable": {
        "thread_id": user_id,
    }
}
```

Use it during invocation:

```python
result = chatbot.invoke(
    {"messages": [HumanMessage(content=user_input)]},
    config=config,
)
```

Meaning:

- The same `thread_id` continues the same conversation.
- A different `thread_id` starts a separate conversation.
- Multiple users can have separate histories.

Real-world mapping:

```text
user_id + conversation_id -> thread_id
```

Examples:

- One thread per customer support ticket.
- One thread per browser session.
- One thread per Slack channel.
- One thread per user and project.

### Basic chat versus checkpointed chat

Basic chat:

```python
chatbot = graph.compile()
```

- Runs the graph.
- Does not automatically preserve state between calls.

Checkpointed chat:

```python
chatbot = graph.compile(checkpointer=MemorySaver())
```

- Saves state.
- Requires a `thread_id` in the config.
- Can recall earlier messages in that thread.

---

## 17. Persistence and Multi-Thread Persistence

### What is persistence?

Persistence means saving the workflow state so the system can continue later.

Think of it like this:

```text
Without persistence:
    user message -> workflow runs -> state disappears

With persistence:
    user message -> workflow saves state -> next message continues naturally
```

In LangGraph, persistence is usually done with a checkpointer.

### 🚀 Part2/3_MemoryPersist notebook focus

This notebook is about one of the most important LangGraph ideas: memory between runs.

> A workflow is not just a sequence of nodes. It is also a stateful system that can remember past steps and continue later.

#### Core concepts in this notebook

- `InMemorySaver` creates a short-lived checkpointer that stores state in RAM.
- `graph.compile(checkpointer=checkpointer)` turns the graph into a stateful workflow.
- `config = {"configurable": {"thread_id": "1"}}` gives the workflow a stable conversation identity.
- `workflow.invoke(..., config=config)` resumes or continues the same thread.
- `workflow.get_state(config)` returns the latest checkpoint for that thread.
- `list(workflow.get_state_history(config))` returns the full timeline of saved states.
- Different `thread_id` values keep separate histories and avoid cross-user memory leakage.
- The notebook introduces “time travel” by showing how a graph can inspect, fork, and resume from older checkpoints.

#### Why this matters in real applications

- A chatbot should remember previous messages.
- A support workflow should keep the same customer state across retries.
- A debugging pipeline should allow replay from a prior checkpoint.
- A multi-user app must never mix one user’s state with another user’s thread.

#### Memory and thread model

```text
Same thread_id  ------------------> same conversation / same memory timeline
Different thread_id  --------------> separate conversation / separate memory
```

#### Advanced checkpoint flow

```text
thread_id = "1"
      |
      v
workflow.invoke({"topic": "programming"}, config=config)
      |
      v
InMemorySaver checkpoint
      |
      +--> latest state ------------------> workflow.get_state(config)
      |
      +--> saved history ----------------> workflow.get_state_history(config)
      |
      +--> prior checkpoint -------------> time travel + fork + resume
```

#### What makes this notebook important

This notebook introduces the difference between:

- stateless workflow: starts fresh every time
- stateful workflow: remembers the previous run
- checkpointed workflow: stores snapshots and can revisit them

A real-world support bot is a perfect example:

- User A asks about billing.
- User B asks about password reset.
- Both are using the same app.
- If they share one state, the app becomes confused.
- With `thread_id`, each conversation keeps its own checkpoint history.

#### Time travel scenario

A checkpoint is a saved moment in a workflow. It can be used to:

- inspect what state existed before a node ran
- debug the exact state that caused a bug
- retry a node with a changed value
- compare different branches without losing the original

Example idea:

```python
history = list(workflow.get_state_history(config))
checkpoint = next(
    (snapshot for snapshot in history if "joke" in snapshot.next),
    None,
)
```

This means:

- find the state right before the `joke` node executes
- copy that checkpoint
- update the topic
- resume from that exact point

That is the essence of time travel in LangGraph.

#### Advanced execution scenarios

1. Retry logic
   - A node fails due to a temporary API issue.
   - You recover from the previous checkpoint and rerun.

2. A/B prompt testing
   - One branch continues with the original topic.
   - Another uses a new topic or reformulated prompt.

3. Multi-user safety
   - Each thread stays isolated.
   - One consumer cannot see another consumer’s workflow state.

4. Conversation continuity
   - A user continues a conversation after a page refresh or restart.

5. Debugging and audit trails
   - Every saved checkpoint becomes a historical record of the workflow.

#### Golden rule

> Persist state when memory matters. Separate memory with `thread_id` when multiple users or workflows run at the same time.

### Why it matters

A workflow without persistence is usually stateless.

That means:

- the next call starts fresh
- old messages are lost
- the conversation cannot be resumed naturally
- the app cannot recover after a restart

With persistence:

- the system remembers prior messages
- a user can continue a conversation later
- a workflow can recover after a crash or restart
- multiple users can use the same app without mixing state

### Real-world example

Imagine a support bot:

- customer A asks about billing
- customer B asks about password reset
- both use the same app
- each conversation must stay separate

Without persistence, the bot cannot maintain conversation continuity. With persistence and a `thread_id`, it can.

### `MemorySaver` (in-memory persistence)

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
```

Use `MemorySaver` when:

- you are learning
- you are building a demo
- your app is short-lived

Limitations:

- stored in RAM only
- lost when the app stops
- not suitable for durable production memory

### `SqliteSaver` (database persistence)

For production systems, use a database-backed checkpointer.

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("chat_history.db")
app = graph.compile(checkpointer=checkpointer)
```

This gives you:

- restart-safe state
- durable chat history
- better recovery
- support for multi-user workflows

### Database persistence example

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chatbot_node(state: ChatState):
    last_message = state["messages"][-1]
    response = AIMessage(content=f"You just said: {last_message.content}")
    return {"messages": [response]}


graph = StateGraph(ChatState)
graph.add_node("chatbot", chatbot_node)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

checkpointer = SqliteSaver.from_conn_string("support_threads.db")
app = graph.compile(checkpointer=checkpointer)

config_1 = {"configurable": {"thread_id": "ticket-101"}}
config_2 = {"configurable": {"thread_id": "ticket-202"}}

app.invoke(
    {"messages": [HumanMessage(content="I need help with my invoice.")]},
    config=config_1,
)

app.invoke(
    {"messages": [HumanMessage(content="My password reset link expired.")]},
    config=config_2,
)
```

### What this means

- `ticket-101` stores one conversation history
- `ticket-202` stores another conversation history
- both threads use the same graph logic
- they stay completely separate because `thread_id` is different

### Multi-thread persistence

The main concept is `thread_id`.

Each thread represents one separate workflow instance.

```python
config_a = {"configurable": {"thread_id": "customer-123"}}
config_b = {"configurable": {"thread_id": "customer-456"}}
```

The same compiled graph may run for many users at the same time:

```text
thread_id = "customer-123" -> billing conversation
thread_id = "customer-456" -> order tracking conversation
thread_id = "agent-9"      -> internal support workflow
```

This is the heart of multi-thread persistence.

### Why `thread_id` is important

Without a `thread_id`, all users can accidentally share the same state.

Examples:

- one thread per customer
- one thread per support ticket
- one thread per session
- one thread per project or agent task

A good pattern is:

```python
thread_id = f"user:{user_id}:ticket:{ticket_id}"
```

### Standard rule

> Persistence rule: If a graph must remember context, persist it. If multiple users or workflows run at the same time, separate them by `thread_id`.
>
> Memorize this: persist state, isolate thread state, and never mix user conversations in the same checkpoint.

### Best practice summary

- Use `MemorySaver` for learning and small local demos.
- Use SQLite or database-backed checkpointers for real apps.
- Always assign a meaningful `thread_id`.
- Keep one graph definition and many separate thread states.

---

## 18. Chat State Pattern

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

This line combines three ideas:

- `messages`: the state field.
- `list[BaseMessage]`: a list of chat messages.
- `add_messages`: the reducer that keeps old and new messages together.

Chat node:

```python
def chat_node(state: ChatState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}
```

Graph:

```python
graph = StateGraph(ChatState)
graph.add_node("Chat_Node", chat_node)
graph.add_edge(START, "Chat_Node")
graph.add_edge("Chat_Node", END)
chatbot = graph.compile(checkpointer=checkpoint)
```

Conversation call:

```python
initial_state = {
    "messages": [HumanMessage(content="Hello")]
}

result = chatbot.invoke(initial_state, config=config)
```

Read the latest answer:

```python
answer = result["messages"][-1].content
```

---

## 18. Error Handling Lessons

LLM workflows can fail because of:

- Missing API keys.
- Invalid model names.
- Network errors.
- Rate limits.
- Invalid structured output.
- Invalid route names.
- Missing state fields.
- Endless loops.

Useful protections:

```python
try:
    result = workflow.invoke(initial_state)
except Exception as error:
    print(f"Workflow failed: {error}")
```

For applications:

- Validate required environment variables.
- Catch errors around model calls.
- Show a useful user-facing message.
- Log the detailed error separately.
- Keep retry limits finite.
- Validate structured output.
- Check that routers return registered nodes.

---

## 19. Important Corrections From The Notebooks

These are useful learning points, not just style issues.

### Conditional moderation notebook

The notebook contains both:

```python
graph.add_edge("analyze_post", END)
graph.add_conditional_edges("analyze_post", decide_the_node)
```

The direct `END` edge should be removed.

Reason:

- The router should decide whether to approve, review, or reject.
- An unconditional edge to `END` creates a competing termination path.

Correct idea:

```python
graph.add_conditional_edges("analyze_post", decide_the_node)
```

### Conditional review notebook

The sentiment node returns a Pydantic object:

```python
return {"sentiment": sentiment}
```

But the state expects the literal value.

Prefer:

```python
return {"sentiment": sentiment.sentiment}
```

Also avoid an unconditional edge that bypasses the router.

If the state says:

```python
response: str
```

return text:

```python
return {"response": response.content}
```

Do not return `response.model_dump()` unless the state field is meant to hold a dictionary.

### Iterative workflow notebook

Check these items:

- Import `BaseModel` and `Field` before using them.
- Use the same evaluation labels everywhere.
- Do not mix `"Good"` and `"approved"`.
- Initialize `iteration`.
- Initialize `max_iteration`.
- Initialize history lists.
- Increment the iteration inside the optimization path.
- Stop at approval or the maximum iteration.

### Other notes

- `celcius` should be spelled `celsius`.
- `QuestionAnswerState.temp` duplicates `answer` and is unused.
- Prompt-based rejection is not strong moderation.
- Several imported classes are unused in the chat notebooks.
- `TypedDict` describes state but does not fully validate it at runtime.

---

## 20. Notebook-by-Notebook Recall

### Notebook 1: Temperature conversion

Learned concepts:

- `StateGraph`.
- `START` and `END`.
- State with `TypedDict`.
- Sequential nodes.
- Normal Python calculation inside nodes.
- Final state returned from `invoke`.

Pattern:

```text
START -> convert -> label -> END
```

### Notebook 2: Question and answer

Learned concepts:

- Add an LLM inside a node.
- Use `ChatOpenAI`.
- Read `response.content`.
- Send one node's output to the next node.
- Refine a generated answer.

Pattern:

```text
question -> answer -> refine -> END
```

### Notebook 3: Blog creation

Learned concepts:

- Use state fields for content, outline, and final text.
- Create an outline first.
- Generate the blog from the outline.
- Build a multi-step content pipeline.

Pattern:

```text
content -> outline -> blog text
```

### Notebook 5: Essay workflow

Learned concepts:

- Pydantic schemas.
- Structured output.
- Parallel evaluation.
- Reducers.
- Combining independent scores.
- Final summary node.

Pattern:

```text
essay -> three evaluations -> final evaluation
```

### Notebook 6: Conditional moderation

Learned concepts:

- Analyze state with normal Python logic.
- Route to multiple nodes.
- Use `Literal` for route names.
- Approve, review, or reject.

Pattern:

```text
analyze -> approve OR review OR reject
```

### Notebook 7: Conditional review

Learned concepts:

- Structured classification.
- Sentiment detection.
- Conditional route.
- Extra diagnosis only for negative reviews.
- Different response styles.

Pattern:

```text
sentiment -> positive response
          -> diagnosis -> negative response
```

### Notebook 8: Iterative workflow

Learned concepts:

- Generate content.
- Evaluate content.
- Store feedback.
- Optimize content.
- Loop back to evaluation.
- Stop on approval or max iterations.

Pattern:

```text
generate -> evaluate -> optimize -> evaluate
```

### Part2 notebook 1: Basic chat

Learned concepts:

- Message-based state.
- `HumanMessage` and `AIMessage`.
- `add_messages` reducer.
- Passing message history to the model.

Limitation:

- Without a checkpointer, separate graph calls do not automatically preserve history.

### Part2 notebook 2: Checkpointed chat

Learned concepts:

- `MemorySaver`.
- `compile(checkpointer=...)`.
- `thread_id`.
- Separate user conversations.
- Persistent state during the running process.

Pattern:

```text
user id -> thread id -> checkpointed message history
```

---

## 21. Fast Recall Sheet

When building a LangGraph workflow, ask:

1. What data must travel through the workflow?
2. What is the state schema?
3. What single task belongs in each node?
4. Which nodes run in sequence?
5. Which nodes can run independently?
6. Where does a decision happen?
7. What values can the router return?
8. Which state fields need reducers?
9. Can the workflow loop forever?
10. What ends the workflow?
11. Does the model return text or structured data?
12. Does the workflow need memory?
13. What identifies one conversation from another?
14. What can fail, and how will it be handled?

The shortest design formula is:

```text
Define state
-> write nodes
-> connect edges
-> add routes or loops
-> add reducers when needed
-> compile
-> invoke
-> validate the result
```

---

## 22. One Complete Minimal Example

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    number: int
    doubled: int


def double_number(state: State):
    return {"doubled": state["number"] * 2}


graph = StateGraph(State)
graph.add_node("double_number", double_number)
graph.add_edge(START, "double_number")
graph.add_edge("double_number", END)

workflow = graph.compile()
result = workflow.invoke({"number": 5})

print(result["doubled"])
```

How to read it:

- `State` defines the shared data.
- `double_number` is the worker node.
- `START` begins the graph.
- The node updates `doubled`.
- `END` stops the graph.
- `compile` creates the runnable workflow.
- `invoke` starts one run.

---

## Final Summary

LangGraph helps turn a complicated AI task into a controlled workflow.

- State carries information.
- Nodes perform work.
- Edges control order.
- Conditional edges make decisions.
- Reducers combine updates.
- Structured output makes model responses reliable.
- Loops support improvement.
- Checkpointers preserve state.
- Thread IDs separate conversations.
- Limits and error handling make workflows safer.
