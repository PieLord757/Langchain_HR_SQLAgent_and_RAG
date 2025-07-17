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
import boto3
import requests

# region SNS setup, IP setup for database usage
sns_client = boto3.client("sns")
SNS_TOPIC_ARN = "YOUR_SNS_TOPIC_ARN"

#Adds user IP to the inbounding rules for VPC
ip = requests.get("https://api.ipify.org").text
cidr_ip = f"{ip}/32"
ec2_client = boto3.client('ec2')
security_group_id = "sg-005dec6c71ad3d791"

try:
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [{'CidrIp': cidr_ip, 'Description': 'Temporary access for demo'}]
            }
        ]
    )
    print(f"Successfully added {cidr_ip} to SG {security_group_id}")
except ec2_client.exceptions.ClientError as e:
    if 'InvalidPermission.Duplicate' in str(e):
        print(f"{cidr_ip} is already whitelisted.")
    else:
        raise


# endregion



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
# llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=GEMINI_API_KEY)

db = SQLDatabase.from_uri(DATABASE_URI)

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

# Function to send the notification
def send_sns_notification(subject, message):
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except Exception as e:
        print(f"Failed to send an SNS notification: {str(e)}" )


#Generate SQL query from the user's question and prior chat history
def write_query(question: str, history_str: str):

    #Might need to rewrite this query since question will appear twice, before and after the chat history 
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

#Generates the answer using the results of the query and the context
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

#Function to put it all together and also activate SNS if "salary" is detected within query or question
def customChain(question, history):
    history_str = ""
    for msg in history:
        prefix = "User" if msg.type == "human" else "Assistant"
        history_str += f"{prefix}: {msg.content}\n"

    query=write_query(question,history_str)
    print(query)
    result=execute_query(query)

    answer = generate_answer(question, query, result, history_str)
    if "salary" in question.lower() or "salary" in query.lower():
        send_sns_notification(
            subject="Salary-related query detected",
            message=f"User asked: {question}\n\nQuery:\n{query}\n\nAnswer:\n{answer}"
        )

    return answer

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


#Configuration for displaying in streamlit UI and invoking llm

for msg in history_for_chain.messages:
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

if prompt := st.chat_input("Ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    response = chain_with_memory.invoke(
        {"question":prompt},
        config={"configurable":{"session_id":SESSION_ID}}
    )

    with st.chat_message("assistant"):
        st.markdown(response)

if st.button("Reset Chat"):
    history_for_chain.clear()
    st.rerun()