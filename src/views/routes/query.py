from flask import Blueprint, request
from src.models.response import Response
from src.controllers.query import search as search_func

# Create a Flask Blueprint for the query functionality
query_blue = Blueprint('query', __name__)


@query_blue.route('/', methods=['GET'])
def query():
    """
    Search Endpoint: Receives user queries and returns search results

    Args:
        - query (str, required): The search string.
        - result_type (str, optional): The format of the returned content, default is "json".
        - iterations (int, optional): The number of content iterations, default is 1.
        - model (str, optional): The retrieval model to be used, default is "default".

    Returns:
        - Response: A response containing the search results.
    """
    # Get the 'query' parameter from the request
    query_str = request.args.get('query', type=str)

    # Check if the required 'query' parameter is provided
    if query_str is None:
        return Response('The "query" parameter is required.').error()

    # Get optional parameters or use defaults if not provided
    result_type = request.args.get('result_type', default='json', type=str)
    iterations = request.args.get('iterations', default=1, type=int)
    model = request.args.get('model', default='default', type=str)

    # Call the search function with the provided parameters
    return search_func(query_str, result_type, iterations, model)
