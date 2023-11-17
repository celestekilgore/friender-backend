import boto3
import os
import uuid
from pyzipcode import ZipCodeDatabase
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.environ['BUCKET_NAME']

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


def is_valid_zip_code(zip_code):
    """Takes zip code and returns boolean."""

    return bool(zcdb.get(zip_code))


def form_errors_to_list(form_errors):
    """Takes WTForm dictionary errors and returns list of errors."""

    errors = []

    for field, field_errors in form_errors.items():
        for error in field_errors:
            errors.append(f"{field}: {error}")

    return errors
