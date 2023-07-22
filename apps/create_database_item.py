import elabapi_python
from src.defaults import api_client

if __name__ == '__main__':
    # # create an instance of Items
    item = elabapi_python.ItemsApi(api_client)
    print(item.read_items())

    # create an instance of Experiments and another for Uploads
    # experimentsApi = elabapi_python.ExperimentsApi(api_client)
    # uploadsApi = elabapi_python.UploadsApi(api_client)

    targetCategory = 1
    response = item.post_item_with_http_info(
        body={'category_id': targetCategory, 'tags': ['API', 'SUCCESS']})
    locationHeaderInResponse = response[2].get('Location')

    item_id = int(locationHeaderInResponse.split('/').pop())
    # now change the title, and body and rating
    item.patch_item(item_id, body={'title': 'Test API item', 'body': 'This item was created with elabapi-python.',
                                   'rating': 3})
    print(item.get_item_with_http_info(id=0))
