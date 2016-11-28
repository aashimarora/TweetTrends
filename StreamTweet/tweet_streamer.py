import tweepy
import json
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from credentials import consumer_key, consumer_secret,access_token,access_token_secret,aws_id, aws_key,queue_name, aws_region
import boto.sqs
from boto.sqs.message import Message

host = "search-jask-tweetmap-hhk4izgywmbpwob2zah4fcdiry.us-west-2.es.amazonaws.com"
awsauth = AWS4Auth(aws_id, aws_key, aws_region,'es')
es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        use_ssl=True,
        http_auth=awsauth,
        verify_certs=True,
        connection_class=RequestsHttpConnection
        )
print(es.info())

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):
    def on_status(self, status):
        json_data = status._json
        user_info = json_data['user']
        if json_data['coordinates']:
            data = {
                    'content': json_data['text'].lower().encode('ascii','ignore').decode('ascii'),
                    'user_id': user_info['id'],
                    'user': user_info['name'],
                    'coordinates': json_data['coordinates']['coordinates'],
                    'time': json_data['timestamp_ms'],
                    'handle': json_data['user']['screen_name']
                    }

            print(data)
            #Add to elastic search
            #try:
                #es.index(index='cloud_tweet', doc_type='twitter', body=data)
            #except:
                #print('ElasticSearch indexing failed')

            #add notif of tweet to sqs
            sqs.send_message(sqs_queue, data)
            print('Data sent to SQS')

        return True

def on_error(self, status):
    print status

def get_sqs_queue(sqs_name):
    #connect with SQS
    try:
          sqs = boto.sqs.connect_to_region(aws_region, aws_access_key_id=aws_id, aws_secret_access_key=aws_key)
    except Exception as e:
        print('Could not connect to SQS')
        print(e)

    print('Connected to AWS SQS: '+ str(sqs))
    return sqs,sqs.get_queue(sqs_name)


if __name__ == '__main__':
    l = StdOutListener()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = tweepy.Stream(auth, l)
    #filter for these terms in tweet text
    terms = [
            'jobs','programming' , 'elections', 'Trump', 'usa', 'wanderlust'
            ,'movies','sports','music','finance','technology'
            ,'fashion','science','travel','health','cricket'
            ,'india', 'love', 'shit','bjp', 'aap', 'india'
            ,'epl', 'football','goal', '1-0' ]
    sqs,sqs_queue = get_sqs_queue(queue_name)
    #stream
    #stream.filter(None,terms)
    while True:
        try:
            stream.filter(track=terms)
        except Exception as e:
            print e
            pass
