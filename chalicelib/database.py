import boto3
import os


# Create a DynamoDB client
dynamodb = boto3.client('dynamodb')

# Define the S3 bucket and DynamoDB table
table_name = os.environ['DYNAMO_TABLE']
index_name = 'latitude-longitude-index'


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

        query = {
            'TableName': table_name,
            'IndexName': index_name,
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
        response = dynamodb.query(**query)
        print("response n = ", len(response['Items']))

        result += response['Items']

    return result
