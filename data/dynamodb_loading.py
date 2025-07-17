import boto3
import numpy as np
import pandas as pd
import io

s3Client = boto3.client('s3')
dynamodbResource = boto3.resource('dynamodb')
dynamodbClient = boto3.client('dynamodb')

bucket_name='BUCKET_NAME'
file_name='FILE_NAME'
s3_response = s3Client.get_object(Bucket=bucket_name, Key=file_name)
# print(s3_response)
file_data = s3_response['Body'].read()
df = pd.read_excel(io.BytesIO(file_data))
# print(df.head())

s3Client.upload_file('filtered_data.xlsx','BUCKET_NAME','PATH_FILE_NAME')

#For creating the table
table = dynamodbClient.create_table(
    AttributeDefinitions=[
        {
            'AttributeName':'EMP_ID',
            'AttributeType':'N'
        },
        # {
        #     'AttributeName':'work_year',
        #     'AttributeType':'N'
        # },
        # {
        #     'AttributeName':'experience_level',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'employment_type',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'job_title',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'salary',
        #     'AttributeType':'N'
        # },
        # {
        #     'AttributeName':'salary_currency',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'salary_in_usd',
        #     'AttributeType':'N'
        # },
        # {
        #     'AttributeName':'employee_residence',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'remote_ratio',
        #     'AttributeType':'N'
        # },
        # {
        #     'AttributeName':'company_location',
        #     'AttributeType':'S'
        # },
        # {
        #     'AttributeName':'company_size',
        #     'AttributeType':'S'
        # },
    ],
    TableName='Salary',
    KeySchema=[
        {
            'AttributeName':'EMP_ID',
            'KeyType':'HASH'
        }
    ],
    BillingMode='PAY_PER_REQUEST'
)

##IF table has already been made
table = dynamodbResource.Table('Salary')

cleaned_df = pd.read_excel('filtered_data.xlsx')


def batch_write(df, batch_size=25):
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i: i+batch_size]['DynamoDB_instructions']
        for item in batch:
            
            eval(item)
batch_write(cleaned_df)

