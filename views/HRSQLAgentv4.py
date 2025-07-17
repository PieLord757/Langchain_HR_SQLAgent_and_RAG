from langchain_community.utilities import SQLDatabase
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import os
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from dotenv import load_dotenv
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_community.chat_message_histories import StreamlitChatMessageHistory


# region configurations, keys
username = "DB_USERNAME"
password = "DB_PASSWORD"
host = "AWS_AURORA_HOST"
port = 5432
database = "DB_NAME"

os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"
GEMINI_API_KEY = "YOUR_API_KEY"
# endregion

DATABASE_URI = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=GEMINI_API_KEY)

db = SQLDatabase.from_uri(DATABASE_URI)

# Pulls SQL Agent Prompt from Langchain Hub
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

#Generates an SQL query from the user's question and prior chat history
def write_query(question: str, history_str: str):

    #Might need to rewrite this query since question will appear twice (from the template), before and after the chat history 
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 15,
            "table_info": db.get_table_info(),
            "input": f"{history_str}\nCurrent question: {question}",
        }
    )
    response = llm.invoke(prompt.to_string())

    extraction_prompt = """
    Please extract the SQL query from the following text and return only the SQL query without any additional characters or formatting:

    {response}

    SQL Query:
    """
    # Format the prompt with the actual response
    prompt = extraction_prompt.format(response=response)
    # Invoke the language model with the prompt
    parsed_query = llm.invoke(prompt)
    cleaned_query = parsed_query.content.strip().strip("`")
    if cleaned_query.startswith("sql"):
        cleaned_query = cleaned_query[3:].strip()
    return cleaned_query

#Executes the SQL query
def execute_query(query: str):

    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return execute_query_tool.invoke(query)

#Generates an answer using the query results and the prior history
def generate_answer(question: str, query: str, result: str, history_str: str):
    prompt = (
        "Given the following conversation history, user question, "
        "corresponding SQL query, and SQL result, answer the user question.\n\n"
        f'Conversation so far:\n{history_str}\n\n'
        f'Question: {question}\n'
        f'SQL Query: {query}\n'
        f'SQL Result: {result}'
    )
    response = llm.invoke(prompt)
    return response.content

#Function to Wrap the chain and put it all together
def customChain(question, history):
    history_str = ""
    for msg in history:
        prefix = "User" if msg.type == "human" else "Assistant"
        history_str += f"{prefix}: {msg.content}\n"

    query=write_query(question,history_str)
    print(query)
    result=execute_query(query)
    return generate_answer(question, query, result, history_str)

chain = RunnableLambda(lambda inputs: customChain(inputs["question"], inputs["history"]))

history_for_chain = StreamlitChatMessageHistory()

chain_with_memory = RunnableWithMessageHistory(
    chain,
    lambda session_id: history_for_chain,
    input_messages_key="question",
    history_messages_key="history"
)

SESSION_ID = "user_123"

st.title("Internal HR Chatbot Tool")

if history_for_chain.messages:
    st.markdown("### Chat History (raw messages)")
    for msg in history_for_chain.messages:
        role = "User" if msg.type == "human" else "Assistant"
        st.markdown(f"**{role}:** {msg.content}")


question = st.text_area("What is your question?\n")

if question:

    response = chain_with_memory.invoke(
        {"question":question},
        config={"configurable":{"session_id":SESSION_ID}}
    )
    # customChain(question)
    st.markdown("### Answer")
    st.write(response)

if st.button("Reset Chat History"):
    history_for_chain.clear()
    st.rerun()