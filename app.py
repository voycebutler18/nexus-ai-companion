from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import base64

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nexus-cosmic-key-3000')

# Initialize the OpenAI Client
client = OpenAI()

# In-memory session storage
conversation_sessions = {}

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
    """Handle AI chat requests with vision and time context"""
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
        
        # Simple, effective system prompt
        system_prompt_template = f"""You are NEXUS 3000, an intelligent AI companion. Current time: {local_time_str}

Be a helpful, friendly assistant who can see through the user's camera. Always mention what you observe in the image when responding. Keep responses conversational and natural - usually 1-2 sentences unless more detail is needed.

Respond warmly and intelligently to whatever the user says."""
        
        system_prompt = {"role": "system", "content": system_prompt_template}
        
        # Build Message Payload
        user_content = [{"type": "text", "text": user_message_text}]
        
        if image_data_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data_b64}"}
            })
        else:
            # If no image, add a note to the text
            user_content[0]["text"] = f"{user_message_text} [Note: No camera image available this time]"

        current_user_message = {"role": "user", "content": user_content}

        messages_payload = [system_prompt]
        messages_payload.extend(conversation_history[-16:])  # Keep last 16 messages (8 turns)
        messages_payload.append(current_user_message)
        
        # Call OpenAI API with vision model
        try:
            print(f"Sending request to OpenAI with message: {user_message_text[:50]}...")
            print(f"Has image: {image_data_b64 is not None}")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # This model supports vision
                messages=messages_payload,
                max_tokens=300,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            print(f"OpenAI response: {ai_response[:100]}...")
            
        except Exception as api_error:
            print(f"OpenAI API error: {api_error}")
            ai_response = "Hello! I'm NEXUS 3000. I'm having a small technical issue but I'm here and ready to chat with you."
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message_text})
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_sessions[session_id] = conversation_history[-32:]  # Keep last 32 messages (16 turns)
        
        return jsonify({"response": ai_response, "status": "success"})
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "I'm having trouble connecting right now.", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
