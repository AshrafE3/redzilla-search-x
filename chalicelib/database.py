from typing import List
import boto3
from boto3.dynamodb.types import TypeDeserializer
import os
import gzip
import json


dynamodb = boto3.client('dynamodb')
table_name = os.environ['DYNAMO_TABLE']
deser = TypeDeserializer()


def deserialize(dynamodb_json):
    return {k: deser.deserialize(v) for k, v in dynamodb_json.items()}


def latitude_box_values(min_lat, max_lat):
    min_lat_int = int(float(min_lat) * 10)
    max_lat_int = int(float(max_lat) * 10)
    return range(min_lat_int, max_lat_int+1)


def dynamo_query(query_parameters):

    latitude_boxes = [str(latitude) for latitude in latitude_box_values(
        query_parameters.get("minLatitude"),
        query_parameters.get("maxLatitude"))]

    result = []
    for latitude_box in latitude_boxes:

        if query_parameters['webAvailable']:
            index_name = 'latitude-longitude-webavailable-index'
        else:
            index_name = 'latitude-longitude-index'

        query = {
            'TableName': table_name,
            'IndexName': index_name,
            'ReturnConsumedCapacity': 'TOTAL',
            'KeyConditionExpression': 'latitude_box = :latitude_box AND longitude BETWEEN :minLongitude AND :maxLongitude',  # noqa
            'FilterExpression': '',
            'ExpressionAttributeValues': {
                ':latitude_box': {"N": latitude_box},
                ':minLongitude': {
                    "N": str(query_parameters.get("minLongitude"))
                },
                ':maxLongitude': {
                    "N": str(query_parameters.get("maxLongitude"))
                }
            }
        }
        for key in query_parameters:
            if key in ["minLongitude", "maxLongitude"]:
                continue
            if key[:3] == "min":
                field = key.replace("min", "")
                field = field[0].lower() + field[1:]
                query['FilterExpression'] += f"{field} >= :{field}_min AND "
                query['ExpressionAttributeValues'][f":{field}_min"] = {
                    "N": str(query_parameters[key])
                }
            elif key[:3] == "max":
                field = key.replace("max", "")
                field = field[0].lower() + field[1:]
                query['FilterExpression'] += f"{field} <= :{field}_max AND "
                query['ExpressionAttributeValues'][f":{field}_max"] = {
                    "N": str(query_parameters[key])
                }
            else:
                field = key
                if type(query_parameters[key]) == list:
                    if len(query_parameters[key]) > 0:
                        values = ','.join([f':{field}_{idx}' for idx in range(
                            len(query_parameters[key]))]
                        )
                        query['FilterExpression'] += f"{field} IN ({values}) AND "  # noqa
                        for idx, value in enumerate(query_parameters[key]):
                            query['ExpressionAttributeValues'][
                                f":{field}_{idx}"
                            ] = {"S": value}
                else:
                    query['FilterExpression'] += f"{field} = :{field} AND "
                    value = query_parameters[key]
                    if isinstance(value, str):
                        value_type = "S"
                    elif isinstance(value, bool):
                        value_type = "BOOL"
                    elif isinstance(value, (int, float)):
                        value_type = "N"
                        value = str(value)
                    else:
                        raise ValueError(f"Unsupported data type for {key}: {type(value)}")  # noqa
                    query['ExpressionAttributeValues'][f":{field}"] = {
                        value_type: value
                    }

        # removes trailing 'AND '
        query['FilterExpression'] = query['FilterExpression'][:-4]
        print("query = ", query)

        last_key = []
        consumed_capacity = 0
        while last_key is not None:
            response = dynamodb.query(
                **query, ExclusiveStartKey=last_key
            ) if last_key else dynamodb.query(**query)
            result += map(deserialize, response['Items'])
            consumed_capacity += response['ConsumedCapacity']['CapacityUnits']
            last_key = response.get('LastEvaluatedKey')

        print("CONSUMED_CAPACITY = ", consumed_capacity)

    return result

# we currently don't have standard_data_gz in the dynamo database

# def expand(id: List[str]) -> List[dict]:
#     id = list(id)

#     chunked_ids = [id[i:i+100] for i in range(0, len(id), 100)]
#     items = []
#     for chunk in chunked_ids:
#         response = dynamodb.batch_get_item(
#             RequestItems={
#                 table_name: {
#                     'Keys': [{'id': {'S': i}} for i in chunk]
#                 }
#             }
#         )
#         items.extend(response['Responses'][table_name])

#     items = [{
#         **{k: v for k, v in item.items() if k != 'standard_data_gz'},
#         'standard_data': json.loads(gzip.decompress(
#             item['standard_data_gz'].value
#         ).decode('utf-8'))
#      } for item in map(deserialize, items)
#     ]

#     return items
