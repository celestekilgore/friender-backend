import boto3
import os
import uuid
from pyzipcode import ZipCodeDatabase

s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ['ACCESS_KEY'],
    aws_secret_access_key=os.environ['SECRET_ACCESS_KEY']
)

zcdb = ZipCodeDatabase()


def add_image(image):
    """Takes FileStorage image, uploads to S3 bucket, and returns public url."""

    file_type, *_ = image.content_type.split("/")

    if file_type != "image":
        return {"errors": ["Invalid image"]}

    BUCKET_NAME = os.environ['BUCKET_NAME']
    filename = str(uuid.uuid4())

    s3.upload_fileobj(
        image,
        BUCKET_NAME,
        filename,
        ExtraArgs={'ACL': 'public-read', 'ContentType':  image.content_type})

    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"


def get_zip_codes_around_radius(zip_code, radius):
    """Takes zip code and radius and returns list of zip codes within radius."""

    zip_codes = zcdb.get_zipcodes_around_radius(zip_code, radius)

    return [z.zip for z in zip_codes]
