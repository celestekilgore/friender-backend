import boto3
from app import db, app
from models import User
from api import add_image, BUCKET_NAME
from werkzeug.datastructures import FileStorage
from io import BytesIO
import os


def drop_tables():
    # Drop all tables
    db.drop_all()


def seed_users():
    # Create and add users to the database
    users_data = [
        {
            "username": "squirrely",
            "password": "password",
            "zip_code": "04106",
            "friend_radius": 50,
            "hobbies": "looking for nuts, storing nuts",
            "interests": "nuts",
            "image": add_image(read_image_file("./images/squirrel.jpg"))
        },
        {
            "username": "LunaTheDog",
            "password": "password",
            "zip_code": "04106",
            "friend_radius": 50,
            "hobbies": "rolling, chasing, jumping",
            "interests": "treats, tennis balls",
            "image": add_image(read_image_file("./images/luna.jpg"))
        },
        {
            "username": "lettucecat",
            "password": "password",
            "zip_code": "04106",
            "friend_radius": 15,
            "hobbies": "looking for lettuce",
            "interests": "lettuce, bells, fences",
            "image": add_image(read_image_file("./images/lettuce.jpg"))
        },
        {
            "username": "Duckinthehat",
            "password": "password",
            "zip_code": "04106",
            "friend_radius": 50,
            "hobbies": "traveling, swimming",
            "interests": "fashion",
            "image": add_image(read_image_file("./images/duck.jpg"))
        },
        {
            "username": "celestekilgore",
            "password": "password",
            "zip_code": "04106",
            "friend_radius": 25,
            "hobbies": "coding, yoga, hiking",
            "interests": "engineering, animals",
            "image": None
        },
        {
            "username": "OutsideZipCode",
            "password": "password",
            "zip_code": "94111",
            "friend_radius": 25,
            "hobbies": "reading",
            "interests": "books",
            "image": None
        }
    ]

    for user_info in users_data:
        User.signup(**user_info)

    db.session.commit()


def read_image_file(file_path, allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp"]):
    try:
        # Extract the file type from the file path
        file_type = file_path.split(".")[-1].lower()

        # Check if the file type is allowed (if allowed_extensions is provided)
        if allowed_extensions and file_type not in allowed_extensions:
            raise ValueError("Invalid image format")

        # Read the file content into BytesIO
        with open(file_path, 'rb') as file:
            file_content = BytesIO(file.read())

        # Create a FileStorage instance
        # Extract the filename from the path
        filename = file_path.split("/")[-1]
        content_type = f'image/{file_type}'
        file_storage = FileStorage(
            stream=file_content, filename=filename, content_type=content_type)

        return file_storage

    except FileNotFoundError:
        raise FileNotFoundError("File not found")
    except Exception as e:
        raise ValueError(str(e))


if __name__ == '__main__':
    # Run the drop tables function and then seed users
    with app.app_context():
        drop_tables()

        s3 = boto3.resource('s3',
                            aws_access_key_id=os.environ['ACCESS_KEY'],
                            aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'])
        bucket = s3.Bucket(BUCKET_NAME)
        bucket.objects.all().delete()

        db.create_all()
        seed_users()
