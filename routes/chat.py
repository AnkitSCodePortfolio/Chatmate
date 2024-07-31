from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app import db
from models.chat_history import ChatHistory
from models.openai_client import client_creator
from io import BytesIO
import base64
from PIL import Image
import pyttsx3
import uuid
import os

bp = Blueprint('chat', __name__, url_prefix='/chat')


@bp.route('/', methods=['GET'])
@login_required
def chat():
    return render_template('index.html')

@bp.route('/api/send_message', methods = ['POST'])
@login_required
def send_message():
    data = request.get_json()
    message = request.get('message')
    model_params = data.get('model_params')
    audio_response = data.get('audio_response')

    client = client_creator()
    response_message = ""
    response = client.chat.completions.create(
        model= model_params["model"] if "model" in model_params else "gpt-4o",
        messages = [{"role": "user", "content": message}],
        temperature=model_params["temperature"] if "temperature" in model_params else 0.3,
        max_tokens=4096,
        stream=True,
    )

    for chunk in response:
        try:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    response_message += content
                yield response_message
        except IndexError as e:
            print(f"Debug Exception - {str(e)}")
            print(f"Debug: Chunk - {chunk}")

    chat_history = ChatHistory(user_id = current_user.id, message = message, response = response_message)
    db.session.add(chat_history)
    db.session.commit()

    response_data = {
        'response': response_message,
        'audio': None  # Audio need to be added
    }

    if audio_response:
        engine = pyttsx3.init()
        unique_audio_file = f'response_audio_{uuid.uuid4()}.mp3'
        engine.save_to_file(response_message, unique_audio_file)
        engine.runAndWait()
        with open(unique_audio_file,'rb') as audio_file:
            audio_bytes = audio_file.read()
        response_data['audio'] = base64.b64encode(audio_bytes).decode('utf-8')
        os.remove(unique_audio_file)

    return jsonify(response_data)

@bp.route('/api/add_image', methods = ['POST'])
@login_required
def add_image():
    #image upload and processing to be done
    if 'image' not in request.files:
        return jsonify({'status': 'No image uploaded'}), 400
    
    image_file = request.files['image']
    if image_file:
        raw_img = Image.open(image_file)
        buffered = BytesIO()
        raw_img.save(buffered, format = raw_img.format)
        img_byte = buffered.getvalue()
        img_base64 = base64.b64encode(img_byte).decode('utf-8')

        chat_history = ChatHistory(user_id = current_user.id, message="", response = "", image = img_base64)
        db.session.add(chat_history)
        db.session.commit()
        return jsonify({'status': 'Image received'})

    return jsonify({'status': 'Image processing failed'}), 500


