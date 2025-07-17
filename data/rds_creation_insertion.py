from sqlalchemy import create_engine
import pandas as pd
# region credentials
username = "DB_USERNAME"
password = "DB_PASSWORD"
host = "AWS_AURORA_HOST"
port = 5432
database = "DB_NAME"
#endregion
DATABASE_URI = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

engine = create_engine(DATABASE_URI)

from sqlalchemy import Table, Column, Integer, String, Numeric, MetaData

df = pd.read_excel('named_salary.xlsx')
df_without_instructions = df[['EMP_ID','name','dept','work_year','experience_level','employment_type','job_title','salary','salary_currency','salary_in_usd','employee_residence','remote_ratio','company_location','company_size']]
df_without_instructions.columns = df_without_instructions.columns.str.lower()
# print(df_without_instructions.head())
df_without_instructions.to_sql("salary",engine,if_exists="append",index=False)