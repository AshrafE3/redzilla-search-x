from chalice import Chalice, Response
from chalicelib.zipinfo import is_valid_zipcode, bounding_rectangle
from chalicelib.database import dynamo_query, expand
import json

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


def photo_uri(sdata):
    if 'ListingKeyNumeric' in sdata:
        source = 'CRMLS'
        photo_id = sdata['ListingKeyNumeric']
        listing_id = sdata['ListingId']
    else:
        source = 'SDMLS'
        photo_id = sdata['SystemID']
        listing_id = sdata['Listingid']
    return f"/main/{source}/{listing_id}/{photo_id}/{sdata['PhotosChangeTimestamp']}/360/360"  # noqa


def address(sdata):
    return sdata.get('Address', None) or ' '.join(
            filter(None, [
                sdata.get('StreetNumber', None),
                sdata.get('StreetDirPrefix', None),
                sdata.get('StreetDirSuffix', None),
                sdata.get('StreetName', None),
                sdata.get('StreetSuffix', None),
                sdata.get('StreetSuffixModifier', None)]))


@app.route('/search-x.api', methods=['POST'], cors=True)
def search():
    query_parameters = prepare(app.current_request.json_body)
    result = dynamo_query(query_parameters)
    print("len(result) =", len(result))

    expanded = expand(i['id'] for i in result)
    print("expanded[0] = ", json.dumps(expanded[0], indent=4, default=str))

    response = [{
        'id': item['id'],
        'photoUri': photo_uri(item['standard_data']),
        'latitude': float(item['latitude']),
        'longitude': float(item['longitude']),
        'displayPrice': int(float(item['standard_data']['ListPrice'])),
        'status': item['status'],
        'bedrooms': int(item['bedroomsTotal']),
        'fullBathrooms': (
            int(item['bathroomsTotalInteger']) -
            int(item['standard_data'].get('BathroomsHalf', '0'))
        ),
        'halfBathrooms': int(item['standard_data'].get('BathroomsHalf', '0')),
        'squareFeet': int(item['livingArea']),
        'address': address(item['standard_data']),
        'city': item['standard_data']['City'],
        'state': item['standard_data']['StateOrProvince'],
        'unit': (item['standard_data'].get('UnitNumber', None) or
                 item['standard_data'].get('StreetAdditionalInfo', None)),
        'zip': int(item['postalCode'])
    } for item in expanded]

    for item in response:
        if item['unit'] is None:
            del item['unit']

    return Response(body=response, status_code=200)
