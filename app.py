from chalice import Chalice, Response

from chalicelib.zipinfo import is_valid_zipcode, bounding_rectangle
from chalicelib.database import dynamo_query, expand

app = Chalice(app_name='homesearch')


def prepare(json):
    print('RAW REQUEST = ', json)
    json['webAvailable'] = json['availableOnly'] == 1
    del json['availableOnly']
    del json['forSaleTypes']  # FIXME
    del json['propertyType']  # FIXME

    if 'keywords' in json and is_valid_zipcode(json['keywords']):
        zip = int(json['keywords'])
        (minLongitude, maxLongitude,
         minLatitude, maxLatitude) = bounding_rectangle(zip)
        json['minLongitude'] = minLongitude
        json['maxLongitude'] = maxLongitude
        json['minLatitude'] = minLatitude
        json['maxLatitude'] = maxLatitude
        json['postalCode'] = zip
        del json['keywords']

    elif 'north' in json:
        json['minLongitude'] = json['west']
        json['maxLongitude'] = json['east']
        json['minLatitude'] = json['south']
        json['maxLatitude'] = json['north']
        del json['west']
        del json['east']
        del json['south']
        del json['north']

    # legacy fields never used
    del json['per_page']
    if 'locationType' in json:
        del json['locationType']

    print('COOKED REQUEST = ', json)
    return json


@app.route('/search-x.api', methods=['POST'], cors=True)
def search():
    query_parameters = prepare(app.current_request.json_body)
    result = dynamo_query(query_parameters)
    print("len(result) =", len(result))
    print("result[0] = ", result[0])
    expanded = expand(i['id'] for i in result)
    print("expanded[0] = ", expanded[0])
    return Response(body=result, status_code=200)
