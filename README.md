# Twitter Thread to Carousel

## Installation

1. Create new environment:
```
conda create --name thread
```

2. Activate new environment:
```
conda activate thread
```

3. Install python and poetry
```
conda install python poetry
```

4. Let poetry install all dependencies
```
poetry install
```

## Set your variables

Create an `.env` file and copy-paste:
```
BEARER_TOKEN=1234qwer
CONSUMER_KEY=1234qwer
CONSUMER_SECRET=1234qwer
ACCESS_TOKEN=1234qwer
ACCESS_TOKEN_SECRET=1234qwer
```

with `1234qwer` being replaced by your own keys and tokens extracted from [Twitter Developer](https://developer.twitter.com/en/portal/projects-and-apps).

* `BEARER_TOKEN`, `ACCESS_TOKEN` and `ACCESS_TOKEN_SECRET` can be found under the Authentication Tokens section of the Keys and Tokens tab of your app
* `CONSUMER_KEY` and `CONSUMER_SECRET` can be found under the Consumer Keys section of the Keys and Tokens tab of your app

## Run the script

```
python convert2carousel.py https://twitter.com/didier_lopes/status/1570731358204600323
```

where the tweet to be input needs to be the first of the thread, e.g. https://twitter.com/didier_lopes/status/1570731358204600323

