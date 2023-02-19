from chalice import Chalice, Response
from chalicelib.zipinfo import is_valid_zipcode, bounding_rectangle
from chalicelib.database import dynamo_query

app = Chalice(app_name='homesearch')


def prepare(json):
    json = {**json}
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


def photoUri(item):
    if 'photoUriPath' in item:
        return '/main' + item['photoUriPath'] + '/360/360'
    else:
        return None


@app.route('/search-x.api', methods=['POST'], cors=True)
def search():
    query_parameters = prepare(app.current_request.json_body)
    result = dynamo_query(query_parameters)
    print("len(result) =", len(result))

    response = [{
        'id': item['id'],
        'photoUri': photoUri(item),
        'latitude': float(item['latitude']),
        'longitude': float(item['longitude']),
        'displayPrice': int(float(item['listPrice'])),
        'status': item['status'],
        'bedrooms': int(item['bedroomsTotal']),
        'fullBathrooms': (
            int(item['bathroomsTotalInteger']) -
            int(item.get('bathroomsHalf', '0'))
        ),
        'halfBathrooms': int(item.get('bathroomsHalf', '0')),
        'squareFeet': int(item['livingArea']),
        'address': item['unitAddress'].split(' #')[0],
        'unit': item[
            'unitAddress'
         ].split(' #')[-1] if ' #' in item['unitAddress'] else None,
        'city': item['city'],
        'state': item['stateOrProvince'],
        'zip': int(item['postalCode'])
    } for item in result]

    for item in response:
        if item['unit'] is None:
            del item['unit']

    return Response(body=response, status_code=200)
