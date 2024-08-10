import os
import requests

def process_brave_search_results(raw_results):
    web_results = raw_results['web']['results']

    processed_results = []

    for result in web_results:
        processed_result = {
            'title': result['title'],
            'url': result['url'],
            'description': result['description']
        }

        processed_results.append(processed_result)

    return processed_results

def call(query, num_results=3, lang="en"):
    brave_api_key = os.getenv("BRAVE_API_KEY")
    assert(brave_api_key)

    url = f'https://api.search.brave.com/res/v1/web/search?q={query}&count={num_results}&search_lang={lang}'
    headers = {
        'X-Subscription-Token': brave_api_key,
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return process_brave_search_results(response.json())
    else:
        return "Brave API returned response with a status code {response.status_code}"
