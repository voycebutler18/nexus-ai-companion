from flask import Flask, render_template, request, jsonify, Response
from openai import OpenAI
import os
import base64
import io
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexus-cosmic-key-3000')

# Initialize the OpenAI Client
client = OpenAI()

# Thread pool for maximum speed
executor = ThreadPoolExecutor(max_workers=8)

# Conversation storage file
CONVERSATIONS_FILE = 'conversations.json'

def load_conversations():
    """Load conversations from JSON file"""
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} conversation sessions from file")
                return data
        else:
            print("📁 No existing conversations file - starting fresh")
            return {}
    except Exception as e:
        print(f"❌ Error loading conversations: {e}")
        return {}

def save_conversations(conversations):
    """Save conversations to JSON file"""
    try:
        # Keep only last 100 messages per session to prevent file from getting huge
        cleaned_conversations = {}
        for session_id, messages in conversations.items():
            cleaned_conversations[session_id] = messages[-100:]  # Keep last 100 messages
        
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(cleaned_conversations, f, indent=2)
        print(f"💾 Saved {len(cleaned_conversations)} conversation sessions to file")
    except Exception as e:
        print(f"❌ Error saving conversations: {e}")

# Load existing conversations on startup
conversation_sessions = load_conversations()
print(f"🚀 NEXUS 3000 - LOADED {len(conversation_sessions)} EXISTING CONVERSATIONS")

# Removed all cached responses - AI will generate natural responses every time
response_cache = {}

def generate_ai_response_async(messages_payload, user_message):
    """Generate natural AI responses every time - no caching"""
    try:
        print(f"🧠 Generating natural AI response for: {user_message[:50]}...")
        
        # Always generate fresh, natural responses from AI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fastest model
            messages=messages_payload,
            max_tokens=200,  # Increased for more natural responses
            temperature=0.8,  # More natural/human-like
            stream=False,
            timeout=10  # 10-second timeout
        )
        
        ai_response = response.choices[0].message.content
        print(f"✅ Natural AI response generated: {ai_response[:100]}...")
        return ai_response
        
    except Exception as api_error:
        print(f"❌ OpenAI API error: {api_error}")
        return "Something weird happened, but I'm still here with you."

def generate_nova_speech_async(text):
    """Ultra-fast Nova speech generation"""
    try:
        print(f"🎤 Generating Nova speech for: {text[:50]}...")
        
        response = client.audio.speech.create(
            model="tts-1",  # Fastest TTS model
            voice="nova",
            input=text,
            response_format="mp3",
            speed=0.95  # Slightly slower for natural speech
        )
        
        audio_bytes = response.content
        print(f"✅ Nova speech generated ({len(audio_bytes)} bytes)")
        return audio_bytes
        
    except Exception as e:
        print(f"❌ Nova speech error: {e}")
        return None

@app.route('/')
def index():
    """Serve the main NEXUS interface"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint with conversation stats"""
    total_conversations = len(conversation_sessions)
    total_messages = sum(len(messages) for messages in conversation_sessions.values())
    return jsonify({
        "status": "NEXUS 3000 ONLINE - PERSISTENT MEMORY ACTIVE",
        "conversations": total_conversations,
        "total_messages": total_messages
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """ULTRA-FAST AI chat with aggressive speed optimization"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
            
        user_message_text = data['message']
        session_id = data.get('session_id', 'default')
        image_data_b64 = data.get('image_data')

        # Initialize session history if it doesn't exist
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
            
        conversation_history = conversation_sessions[session_id]
        
        # ULTRA-FAST system prompt - minimal for speed but includes vision
        system_prompt_template = f"""You are NEXUS, an intelligent AI with vision capabilities. 

IMPORTANT: You CAN see through the user's camera. Always mention what you observe in the image when responding.

Be natural and conversational. Keep responses 1-3 sentences unless more detail is clearly needed. 

If you see the user in the image, comment on what they're wearing, their expression, their environment, or anything notable you observe.

Time: {time.strftime('%I:%M %p')}"""
        
        system_prompt = {"role": "system", "content": system_prompt_template}
        
        # Minimal message payload for maximum speed
        user_content = [{"type": "text", "text": user_message_text}]
        
        # Only add image if it exists (saves processing time)
        if image_data_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data_b64}"}
            })

        current_user_message = {"role": "user", "content": user_content}

        # Keep only last 4 messages for speed (was 6)
        messages_payload = [system_prompt]
        messages_payload.extend(conversation_history[-4:])
        messages_payload.append(current_user_message)
        
        # Generate ultra-fast response with timeout
        start_total = time.time()
        future = executor.submit(generate_ai_response_async, messages_payload, user_message_text)
        ai_response = future.result(timeout=6)  # 6 second max
        total_time = (time.time() - start_total) * 1000
        
        print(f"🚀 TOTAL RESPONSE TIME: {total_time:.0f}ms")
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message_text})
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_sessions[session_id] = conversation_history[-8:]  # Keep last 8 messages in memory
        
        # Save to file after every conversation
        save_conversations(conversation_sessions)
        
        return jsonify({"response": ai_response, "status": "success"})
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({"error": "Something went wrong, but I'm still here!", "details": str(e)}), 500

@app.route('/api/nova-speech', methods=['POST'])
def nova_speech():
    """Ultra-fast Nova voice generation"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400
            
        text = data['text'].strip()
        
        if not text or text == " ":
            # Return empty audio for warming requests
            return Response(b"", mimetype="audio/mpeg")
        
        # Generate Nova speech at maximum speed
        future = executor.submit(generate_nova_speech_async, text)
        audio_bytes = future.result(timeout=12)
        
        if audio_bytes is None:
            return jsonify({"error": "Failed to generate speech"}), 500
        
        return Response(
            audio_bytes,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=nova_speech.mp3",
                "Content-Length": str(len(audio_bytes)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        print(f"❌ Nova speech error: {e}")
        return jsonify({"error": "Speech generation failed", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🚀 NEXUS 3000 - PERSISTENT MEMORY MODE ACTIVATED")
    print(f"💾 Conversations will be saved to: {CONVERSATIONS_FILE}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
