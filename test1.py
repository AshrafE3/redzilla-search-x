import unittest
import os

os.environ['DYNAMO_TABLE'] = 'test-rets-search'
import app  # noqa


query_parameters = {
    'keywords': '92101', 'availableOnly': 1,
    'forSaleTypes': [
        'By Agent', 'Coming Soon', 'By Owner', 'Auction',
        'New Construction', 'Foreclosures'
    ],
    'propertyType': [
        'Condo', 'House', 'Town_House', 'Multi_Unit', 'Modular',
        'Commercial', 'Land', 'Timeshare', 'Parking', 'Rental', 'Other'
    ],
    'otherAmenities': [],
    'viewTypes': [],
    'per_page': 200
}


class TestSearch(unittest.TestCase):

    def test_search(self):
        # Arrange

        # Act
        app.app.current_request = type(
            'Request',
            (object,),
            {'json_body': query_parameters}
        )
        response = app.search()

        # Assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, app.Response)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.body), 10)


if __name__ == '__main__':
    unittest.main()
