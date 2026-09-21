import boto3
import streamlit as st


def get_aws_client(
    service_name: str,
    region_name: str = "us-east-1",
):
    """
    Create an AWS client using credentials stored
    in Streamlit secrets.
    """
    return boto3.client(
        service_name,
        region_name=region_name,
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    )