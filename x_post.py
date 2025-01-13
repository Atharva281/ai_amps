import streamlit as st
import requests
from requests_oauthlib import OAuth1
import toml
import google.generativeai as genai

# Load configuration from TOML file
config = toml.load("config.toml")

# API Credentials from TOML
BEARER_TOKEN = config["api_keys"]["token"]
GEMINI_API_KEY = config["api_keys"]["GEMINI_API_KEY"]
CONSUMER_KEY = config["api_keys"]["TWITTER_CONSUMER_KEY"]
CONSUMER_SECRET = config["api_keys"]["TWITTER_CONSUMER_SECRET"]

# Agent access tokens
agents = {
    "Agent 1": {
        "access_token": config["api_keys"]["agent_1_access_token"],
        "access_secret": config["api_keys"]["agent_1_access_token_secret"],
    },
    "Agent 2": {
        "access_token": config["api_keys"]["agent_2_access_token"],
        "access_secret": config["api_keys"]["agent_2_access_token_secret"],
    },
    "Agent 3": {
        "access_token": config["api_keys"]["agent_3_access_token"],
        "access_secret": config["api_keys"]["agent_3_access_token_secret"],
    },
    "Agent 4": {
        "access_token": config["api_keys"]["agent_4_access_token"],
        "access_secret": config["api_keys"]["agent_4_access_token_secret"],
    },
    "Agent 5": {
        "access_token": config["api_keys"]["agent_5_access_token"],
        "access_secret": config["api_keys"]["agent_5_access_token_secret"],
    },
    "Agent 6": {
        "access_token": config["api_keys"]["agent_6_access_token"],
        "access_secret": config["api_keys"]["agent_6_access_token_secret"],
    },
}

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def get_tweet_content(tweet_id):
    """Fetches the content of a tweet by ID using Twitter API."""
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "tweet.fields": "text,entities,attachments,context_annotations,referenced_tweets",
        "expansions": "author_id",
    }
    response = requests.get(f"https://api.twitter.com/2/tweets/{tweet_id}", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json().get('data', {})
        return data.get('text', "Full tweet content unavailable.")
    else:
        return "Error fetching tweet: " + response.text

def generate_gemini_response(prompt):
    """Generates a response using the Gemini API."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

def post_reply(tweet_id, reply_text, access_token, access_secret):
    """Posts a reply to a tweet using OAuth1 for authentication."""
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, access_token, access_secret)
    payload = {"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}}
    response = requests.post(url, auth=auth, json=payload)
    try:
        response.raise_for_status()
        return "Reply posted successfully!"
    except requests.HTTPError as e:
        return f"Failed to post reply: {e}"

def retweet_with_comment(tweet_id, comment_text, access_token, access_secret):
    """Retweets a tweet with a comment."""
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, access_token, access_secret)
    payload = {"text": comment_text, "quote_tweet_id": tweet_id}
    response = requests.post(url, auth=auth, json=payload)
    try:
        response.raise_for_status()
        return "Retweeted with comment successfully!"
    except requests.HTTPError as e:
        return f"Failed to retweet: {e}"

st.title("Twitter Interaction Dashboard")

# Select bot (agent) to use
selected_agent = st.selectbox("Select Bot to Use", list(agents.keys()))
selected_access_token = agents[selected_agent]["access_token"]
selected_access_secret = agents[selected_agent]["access_secret"]

# Input for Tweet URL
tweet_url = st.text_input("Enter the URL of the tweet:")

if tweet_url:
    tweet_id = tweet_url.split("/")[-1]

    # Using session state to store and retrieve tweet content
    if 'tweet_content' not in st.session_state or st.session_state.get('last_tweet_id') != tweet_id:
        st.session_state.tweet_content = get_tweet_content(tweet_id)
        st.session_state.last_tweet_id = tweet_id

    st.text_area("Tweet Content", st.session_state.tweet_content, height=150)

    # Default prompt
    default_prompt = (
        f"Generate a highly engaging and thoughtful tweet based on this content: {st.session_state.tweet_content}. "
        "The tweet should:\n"
        "Write a professionally confident and nuanced response that critically evaluates the significance of the news, adding a unique perspective without using hyperbole or generic praise. Be concise yet impactful (under 200 characters), conveying thoughtful insight that inspires discussion. Maintain a conversational, human tone—confident but not overbearing. Avoid jargon, emojis, or hashtags."
    )

    editable_prompt = st.text_area("Edit the Prompt", default_prompt, height=200)

    if st.button("Generate Response"):
        combined_prompt = editable_prompt.strip()
        st.session_state.gemini_response = generate_gemini_response(combined_prompt)
        st.session_state.generated = True

    if 'generated' in st.session_state and st.session_state.generated:
        st.text_area("Generated Response", st.session_state.gemini_response, height=150)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve and Reply"):
                reply_result = post_reply(tweet_id, st.session_state.gemini_response, selected_access_token, selected_access_secret)
                st.success(reply_result)

        with col2:
            if st.button("Approve and Repost"):
                repost_result = retweet_with_comment(tweet_id, st.session_state.gemini_response, selected_access_token, selected_access_secret)
                st.success(repost_result)
