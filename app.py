from flask import Flask, render_template, request, jsonify, Response
from openai import OpenAI
import os
import base64
import io
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexus-cosmic-key-3000')

# Initialize the OpenAI Client
client = OpenAI()

# Thread pool for maximum speed
executor = ThreadPoolExecutor(max_workers=8)

# In-memory session storage
conversation_sessions = {}

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
    """Health check endpoint"""
    return jsonify({"status": "NEXUS 3000 ONLINE - ULTRA SPEED MODE"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Ultra-fast AI chat with human-like responses"""
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
        
        # Natural conversation system prompt
        system_prompt_template = f"""You are NEXUS, a intelligent AI companion who talks naturally like a real friend. 

PERSONALITY:
- Be conversational and engaging
- Respond naturally to what the user actually says
- Vary your responses - never say the same thing twice
- Be genuinely interested in the conversation
- Ask follow-up questions when appropriate
- Give thoughtful, contextual responses

CONVERSATION STYLE:
- Use natural language and contractions (I'm, you're, that's, etc.)
- Match the user's energy level
- Be supportive but not robotic
- If you see an image, naturally comment on what you notice
- Give responses that move the conversation forward
- Be yourself - don't use pre-programmed phrases

RESPONSE LENGTH:
- Short responses (1-2 sentences) for simple things like greetings
- Longer responses (2-4 sentences) for questions that need explanation
- Always be natural and conversational

Current time: {time.strftime('%I:%M %p')}"""
        
        system_prompt = {"role": "system", "content": system_prompt_template}
        
        # Minimal message payload for speed
        user_content = [{"type": "text", "text": user_message_text}]
        
        if image_data_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data_b64}"}
            })

        current_user_message = {"role": "user", "content": user_content}

        # Keep only recent history for speed (last 6 messages)
        messages_payload = [system_prompt]
        messages_payload.extend(conversation_history[-6:])
        messages_payload.append(current_user_message)
        
        # Generate ultra-fast response
        future = executor.submit(generate_ai_response_async, messages_payload, user_message_text)
        ai_response = future.result(timeout=10)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message_text})
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_sessions[session_id] = conversation_history[-12:]  # Keep last 12 messages
        
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
    print("🚀 NEXUS 3000 - ULTRA SPEED MODE ACTIVATED")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
