import streamlit as st


from forms.contact import contact_form

st.title("GenAI & AWS Use-Case")

@st.dialog("Contact Me")
def show_contact_form():
    contact_form()



# Hero Section

col1, col2 = st.columns(2, gap="small",vertical_alignment="center")
with col1:
    # st.image("./assets/profile_image.png",width=239)
    st.image("https://miro.medium.com/v2/resize:fit:1358/0*ckdXC34JDf6benSt",width=239)
with col2:
    st.title("Shiva Pochampally", anchor=False)
    st.write("Student at Virginia Tech")
    
    if st.button("✉️ Contact Me"):
        show_contact_form()

st.write("\n")
st.subheader("Tools Used Within Projects:", anchor=False)
st.write(
    """
    - GenAI: LangChain, LLM (Gemini) API, Ollama
    - Programming: Python (NumPy, Pandas, Boto3), SQL
    - Databases: AWS Aurora (Postgres compatible), Dynamodb (NoSQL)
    - AWS: S3, Lambda, RDS (Aurora), DynamoDB, SNS, Lambda, IAM
    - Other Tools: Jupyter Notebook
    """
)