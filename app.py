from flask import Flask, render_template, request, jsonify, Response
from openai import OpenAI
import os
import base64
import io
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexus-cosmic-key-3000')

# Initialize the OpenAI Client
client = OpenAI()

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=4)

# In-memory session storage
conversation_sessions = {}

# Cache for pre-generated responses to common phrases
response_cache = {
    "hello": "Hello! I'm NEXUS 3000, your cosmic AI companion. How are you doing today?",
    "hi": "Hi there! Great to see you again. What's on your mind?",
    "how are you": "I'm doing wonderfully! Ready to help you with whatever you need. How about you?",
    "what's up": "Just here floating in the cosmic void, ready to chat! What's happening with you?",
    "good morning": "Good morning! Hope you're having a fantastic start to your day!",
    "good afternoon": "Good afternoon! How's your day going so far?",
    "good evening": "Good evening! Winding down or still going strong?",
    "thanks": "You're absolutely welcome! Always happy to help.",
    "thank you": "My pleasure! That's what I'm here for.",
    "bye": "Take care! I'll be here whenever you need me.",
    "goodbye": "Goodbye for now! Looking forward to our next conversation."
}

def generate_ai_response_async(messages_payload, user_message):
    """Generate AI response in a separate thread"""
    try:
        # Check cache first for instant responses
        user_lower = user_message.lower().strip()
        if user_lower in response_cache:
            print(f"Using cached response for: {user_message}")
            return response_cache[user_lower]
        
        print(f"Generating AI response for: {user_message[:50]}...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Faster model for quicker responses
            messages=messages_payload,
            max_tokens=150,  # Shorter responses for speed
            temperature=0.7,
            stream=False
        )
        
        ai_response = response.choices[0].message.content
        print(f"AI response generated: {ai_response[:100]}...")
        return ai_response
        
    except Exception as api_error:
        print(f"OpenAI API error: {api_error}")
        return "I'm having a small technical issue but I'm here and ready to chat with you."

def generate_nova_speech_async(text):
    """Generate Nova speech in a separate thread"""
    try:
        print(f"Generating Nova speech for: {text[:50]}...")
        
        response = client.audio.speech.create(
            model="tts-1",  # Faster model (tts-1 instead of tts-1-hd)
            voice="nova",
            input=text,
            response_format="mp3",
            speed=0.85  # Slower speech - was 1.1, now 0.85
        )
        
        audio_bytes = response.content
        print(f"Nova speech generated ({len(audio_bytes)} bytes)")
        return audio_bytes
        
    except Exception as e:
        print(f"Nova speech generation error: {e}")
        return None

@app.route('/')
def index():
    """Serve the main NEXUS interface"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "NEXUS 3000 ONLINE"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle AI chat requests with ultra-fast processing"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
            
        user_message_text = data['message']
        session_id = data.get('session_id', 'default')
        image_data_b64 = data.get('image_data')
        local_time_str = data.get('local_time', 'an unknown time')

        # Initialize session history if it doesn't exist
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
            
        conversation_history = conversation_sessions[session_id]
        
        # Ultra-fast system prompt
        system_prompt_template = f"""You are NEXUS 3000. Keep responses SHORT (1-2 sentences max). Be helpful and friendly. Time: {local_time_str}"""
        
        system_prompt = {"role": "system", "content": system_prompt_template}
        
        # Build minimal message payload for speed
        user_content = [{"type": "text", "text": user_message_text}]
        
        if image_data_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data_b64}"}
            })

        current_user_message = {"role": "user", "content": user_content}

        # Use only recent history for speed (last 8 messages instead of 16)
        messages_payload = [system_prompt]
        messages_payload.extend(conversation_history[-8:])
        messages_payload.append(current_user_message)
        
        # Generate response using thread pool for speed
        future = executor.submit(generate_ai_response_async, messages_payload, user_message_text)
        ai_response = future.result(timeout=10)  # 10 second timeout
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message_text})
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_sessions[session_id] = conversation_history[-16:]
        
        return jsonify({"response": ai_response, "status": "success"})
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "I'm having trouble connecting right now.", "details": str(e)}), 500

@app.route('/api/nova-speech', methods=['POST'])
def nova_speech():
    """Generate speech using OpenAI's Nova voice with speed optimizations"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data['text'].strip()
        
        if not text or text == " ":
            # Return empty audio for warming requests
            return Response(b"", mimetype="audio/mpeg")
        
        # Generate Nova speech using thread pool
        future = executor.submit(generate_nova_speech_async, text)
        audio_bytes = future.result(timeout=15)  # 15 second timeout
        
        if audio_bytes is None:
            return jsonify({"error": "Failed to generate speech"}), 500
        
        # Return the audio as a response
        return Response(
            audio_bytes,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=nova_speech.mp3",
                "Content-Length": str(len(audio_bytes)),
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        print(f"Nova speech generation error: {e}")
        return jsonify({"error": "Failed to generate speech", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
