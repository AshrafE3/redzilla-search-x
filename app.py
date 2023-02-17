from chalice import Chalice, Response

from chalicelib.zipinfo import is_valid_zipcode, bounding_rectangle
from chalicelib.database import dynamo_query

app = Chalice(app_name='homesearch')


def prepare(json):
    del json['per_page']
    json['webAvailable'] = json['availableOnly'] == 1
    del json['availableOnly']
    del json['forSaleTypes']  # FIXME
    del json['propertyType']  # FIXME

    if is_valid_zipcode(json['keywords']):
        zip = int(json['keywords'])
        (minLongitude, maxLongitude,
         minLatitude, maxLatitude) = bounding_rectangle(zip)
        json['minLongitude'] = minLongitude
        json['maxLongitude'] = maxLongitude
        json['minLatitude'] = minLatitude
        json['maxLatitude'] = maxLatitude
        json['postalCode'] = zip
        del json['keywords']

    return json


@app.route('/search-x.api', methods=['POST'], cors=True)
def search():
    query_parameters = prepare(app.current_request.json_body)
    print(query_parameters)
    result = dynamo_query(query_parameters)
    print("len(result) =", len(result))
    return Response(body=result, status_code=200)
