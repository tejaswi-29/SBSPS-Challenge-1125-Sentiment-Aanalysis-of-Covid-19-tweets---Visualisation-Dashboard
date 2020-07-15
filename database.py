from __future__ import print_function
import tweepy
import pandas as pd
from tweepy import Stream
from tweepy import OAuthHandler
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
from unidecode import unidecode
import re
import json
import time
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
authenticator = IAMAuthenticator('your apikey')
tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    authenticator=authenticator)
tone_analyzer.set_service_url('your url')

WORDS = ['#covid19india','#indiafightscorona','#MumbaiCovid','#Covid19Hyd','#Delhifightscorona']

atoken = "your access token"
asecret = "your access token secret"
ckey = "your consumer key"
csecret = "your consumer secret key"

client = Cloudant("USERNAME", "PASSWORD", "URL")
client.connect()
print("connected to db!")
# Database
# database_name = "tweets1"
my_database = client['tweets2']
my_document = my_database['Livefeed']
if my_document.exists():
    print('SUCCESS!!')
#create a dataframe
df = pd.DataFrame()
#counting number of tweets so that avg of the sentiment can be found.
tweetdetails = {}
class StreamListener(tweepy.StreamListener):    
    #This is a class provided by tweepy to access the Twitter Streaming API. 

    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("You are now connected to the streaming API.")
 
    def on_error(self, status_code):
        # On error - if an error occurs, display the error / status code
        print('An Error has occured: ' + repr(status_code))
        return False
    def on_data(self, data):
        #This is the meat of the script...it connects to your mongoDB and stores the tweet
        try:
            datajson = json.loads(data)
            # print(datajson)
            tweet = unidecode(datajson['text'])
            tweet = tweet.lower()
            tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','URL',tweet)
            tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
            print("done preprocessing")
            print(tweet)
            tone_analysis = tone_analyzer.tone({'text': tweet},content_type='application/json').get_result()
            tone=json.dumps(tone_analysis, indent=2)    
            jsonParse = json.loads(tone)
            vs = analyzer.polarity_scores(tweet)
            sentiment = vs['compound']
            emotions_score = {}
            if "document_tone" in jsonParse.keys():
                if jsonParse["document_tone"]["tones"]!=[]:
                    length = len(jsonParse["document_tone"]["tones"])
                    k = jsonParse["document_tone"]['tones']
                    for i in range(length):
                        n = k[i]['tone_name']
                        my_document[n] += 1 #updating the score count of the emotion
                        my_document.save()
                        print("document updated!")
                        if n in emotions_score:
                            emotions_score[n] = emotions_score[n]+k[0]['score']
                            print("done adding the score")
                        else:
                            emotions_score.update({n:k[0]['score']})    
                            print("adding a new emotion")
                else:
                    emotions_score={"tone":"None"}    
                    my_document['Neutral']+=1
                    my_document.save()
            else:
                emotions_score={"tone":"None"}
                my_document['Neutral']+=1
                my_document.save()
            global df 
            global tweetdetails 
            my_document['Tweet_Count'] +=1
            tweetdetails.update({my_document['Tweet_Count']:[datajson['created_at'],datajson['text'],sentiment,emotions_score]})
            # df =  df.append({'Created_at':datajson['created_at'],'tweet':datajson['text'],'Emotions':emotions_score},ignore_index = True)
            my_document['Sentiment_score_avg']=(my_document['Sentiment_score_avg']+sentiment)/my_document['Tweet_Count']
            my_document['Tweets'] = tweetdetails
            my_document.save()
            print("Updated document!")
        except KeyError as e:
            print("helloo its a key error!!")
            print(e)
        return(True)

while True:
    try:
        auth = OAuthHandler(ckey,csecret)
        auth.set_access_token(atoken,asecret)
        #Set up the listener. The 'wait_on_rate_limit=True' is needed to help with Twitter API rate limiting.
        listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True)) 
        streamer = tweepy.Stream(auth=auth, listener=listener)
        print("Tracking: " + str(WORDS))
        streamer.filter(track=WORDS,languages=["en"])
    except Exception as e:
        print("helloo! im the error 400")
        print(str(e))
        time.sleep(5)







