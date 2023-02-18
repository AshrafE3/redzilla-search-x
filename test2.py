import unittest
from unittest.mock import MagicMock
import os
os.environ['DYNAMO_TABLE'] = 'my_table'
from chalicelib import database  # noqa


# Mock the DynamoDB client and response
database.dynamodb = MagicMock()
database.dynamodb.batch_get_item.return_value = {
    'Responses': {
        'my_table': [
            {'id': {'S': '123'}, 'name': {'S': 'John Doe'}},
            {'id': {'S': '456'}, 'name': {'S': 'Jane Smith'}}
        ]
    }
}


class TestExpand(unittest.TestCase):
    def test_expand(self):

        # Call the expand function with a list of IDs
        result = database.expand(['123', '456'])

        # Assert that the expected items were returned
        expected = [
            {'id': '123', 'name': 'John Doe'},
            {'id': '456', 'name': 'Jane Smith'}
        ]
        self.assertEqual(result, expected)

        # Assert that the DynamoDB client was called with the correct arguments
        database.dynamodb.batch_get_item.assert_called_once_with(
            RequestItems={
                'my_table': {
                    'Keys': [{'id': {'S': '123'}}, {'id': {'S': '456'}}]
                }
            }
        )
