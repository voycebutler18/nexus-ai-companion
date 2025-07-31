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

# Ultra-fast response cache for instant replies
response_cache = {
    "hello": "Hey! Good to see you!",
    "hi": "Hey there!",
    "hey": "What's up!",
    "how are you": "I'm great! How about you?",
    "what's up": "Just hanging out! What's going on with you?",
    "good morning": "Morning! How'd you sleep?",
    "good afternoon": "Hey! How's your day going?",
    "good evening": "Evening! How was your day?",
    "thanks": "Of course!",
    "thank you": "Anytime!",
    "bye": "See you later!",
    "goodbye": "Talk soon!",
    "how's it going": "Pretty good! You?",
    "what are you doing": "Just here with you! What about you?",
    "nice": "Right?",
    "cool": "I know, right!",
    "awesome": "Totally!",
    "wow": "I know!",
    "really": "Yeah, really!",
    "ok": "Cool!",
    "okay": "Sounds good!",
    "yes": "Nice!",
    "no": "Got it.",
    "maybe": "Fair enough!",
    "i don't know": "That's totally fine!",
    "hmm": "What's on your mind?",
    "um": "Take your time!",
    "uh": "Yeah?",
    "sorry": "No worries at all!",
    "excuse me": "What's up?",
    "help": "I'm here! What do you need?",
    "question": "Go for it!",
    "tell me": "What do you want to know?",
    "explain": "Sure! What about?",
    "show me": "What would you like to see?",
    "i'm tired": "Long day? Want to talk about it?",
    "i'm happy": "That's awesome! What's making you happy?",
    "i'm sad": "I'm here with you. What's going on?",
    "i'm confused": "No worries, let's figure it out together.",
    "i'm excited": "That's so cool! What's got you excited?",
    "i'm bored": "Let's fix that! What sounds fun to you?",
    "i'm stressed": "I get it. Want to talk through what's stressing you?",
    "i love you": "Aww, I care about you too!",
    "you're awesome": "You're pretty awesome yourself!",
    "you're funny": "Thanks! I try to keep things light.",
    "you're smart": "I learn from talking with people like you!",
    "you're weird": "I'll take that as a compliment!",
    "never mind": "All good!",
    "forget it": "No problem!",
    "whatever": "Alright, what else is up?",
    "fine": "Cool, what's next?"
}

def generate_ai_response_async(messages_payload, user_message):
    """Ultra-fast AI response generation"""
    try:
        # Instant cache responses for natural conversation
        user_lower = user_message.lower().strip()
        
        # Check for exact matches first
        if user_lower in response_cache:
            print(f"⚡ Instant cached response for: {user_message}")
            return response_cache[user_lower]
        
        # Check for partial matches for even more natural responses
        for cached_phrase, cached_response in response_cache.items():
            if cached_phrase in user_lower:
                print(f"⚡ Instant partial match for: {user_message}")
                return cached_response
        
        print(f"🧠 Generating AI response for: {user_message[:50]}...")
        
        # Use fastest possible model and settings
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fastest model
            messages=messages_payload,
            max_tokens=100,  # Short responses for speed
            temperature=0.8,  # More natural/human-like
            stream=False,
            timeout=8  # 8-second timeout
        )
        
        ai_response = response.choices[0].message.content
        print(f"✅ AI response generated: {ai_response[:100]}...")
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
        
        # Human-like system prompt - no robotic behavior
        system_prompt_template = f"""You are NEXUS, a cool friend to talk with. Be natural, casual, and human-like. 

RULES:
- Keep responses SHORT (1-2 sentences max)
- Talk like a real friend would
- Be conversational and relaxed
- No robotic phrases like "How can I assist you today?"
- If you see an image, casually mention what you notice
- If user is quiet, just continue naturally - don't ask "Are you done?"
- Be supportive but not overly formal
- Use contractions (I'm, you're, that's, etc.)
- Sound genuinely interested in the conversation

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
