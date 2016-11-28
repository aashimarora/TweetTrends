from django.shortcuts import render
from django.http import HttpResponse
from requests_aws4auth import AWS4Auth
from credentials import consumer_key, consumer_secret,access_token,access_token_secret, queue_name, aws_region
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch, RequestsHttpConnection
from credentials import aws_key, aws_id


awsauth = AWS4Auth(aws_id, aws_key,'us-west-2','es')
host = "search-jask-tweetmap-hhk4izgywmbpwob2zah4fcdiry.us-west-2.es.amazonaws.com"
es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        use_ssl=True,
        http_auth=awsauth,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
print(es.info())

def get_sqs_queue(sqs_name):
    #connect with SQS
    try:
        sqs = boto.sqs.connect_to_region(aws_region, aws_access_key_id=consumer_key, aws_secret_access_key=consumer_secret)
    except Exception as e:
        print('Could not connect to SQS')
        print(e)
    print('Connected to AWS SQS: '+ str(sqs))
    return sqs,sqs.get_queue(sqs_name)

def index(request):
    return render(request, "polls/maps.html")

@csrf_exempt
def sns_process_tweet(request):
    type = request.META.get('HTTP_X_AMZ_SNS_MESSAGE_TYPE')
    print request
    print type
    if type == 'SubscriptionConfirmation':
        received_json_data = json.loads(request.body)
        url = received_json_data['SubscribeURL']
        response = requests.get(url)
        print url
        return HttpResponse(response)
    elif type == 'Notification':
        received_json_data = json.loads(request.body)
        id = received_json_data['MessageId']
        message = received_json_data['Message']
        #add to Elasticsearch
	try:
            es.index(index='cloud_index', doc_type='twitter', body=message)
        except Exception as e:
           print('Elasticserch indexing failed')
           print(e)

        print message
        return HttpResponse(message)
    else :
        return HttpResponse("SNS Running")

def map(request):
    if request.method == 'POST':
        data = request.POST.get('query')
        res = es.search(size=5000, index="cloud_index", doc_type="twitter", body={
            "query":{
                "match" : { "content": data}
                }
            })
        print("Hits total" + str(res['hits']['total']))
        print("Hits Hits" + str(len(res['hits']['hits'])))
        coordinate_array = []
        coordinates = res['hits']
        individual_coordinate_sets = coordinates['hits']
        list_of_dicts = [dict() for num in range (len(individual_coordinate_sets))]
        for idx,element in enumerate(list_of_dicts):
            source_value = individual_coordinate_sets[idx]['_source']
            temp_coordinates = source_value['coordinates']
            tweet_info = source_value['user'] + ": " + source_value['content']
            sm = str(source_value['sentiment'])
            list_of_dicts[idx] = dict(lng=temp_coordinates[0], sentiment=sm,lat = temp_coordinates[1])
        return render(request, "polls/maps.html", {'plot':list_of_dicts})
    else:
        return render(request, "polls/maps.html", {'plot':[0]})
"""
    if request.method == 'POST':
        print("Reached here")
        with open('data.txt','r') as f :
            for line in f:
                tweet = eval(line)
                if tweet['coordinates']:
                    print(tweet['coordinates'])
                    coordinates.append(tweet['coordinates']['coordinates'])
    print(coordinates)
"""
