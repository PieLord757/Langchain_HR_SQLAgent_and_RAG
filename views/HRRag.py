import os
import numpy as np
import pandas as pd
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

#region credentials, keys
os.environ["GOOGLE_API_KEY"] = "YOUR API KEY"
GEMINI_API_KEY = "YOUR API KEY"
#endregion

# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-exp-03-07")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", api_key=GEMINI_API_KEY)


df = pd.read_excel('named_salary.xlsx')


def create_summary(row):
    experience_map = {"EN":"Entry-level","MI":"Mid-level","SE":"Senior","EX":"Executive"}
    company_size_map = {"S":"small","M":"medium-sized","L":"large"}
    remote_map = {
        0:"fully on-site (0% remote)",
        50:"hybrid (50% remote)",
        100:"fully remote (100%)"
    }
    employment_type_map ={
        "FT":"full-time",
        "PT":"part-time",
        "CT":"contract",
        "FL":"freelance"
    }
    experience = experience_map[row["experience_level"]]
    company_size = company_size_map[row["company_size"]]
    employment_type = employment_type_map[row["employment_type"]]
    remote_ratio = remote_map[row["remote_ratio"]]

    summary = (
        f"{row['name']} is a {experience} {row['job_title']} working {employment_type} in the {row['dept']} department at a {company_size} company based in {row['company_location']}. In {row['work_year']}, they earned a salary of ${row['salary_in_usd']} USD, ({row['salary']} {row['salary_currency']}). They reside in {row['employee_residence']} and work {remote_ratio}."
    )
    return summary

docs = []
for _, row in df.iterrows():
    docs.append(
        Document(
            page_content=create_summary(row),
            metadata={
                'EMP_ID':row['EMP_ID'],
                'name':row['name'],
                'dept':row['dept'],
                'work_year':row['work_year'],
                'experience_level':row['experience_level'],
                'employment_type':row['employment_type'],
                'job_title':row['job_title'],
                'salary':row['salary'],
                'salary_currency':row['salary_currency'],
                'salary_in_usd':row['salary_in_usd'],
                'employee_residence':row['employee_residence'],
                'remote_ratio':row['remote_ratio'],
                'company_location':row['company_location'],
                'company_size':row['company_size']
            }
        )
    )



db = Chroma.from_documents(docs, embeddings)
retriever = db.as_retriever(search_kwargs={"k":10})

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system","""Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history. Keep all proper name, numbers, or specific references intact. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ]    
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system","""You are a helpful assistant for helping with HR-related queries. Use the provided context to respond. If the answer isn't clear or not present in the context, acknowledge that you don't know, especially when there are names, numbers, or references that are not present in the context. <Information_from_the_knowledge_base>{context}</Information_from_the_knowledge_base>"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human","{input}")
    ]
)

history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

rag_chain = (
    {"context":history_aware_retriever,"input":(lambda x: x["input"]),"chat_history":(lambda x: x["chat_history"])} | qa_prompt | llm | StrOutputParser()
)

history_for_chain = StreamlitChatMessageHistory()

chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    lambda session_id: history_for_chain,
    input_messages_key="input",
    history_messages_key="chat_history"
)

st.title("Internal HR Chatbot Tool")

question = st.text_input("What is your question?\n")

if question:
    
    response = chain_with_history.invoke({"input":question},{"configurable":{"session_id":"abc123"}})

    st.write(response)