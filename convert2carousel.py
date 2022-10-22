import requests
import pandas as pd
from datetime import datetime,timedelta
import tweepy
import io
import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from matplotlib import pyplot as plt
import numpy as np
import textwrap
import re
import emoji
from PyPDF2 import PdfMerger
import os
from dotenv import load_dotenv

if __name__ == '__main__':
    THREAD = sys.argv[1]

    if "https://twitter.com/" not in THREAD or "/status/" not in THREAD:
        print("Please provide a valid Twitter thread URL, e.g.: https://twitter.com/didier_lopes/status/1570731358204600323")
        sys.exit(2)

    # Style of carousel
    HEADER_HEIGHT = 0
    RADIUS = 20
    WHITE_LINE_WIDTH = 3
    OUTSIDE_CANVAS_WIDTH = 650
    OUTSIDE_CANVAS_HEIGHT = 450 
    BACKGROUND_WIDTH_SLACK = 150
    BACKGROUND_HEIGHT_SLACK = 150

    # Load environment variables
    load_dotenv()

    bearer_token = os.getenv('BEARER_TOKEN') or "REPLACE-ME"
    consumer_key = os.getenv('CONSUMER_KEY') or "REPLACE-ME"
    consumer_secret = os.getenv('CONSUMER_SECRET') or "REPLACE-ME"
    access_token = os.getenv('ACCESS_TOKEN') or "REPLACE-ME"
    access_token_secret = os.getenv('ACCESS_TOKEN_SECRET') or "REPLACE-ME"

    # You can authenticate as your app with just your bearer token
    # client = tweepy.Client(bearer_token=bearer_token)

    # You can provide the consumer key and secret with the access token and access token secret to authenticate as a user
    client = tweepy.Client(
        consumer_key=consumer_key, consumer_secret=consumer_secret,
        access_token=access_token, access_token_secret=access_token_secret,
        bearer_token=bearer_token,
    )

    # Get the thread ID and username
    THREAD_ID = THREAD.split("/")[-1]
    USERNAME = THREAD.split("/")[-3]

    # Get the first tweet
    response = client.get_tweet(THREAD_ID, tweet_fields=["created_at", "author_id"])

    # Get the date of the start of the thread
    threadstart = datetime.strptime(response.data.data["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")

    # Get all tweets
    tweets = client.get_users_tweets(
        id=response.data.data["author_id"], 
        tweet_fields=["created_at,conversation_id,referenced_tweets,attachments,entities"],
        expansions=["author_id,referenced_tweets.id,referenced_tweets.id.author_id,attachments.media_keys"],
        media_fields=["duration_ms,height,media_key,preview_image_url,type,url,width,public_metrics"],
        start_time=f'{(threadstart - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
        end_time=f'{(threadstart + timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
        max_results=100)

    # Iterate through all tweets to create thread
    thread = list()
    for tweet in tweets.data:
        images = list()
        if "entities" in tweet.data:
            if "urls" in tweet.data["entities"]:
                for entity in tweet.data["entities"]["urls"]:
                    # Check if the tweet has an image
                    if "media_key" in entity:
                        for media in tweets.includes["media"]:
                            if media.media_key == entity["media_key"]:
                                images.append(
                                    {
                                        "url": media.url,
                                        "height": media.height,
                                        "width": media.width,
                                    }
                                )
        thread.append(
            {
                "text": tweet.text,
                "images": images,
            }
        )
    thread = thread[::-1]

    # Make sure no folder is overriden
    FOLDER_NAME = THREAD_ID
    repeated = 1
    while os.path.exists(FOLDER_NAME):
        FOLDER_NAME = f"{THREAD_ID} ({repeated})"
        repeated += 1

    # Create new folder to save thread
    os.mkdir(FOLDER_NAME)

    # Create each png image for the carousel
    for idx, tweet in enumerate(thread):
        
        # Start creating image
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png")
        shot = Image.open(img_buf)

        # Get the background colors
        background = Image.open("background.png")
        background = background.resize((shot.width + BACKGROUND_WIDTH_SLACK, shot.height + BACKGROUND_HEIGHT_SLACK))

        # Add a white border around
        x = int((background.width - OUTSIDE_CANVAS_WIDTH) / 2)
        y = int((background.height - OUTSIDE_CANVAS_HEIGHT) / 2)
        white_shape = (
            (x, y),
            (x + OUTSIDE_CANVAS_WIDTH, y + OUTSIDE_CANVAS_HEIGHT),
        )
        img = ImageDraw.Draw(background)
        
        img.rounded_rectangle(
            white_shape,
            fill="#4b5564",
            #outline="white",
            width=WHITE_LINE_WIDTH,
            radius=RADIUS,
        )

        # Get Twitter profile picture
        url_profile = client.get_user(username=USERNAME, user_auth=False, user_fields=["profile_image_url"]).data.profile_image_url.replace("_normal", "")
        profile = Image.open(io.BytesIO(requests.get(url_profile).content))

        # Make it in circular shape
        size = (100, 100)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        cropped_profile = ImageOps.fit(profile, mask.size, centering=(0.5, 0.5))
        cropped_profile.putalpha(mask)
        background.paste(cropped_profile, (x + WHITE_LINE_WIDTH + 25, y + WHITE_LINE_WIDTH + 25), mask)

        x_user = x + WHITE_LINE_WIDTH + 25 + size[0] + 25
        y_user = y + WHITE_LINE_WIDTH + 40

        # Process username
        font = ImageFont.truetype(r'Ch1rp/chirp_heavy.otf', 30)
        username = client.get_user(username="didier_lopes", user_auth=False, user_fields=["profile_image_url"]).data.name
        # TODO: Improve to accept emojis
        username = emoji.demojize(username).split(":")[0].strip()
        img.text((x_user, y_user), username, (255,255,255), font=font)

        # Process tag name
        font = ImageFont.truetype(r'Ch1rp/chirp_medium.otf', 20)
        img.text((x_user, y_user + 40), "@" + USERNAME, (255,255,255), font=font)

        # Add tweet icon
        tweet_icon = Image.open("twitter-64.png")
        background.paste(tweet_icon, (710, 560), tweet_icon)

        # Add Tweet text
        font = ImageFont.truetype(r'Ch1rp/chirp_regular.otf', 24)
        # remove last reference to link
        if 'https://t.co/' in tweet["text"].split(" ")[-1] and len(tweet["text"].split(" ")[-1]) == 23 and ": https://t.co" not in tweet["text"].split(" ")[-1]:
            text = " ".join(tweet["text"].split(" ")[:-1])
        else:
            text = tweet["text"]
        astr = emoji.demojize(text)
        if idx == 0:
            astr = astr.split(":")[0].strip() # removes thread symbol
        text_w_spacing = list()
        for text in astr.split("\n"):
            if text:      
                text_w_spacing += textwrap.wrap(text, width=50)
            else:
                text_w_spacing += ["\n"]
        img.text((x + WHITE_LINE_WIDTH + 30, y_user + 110), "\n".join(text_w_spacing), (255,255,255), font=font)

        # Add Tweet image
        if len(tweet["images"]):
            # only 1 image on the tweet
            if len(tweet["images"]) == 1:
                img = Image.open(io.BytesIO(requests.get(tweet["images"][0]["url"]).content))
                img = img.resize((270, 160))
                background.paste(img, (x + WHITE_LINE_WIDTH + 190, y_user + 230))

            # only show up to 2 images
            else:
                img = Image.open(io.BytesIO(requests.get(tweet["images"][0]["url"]).content))
                img = img.resize((270, 140))
                background.paste(img, (x + WHITE_LINE_WIDTH + 30, y_user + 250))

                img = Image.open(io.BytesIO(requests.get(tweet["images"][1]["url"]).content))
                img = img.resize((270, 140))
                background.paste(img, (x + WHITE_LINE_WIDTH + 350, y_user + 250))

        background.save(os.path.join(FOLDER_NAME, f"tweet_{idx}.png"))

    # Convert images png to pdf
    merger = PdfMerger()
    for filename in os.listdir(FOLDER_NAME):
        if ".png" in filename:
            Image.open(os.path.join(FOLDER_NAME, filename)).convert('RGB').save(os.path.join(FOLDER_NAME, filename).replace("png", "pdf"))

    # Merge individual PDFs into a single one
    merger = PdfMerger()
    for i in range(len(thread)):
        merger.append(os.path.join(FOLDER_NAME, f"tweet_{i}.pdf"))
    merger.write(os.path.join(FOLDER_NAME, "carousel.pdf"))
    merger.close()

    print(f"Successfully saved carousel in {os.path.join(FOLDER_NAME, 'carousel.pdf')}")