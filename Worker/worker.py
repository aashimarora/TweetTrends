from credentials import aws_key, aws_id, aws_region, queue_name, arn
from time import sleep
import json
import boto.sqs
import boto.sns
from boto.sqs.message import Message
import ast
from alchemyapi import AlchemyAPI
import sys
reload(sys)

class SNSNotification():
    def __init__(self, aws_id, aws_key, queue_name="q1", aws_region='us-west-2'):
        try:
            #connect with sqs
            self.sqs = boto.sqs.connect_to_region(aws_region, aws_access_key_id=aws_id, aws_secret_access_key=aws_key)
            self.sqs_queue = self.sqs.get_queue(queue_name)
            self.alc = AlchemyAPI()
            self.sns = boto.sns.connect_to_region(aws_region)
            self.es = es
        except Exception as e:
            print('Could not connect')
            print(e)
        print('Connected to AWS SQS: '+ str(self.sqs))

    def readAndPublishSNSs(self):
        while True:
            #poll for new notifs every second
            rs = self.sqs_queue.get_messages() #result set
            if len(rs) > 0:
                for m in rs:
                    print('Opening notification')
                    body = m.get_body()
                    tweet= ast.literal_eval(body)
                    #do something with the tweet
                    print(tweet['content'])
                    response = self.alc.sentiment("text", tweet['content'])
                    if(response['status']=='ERROR'):
                        print('ERROR')
                        break
                    tweet['sentiment'] = response["docSentiment"]["type"]
                    print tweet
                    print("Sentiment: "+ tweet['sentiment'])
                    json_string = json.dumps(tweet)
                    #send processed tweet to SNS
                    self.sns.publish(arn, json_string, subject='Sub')

                    #delete notification when done
                    self.sqs_queue.delete_message(m)
                    print('Done')
            else:
                sleep(1)

sys.setdefaultencoding('utf-8')
sns_notif = SNSNotification(aws_id, aws_key)
sns_notif.readAndPublishSNSs()
