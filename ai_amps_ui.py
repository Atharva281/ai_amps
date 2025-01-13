import streamlit as st
import requests
import google.generativeai as genai
from requests_oauthlib import OAuth1
from dotenv import load_dotenv
import os
import time
import toml
# Load environment variables
load_dotenv()

# Constants
TWITTER_CONSUMER_KEY = st.secrets["api_keys"]["TWITTER_CONSUMER_KEY"]
TWITTER_CONSUMER_SECRET = st.secrets["api_keys"]["TWITTER_CONSUMER_SECRET"]
X_BEARER_TOKEN = st.secrets["api_keys"]["token"]
GEMINI_KEY = st.secrets["api_keys"]["GEMINI_API_KEY"]
PERPLEXITY_BEARER_TOKEN = st.secrets["api_keys"]['PERPLEXITY_BEARER_TOKEN']
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Gemini st.secretsuration
genai.configure(api_key=GEMINI_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")


# Functions
def generate_gemini_response(tweet_text):
    prompt = f"Generate a response for this tweet: '{tweet_text}'only one response strictly , no options"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating Gemini response: {e}")
        return "I couldn't generate a response."
def generate_gemini_response_for_post(content):
    """
    Generates a response using Gemini API.
    """
    prompt = f"Generate a highly engaging and thoughtful tweet based on this content: {content}. The tweet should: 1. Express a well-formed opinion highlighting the significance. 2. Be concise and impactful. 3. Avoid hashtags or emojis. Deliver only the tweet content in less than 200 characters."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating Gemini response: {e}")
        return "Could not generate a response."

def generate_perplexity_response(user_input):
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be concise and precise."},
            {"role": "user", "content": user_input},
        ],
        "max_tokens": 200,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("choices", [])[0].get("message", {}).get("content", "No response")
        else:
            st.error(f"Perplexity API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to Perplexity API: {e}")
        return None


def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", {}).get("id")
    elif response.status_code == 429:
        reset_time = int(response.headers.get("x-rate-limit-reset", time.time() + 60))
        sleep_time = reset_time - time.time()
        st.warning(f"Rate limit hit. Please wait for {int(sleep_time)} seconds and try again.")
        time.sleep(max(sleep_time, 1))
        return None
    else:
        st.error(f"Error fetching user ID: {response.status_code}")
        return None


def fetch_tweets(user_id, max_results=5):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {"max_results": max_results}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    elif response.status_code == 429:
        reset_time = int(response.headers.get("x-rate-limit-reset", time.time() + 60))
        sleep_time = reset_time - time.time()
        st.warning(f"Rate limit hit. Please wait for {int(sleep_time)} seconds and try again.")
        time.sleep(max(sleep_time, 1))
        return []
    else:
        st.error(f"Error fetching tweets: {response.status_code}")
        return []


def post_tweet(agent_number, tweet_text):
    """
    Posts a tweet using Twitter API.
    """
    access_token = st.secrets["api_keys"][f"agent_{agent_number}_access_token"]
    access_token_secret = st.secrets["api_keys"][f"agent_{agent_number}_access_token_secret"]
    auth = OAuth1(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, access_token, access_token_secret)
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": tweet_text}

    try:
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error posting tweet for agent_{agent_number}: {e}")
        return None


def reply_to_tweet(agent_number, tweet_id, reply_text):
    access_token = st.secrets["api_keys"][f"agent_{agent_number}_access_token"]
    access_token_secret = st.secrets["api_keys"][f"agent_{agent_number}_access_token_secret"]
    auth = OAuth1(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, access_token, access_token_secret)
    url = "https://api.twitter.com/2/tweets"
    try:
        payload = {
            "text": reply_text,
            "reply": {
                "in_reply_to_tweet_id": tweet_id
            }
        }
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()
        print(f"Successfully replied to tweet with ID: {tweet_id}")
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def retweet_with_comment(agent_number, tweet_id, comment_text):
    access_token = st.secrets["api_keys"][f"agent_{agent_number}_access_token"]
    access_token_secret = st.secrets["api_keys"][f"agent_{agent_number}_access_token_secret"]
    auth = OAuth1(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, access_token, access_token_secret)
    url = "https://api.twitter.com/2/tweets"
    payload = {
        "text": comment_text,
        "quote_tweet_id": tweet_id
    }
    try:
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()
        print(f"Successfully retweeted with comment for tweet ID: {tweet_id}")
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None
def fetch_news():
    """
    Fetches six distinct news points from the Perplexity API.
    """
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be concise and precise."},
            {
                "role": "user",
                "content": "Provide six distinct and detailed updates from the following categories. Each update should focus on the latest, unique, and impactful news within its respective category. Ensure the updates are concise, precise, and easy to understand.1. General trending news in USA.2. **DeFi News**: Provide the latest trends, partnerships, or innovations in the DeFi space.3. **Trending Twitter News**: Highlight a major topic currently trending on Twitter.Not hashtags, but actual topics and a context and the discusiion4. **Crypto News**: Share impactful updates about cryptocurrency projects or ecosystem developments.5. **Political News in the USA**: Provide news going on in U>S politics and everyday discussions.6. **LLMs News**: Highlight the latest advancements in large language models. Ensure each category has only one unique news point.",
            },
        ],
        "max_tokens": 700,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, json=payload, headers={
            "Authorization": f"Bearer {PERPLEXITY_BEARER_TOKEN}",
            "Content-Type": "application/json",
        })
        response.raise_for_status()
        news_points = response.json()["choices"][0]["message"]["content"].split("\n\n")
        return news_points
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []
# Streamlit UI
st.title("Twitter Interaction Manager")

