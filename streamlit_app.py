import streamlit as st
from PIL import Image

# Page setup

Home_page = st.Page(
    page="views/about_me.py",
    title="Home Page",
    icon=":material/account_circle:",
    default=True
)

HR_Rag_Page = st.Page(
    page="views/HRRag.py",
    title="HR RAG",
    icon=":material/search:"
)

HRSQLAgentv4Page = st.Page(
    page="views/HRSQLAgentv4.py",
    title="HR SQL Agent (v4)",
    icon=":material/search:"
)

HRSQLAgentv5Page = st.Page(
    page="views/HRSQLAgentv5.py",
    title="HR SQL Agent (v5)",
    icon=":material/search:"
)

pg = st.navigation(
    {
        "Info":[Home_page],
        "Projects":[HRSQLAgentv4Page,HRSQLAgentv5Page,HR_Rag_Page]
    }
    )


st.sidebar.text("Made by Shiva Pochampally")
pg.run()