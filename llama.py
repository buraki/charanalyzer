from flask import Flask, redirect, request, session, url_for, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
CORS(app)

# Spotify API credentials
SPOTIFY_CLIENT_ID = "b498dc1df97847318c5d40b7083f544f"
SPOTIFY_CLIENT_SECRET = "bcb404e5b75c49af8d30b897a688d2c6"
SPOTIFY_REDIRECT_URI = "http://localhost:5000/callback"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"

# Llama API endpoint and headers
LLAMA_API_URL = "https://runtime.thyris.ai/v1/chat/completions"  # Replace with the actual endpoint
LLAMA_API_KEY = "9b34c4f0-acd7-4e85-a386-835d4ab37b0d"  # Replace with your API key

@app.route("/")
def home():
    return render_template('flask2.html')

@app.route("/login")
def login():
    scope = "user-library-read"
    auth_url = (
        f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={SPOTIFY_CLIENT_ID}"
        f"&scope={scope}&redirect_uri={SPOTIFY_REDIRECT_URI}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if code:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        }
        response = requests.post(SPOTIFY_TOKEN_URL, data=payload)
        response_data = response.json()
        session["access_token"] = response_data.get("access_token")
        return redirect(url_for("analyze_songs"))
    return "Authorization failed."

@app.route("/analyze_songs")
def analyze_songs():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/me/tracks?limit=50", headers=headers)
    if response.status_code == 200:
        tracks_data = response.json()
        track_names = [track["track"]["name"] for track in tracks_data["items"]]
        
        if not track_names:
            return jsonify({"error": "No saved songs found in your library."})

    print("Spotify song list: ", track_names) # Debugging

    prompt = f"Analyze the user's personality in a few creative sentences based on the following song names and address the user as you and don't mention the word user: {', '.join(track_names)}"

    payload = {
        "model": "Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a music-inspired personality analyzer."},
            {"role": "user", "content": prompt}
            ]
        }
    
    llama_headers = {"Authorization": f"Bearer {LLAMA_API_KEY}"}
    llama_response = requests.post(LLAMA_API_URL, json=payload, headers=llama_headers)
        
         
    if llama_response.status_code != 200:
        return jsonify({"error": "Failed to fetch analysis from Llama API."})

    print("Llama API Response:", llama_response.json())  # Debugging

    try:
        response_data = llama_response.json()
        analysis = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No analysis available.")
    
    except (KeyError, IndexError, ValueError):
        analysis = "The analysis could not be retrieved. Please try again later."

   
    return render_template('flask3.html', analysis=analysis)
        
if __name__ == "__main__":
    app.run(debug=True)
