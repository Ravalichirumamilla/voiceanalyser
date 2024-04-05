import boto3
import json
s3 = boto3.client('s3')

resfile = s3.get_object(Bucket="voice.analayser.app",Key="outputs/3162.json")
file_content = resfile['Body'].read().decode('utf-8')

print(file_content)