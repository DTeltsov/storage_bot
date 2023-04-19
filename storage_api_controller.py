from google.cloud import storage

from consts import CREDS

client = storage.Client.from_service_account_json(json_credentials_path=CREDS)
bucket_name = 'test_lab_bucket'


def get_files_list():
    blobs = client.list_blobs(bucket_name)
    return [blob.name for blob in blobs]


def upload_file(file_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)


def download_file(file_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.download_to_filename(file_name)
