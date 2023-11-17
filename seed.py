import boto3
from app import db, app
from models import User
from api import add_image, BUCKET_NAME
from werkzeug.datastructures import FileStorage
from io import BytesIO


def drop_tables():
    # Drop all tables
    db.drop_all()


def seed_users():
    # Create and add users to the database
    users_data = [
        {
            "username": "MysticWanderer",
            "password": "password",
            "zip_code": "10014",
            "friend_radius": 50,
            "hobbies": "spell casting, wandering",
            "interests": "dark arts, cats",
            "image": None
        },
        {
            "username": "QuantumJaguar",
            "password": "password",
            "zip_code": "94111",
            "friend_radius": 50,
            "hobbies": "teleporting, prowling",
            "interests": "wormholes",
            "image": add_image(read_image_file("./images/jag.jpg"))
        },
        {
            "username": "BillGates",
            "password": "password",
            "zip_code": "94111",
            "friend_radius": 50,
            "hobbies": "reading, public speaking",
            "interests": "software, philanthropy",
            "image": add_image(read_image_file("./images/bill.jpg"))
        },
        {
            "username": "TomHanks",
            "password": "password",
            "zip_code": "94111",
            "friend_radius": 50,
            "hobbies": "typewriter collecting, aviation, reading",
            "interests": "acting",
            "image": add_image(read_image_file("./images/tom.jpg"))
        },
        {
            "username": "NebulaPioneer",
            "password": "password",
            "zip_code": "94111",
            "friend_radius": 50,
            "hobbies": "stargazing, astronomy",
            "interests": "inventing, engineering, science",
            "image": None
        },
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
        filename = file_path.split("/")[-1]  # Extract the filename from the path
        content_type = f'image/{file_type}'
        file_storage = FileStorage(stream=file_content, filename=filename, content_type=content_type)

        return file_storage

    except FileNotFoundError:
        raise FileNotFoundError("File not found")
    except Exception as e:
        raise ValueError(str(e))


if __name__ == '__main__':
    # Run the drop tables function and then seed users
    with app.app_context():
        drop_tables()

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(BUCKET_NAME)
        bucket.objects.all().delete()

        db.create_all()
        seed_users()
