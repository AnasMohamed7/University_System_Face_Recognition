from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import os
import base64
import numpy as np
from deepface import DeepFace
import json
import uuid
import re

app = Flask(__name__)
CORS(app)  # This allows requests from your web page

# Folder where faces are stored
FACES_FOLDER = "faces"
# File to store user data
USERS_FILE = "users.json"

# Make sure faces folder exists
os.makedirs(FACES_FOLDER, exist_ok=True)

# Initialize users data
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)


def load_users():
    """Load users data from file."""
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    """Save users data to file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


def has_all_same_digits(national_id):
    """Check if all digits in the national ID are the same."""
    return bool(re.match(r'^(\d)\1+$', national_id))


@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        # Get the image data and national ID from the request
        data = request.json
        image_data = data['image'].split(',')[1]  # Remove the "data:image/png;base64," part
        national_id = data['nationalId']

        # Check if all digits are the same
        if has_all_same_digits(national_id):
            return jsonify({
                'success': False,
                'message': 'الرقم القومي غير صالح. لا يمكن أن تكون جميع الأرقام متطابقة.'
            })

        # Load users data
        users = load_users()

        # Check if the national ID exists
        if national_id not in users:
            return jsonify({
                'success': False,
                'message': 'رقم قومي غير مسجل'
            })

        # Convert base64 to image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Save temporary image
        temp_capture_path = "temp_capture.jpg"
        cv2.imwrite(temp_capture_path, image)

        # Get the user's face images
        user_data = users[national_id]
        user_name = user_data['fullName']

        # Check if face is recognized
        is_recognized = False

        for face_file in user_data['faceFiles']:
            face_path = os.path.join(FACES_FOLDER, face_file)

            try:
                result = DeepFace.verify(
                    img1_path=temp_capture_path,
                    img2_path=face_path,
                    enforce_detection=False
                )

                if result["verified"]:
                    is_recognized = True
                    break
            except Exception as e:
                print(f"⚠️ Error verifying {face_path}: {e}")

        # Clean up temporary file
        if os.path.exists(temp_capture_path):
            os.remove(temp_capture_path)

        if is_recognized:
            return jsonify({
                'success': True,
                'message': f'تم التعرف على الوجه: {user_name}',
                'user': user_name
            })
        else:
            return jsonify({
                'success': False,
                'message': 'لم يتم التعرف على الوجه. تم رفض الدخول.'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })


@app.route('/check-id', methods=['POST'])
def check_id():
    try:
        data = request.json
        national_id = data['nationalId']

        # Check if all digits are the same
        if has_all_same_digits(national_id):
            return jsonify({
                'exists': False,
                'invalid': True,
                'message': 'الرقم القومي غير صالح. لا يمكن أن تكون جميع الأرقام متطابقة.'
            })

        # Load users data
        users = load_users()

        # Check if national ID already exists
        if national_id in users:
            return jsonify({
                'exists': True,
                'message': 'هذا الرقم القومي مسجل بالفعل'
            })
        else:
            return jsonify({
                'exists': False
            })

    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'خطأ: {str(e)}'
        })


@app.route('/register', methods=['POST'])
def register():
    try:
        # Get the data from the request
        data = request.json
        national_id = data['nationalId']
        full_name = data['fullName']
        images = data['images']

        # Check if all digits are the same
        if has_all_same_digits(national_id):
            return jsonify({
                'success': False,
                'message': 'الرقم القومي غير صالح. لا يمكن أن تكون جميع الأرقام متطابقة.'
            })

        # Load users data
        users = load_users()

        # Check if national ID already exists
        if national_id in users:
            return jsonify({
                'success': False,
                'message': 'هذا الرقم القومي مسجل بالفعل'
            })

        # Save face images
        face_files = []

        for idx, image_data in enumerate(images):
            # Remove the "data:image/png;base64," part
            image_data = image_data.split(',')[1]

            # Convert base64 to image
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Generate a unique filename
            filename = f"{national_id}_{idx + 1}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(FACES_FOLDER, filename)

            # Save the image
            cv2.imwrite(filepath, image)
            face_files.append(filename)

        # Add user to database
        users[national_id] = {
            'fullName': full_name,
            'faceFiles': face_files
        }

        # Save users data
        save_users(users)

        return jsonify({
            'success': True,
            'message': f'تم تسجيل المستخدم {full_name} بنجاح'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })


if __name__ == '__main__':
    app.run(debug=True, port=5000)