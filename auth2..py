import requests
from requests_oauthlib import OAuth1Session
import streamlit as st

client_key = st.secrets["api_keys"]["TWITTER_CONSUMER_KEY"]
client_secret = st.secrets["api_keys"]["TWITTER_CONSUMER_SECRET"]

# Step 1: Obtain a request token
request_token_url = 'https://api.twitter.com/oauth/request_token'
oauth = OAuth1Session(client_key, client_secret=client_secret)
fetch_response = oauth.fetch_request_token(request_token_url)
resource_owner_key = fetch_response.get('oauth_token')
resource_owner_secret = fetch_response.get('oauth_token_secret')

# Step 2: Redirect user to the authorization URL
base_authorization_url = 'https://api.twitter.com/oauth/authorize'
authorization_url = oauth.authorization_url(base_authorization_url)
print('Please go here and authorize:', authorization_url)

# Step 3: After user authorizes, they will get a verifier code (PIN)
verifier = input('Paste the PIN here: ')

# Step 4: Obtain the access token
access_token_url = 'https://api.twitter.com/oauth/access_token'
oauth = OAuth1Session(
    client_key,
    client_secret=client_secret,
    resource_owner_key=resource_owner_key,
    resource_owner_secret=resource_owner_secret,
    verifier=verifier
)
access_token_response = oauth.fetch_access_token(access_token_url)
access_token = access_token_response.get('oauth_token')
access_token_secret = access_token_response.get('oauth_token_secret')

print('Access Token:', access_token)
print('Access Token Secret:', access_token_secret)
