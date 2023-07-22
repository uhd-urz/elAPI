import elabapi_python
from decouple import config

HOST = config("HOST")
API_KEY = config("API_KEY")
TOKEN_BEARER = config("TOKEN_BEARER")

configuration = elabapi_python.Configuration()
configuration.api_key["api_key"] = API_KEY
configuration.api_key_prefix["api_key"] = TOKEN_BEARER
configuration.host = HOST

# change to include debug information
configuration.debug = False
configuration.verify_ssl = True

# client handler object
api_client = elabapi_python.ApiClient(configuration)

# Observation: The following is a repetition of the headers above
# the following was taken from the official examples: https://github.com/elabftw/elabapi-python/tree/master/examples
# commenting it out results in authorization error.

# fix issue with Authorization header not being properly set by the generated lib
api_client.set_default_header(header_name=TOKEN_BEARER, header_value=API_KEY)

# After digging through the implementation
# api_client.set_default_header(any_valid_http_header, header_value)
# api_client.set_default_header(header_name='Content-Type', header_value='application/json')