# Select interaction type
interaction_type = st.selectbox("Select Interaction Type", ["Reply", "Retweet", "Post Own"])

if interaction_type in ["Reply", "Retweet"]:
    username = st.text_input("Enter the username of the person you want to interact with")
    if username:
        user_id = get_user_id(username)
        if user_id:
            tweets = fetch_tweets(user_id)
            if tweets:
                # Select a tweet
                tweet_options = {tweet["id"]: tweet["text"] for tweet in tweets}
                selected_tweet_id = st.selectbox(
                    "Select a tweet to interact with",
                    options=list(tweet_options.keys()),
                    format_func=lambda x: tweet_options[x],
                )

                # Store the selected tweet in session state
                st.session_state["selected_tweet_text"] = tweet_options[selected_tweet_id]
                st.write(f"Selected Tweet: {st.session_state['selected_tweet_text']}")

                # Choose bots and generate response
                bots_selected = st.multiselect("Select bots for this interaction", options=list(range(1, 7)))
                if st.button("Generate Responses"):
                    st.session_state["responses"] = {}
                    for bot in bots_selected:
                        gemini_response = generate_gemini_response(st.session_state["selected_tweet_text"])
                        st.session_state["responses"][bot] = gemini_response
                        st.write(f"Bot {bot} generated: {gemini_response}")

                # Display responses with post button
                if "responses" in st.session_state:
                    for bot, response in st.session_state["responses"].items():
                        if interaction_type == "Reply":
                            if st.button(f"Reply with Bot {bot}", key=f"reply_{bot}"):
                                reply_response = reply_to_tweet(bot, selected_tweet_id, response)
                                if reply_response:
                                    st.success(f"Bot {bot} successfully replied to the tweet.")
                        elif interaction_type == "Retweet":
                            if st.button(f"Retweet with Comment using Bot {bot}", key=f"retweet_{bot}"):
                                retweet_response = retweet_with_comment(bot, selected_tweet_id, response)
                                if retweet_response:
                                    st.success(f"Bot {bot} successfully retweeted with comment.")

else:  # "Post Own" case
    use_news_fetching = st.checkbox("Fetch Latest News for Posts", value=True)

    if use_news_fetching:
        if st.button("Fetch News"):
            news_points = fetch_news()
            if news_points:
                st.session_state["news_points"] = news_points
                st.success("News fetched successfully!")
                for i, news in enumerate(news_points, start=1):
                    st.write(f"News Point {i}: {news}")
            else:
                st.error("Failed to fetch news.")

        if "news_points" in st.session_state and st.button("Generate and Post News Tweets"):
            for i, news_point in enumerate(st.session_state["news_points"], start=1):
                if i > 6:  # Limit to 6 agents
                    break

                st.write(f"Processing Agent {i}: {news_point}")
                tweet_text = generate_gemini_response(news_point)
                st.write(f"Generated Tweet: {tweet_text}")
                response = post_tweet(i, tweet_text)
                if response:
                    st.success(f"Tweet successfully posted for Agent {i}")
                else:
                    st.error(f"Failed to post tweet for Agent {i}")

    else:  # Manual post input
        user_input = st.text_area("Enter your topic or content for the post")
        if st.button("Generate Post"):
            gemini_response = generate_gemini_response_for_post(user_input)
            st.session_state["generated_post"] = gemini_response
            st.write(f"Generated via Gemini: {gemini_response}")

            if st.button("Post Generated Content", key="post_gemini"):
                post_response = post_tweet(1, st.session_state["generated_post"])
                if post_response:
                    st.success("Post successfully made.")
