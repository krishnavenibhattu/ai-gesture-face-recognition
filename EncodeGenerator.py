import cv2
import face_recognition
import pickle
import os
import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'host': '127.0.0.1',  # Update with your database host
    'user': 'root',  # Update with your MySQL username
    'password': 'Vaibhav@2504',  # Update with your MySQL password
    'database': 'newdata',  # Update with your database name
}

# Importing student images
folderPath = 'Images'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentIds = []

# Opens the files
for path in pathList:
    img = cv2.imread(os.path.join(folderPath, path))
    if img is not None:
        imgList.append(img)
        studentIds.append(os.path.splitext(path)[0])
    else:
        print(f"Image {path} could not be loaded.")

print(studentIds)


# Function to find encodings
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Try to find face encodings
        faceLoc = face_recognition.face_locations(img_rgb)

        if len(faceLoc) == 0:
            print("No faces found in this image.")
            continue

        encode = face_recognition.face_encodings(img_rgb, faceLoc)

        # If encodings were found, append the first encoding
        if len(encode) > 0:
            encodeList.append(encode[0])
        else:
            print("No face encoding found for this image.")

    return encodeList


print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)

if len(encodeListKnown) == 0:
    print("No valid encodings found. Exiting...")
else:
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("Encoding Complete")

    # Save encodings to a file
    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("File Saved")

    # Save encodings to MySQL database
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to MySQL database")
            cursor = connection.cursor()

            # Ensure table exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Encodings (
                id VARCHAR(100) PRIMARY KEY,
                encoding LONGBLOB
            )
            """)

            # Insert encodings into the database
            for student_id, encoding in zip(studentIds, encodeListKnown):
                cursor.execute(
                    """
                    INSERT INTO Encodings (id, encoding)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        encoding = VALUES(encoding)
                    """,
                    (student_id, pickle.dumps(encoding))
                )

            # Commit changes
            connection.commit()
            print("Encodings inserted into the database successfully")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")
