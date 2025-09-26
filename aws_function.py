import boto3
import botocore.exceptions
import os
import base64

from botocore.exceptions import ClientError
import json
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

#set up amazon S3
S3_BUCKET = os.environ.get("S3_BUCKET", "your-bucket")
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID ,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY ,
    region_name="us-west-2"
)

def read_image(file_path):
    obj = s3.get_object(Bucket=S3_BUCKET, Key=file_path)
    img_bytes = obj["Body"].read()
    return img_bytes


def create_folder(folder_name, path="survey/"):
    """Create a new folder in S3 (folders in S3 are just keys ending with /)."""
    folder_key = os.path.join(path, folder_name) + "/"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=folder_key)
        print(f"Folder created: {folder_key}")
    except ClientError as e:
        print(f"Error creating folder: {e}")

def list_folders(path="survey/"):
    """List all folder names inside a given S3 path (without prefix)."""
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter="/")
        folders = [
            prefix["Prefix"].replace(path, "").strip("/")
            for prefix in response.get("CommonPrefixes", [])
        ]
        return folders
    except ClientError as e:
        print(f"Error listing folders: {e}")
        return []

def create_file(file_name, data, path="survey/"):
    """Create (or overwrite) a JSON file in the given folder path."""
    file_key = os.path.join(path, file_name)
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=json.dumps(data),
            ContentType="application/json"
        )
        print(f"File created/overwritten: {file_key}")
    except ClientError as e:
        print(f"Error creating file: {e}")

def read_file(file_name, path="survey/"):
    """Read a JSON file from the given folder path."""
    file_key = os.path.join(path, file_name)
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        content = obj["Body"].read().decode("utf-8")
        return json.loads(content)
    except ClientError as e:
        print(f"Error reading file: {e}")
        return None
    
def delete_folder(folder_name, path="survey/"):
    """Delete a folder (all objects with that prefix)."""
    folder_key = os.path.join(path, folder_name) + "/"
    st.markdown(folder_key)
    try:
        # List objects under the prefix
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=folder_key)
        if "Contents" in response:
            objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]
            s3.delete_objects(
                Bucket=S3_BUCKET,
                Delete={"Objects": objects_to_delete}
            )
            print(f"Folder deleted: {folder_key}")
            st.success("you are unregistered successfully.")
        else:
            print(f"No such folder or already empty: {folder_key}")
    except ClientError as e:
        print(f"Error deleting folder: {e}")