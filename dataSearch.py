import requests
from bs4 import BeautifulSoup

def search_google(query):
    print("searching...")
    api_key = "AIzaSyDQzE1u1LNDERNCBpXBC9mxntYKStrEWlE"
    cx = "f335791899e1e4129"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}"

    response = requests.get(url)
    data = response.json()
    if 'items' not in data:
        return (["No results found."], [])

    snippets = [result.get("snippet", "") for result in data['items']]

    urls = [result.get('link') for result in data.get('items', [])[:2] if result.get('link')]
    print("urls: ", urls)
    data_contents = [scrape_full_content(url) for url in urls]
    images = [scrape_images(url) for url in urls]
    images = [image for sub_images in images for image in sub_images]

    print("data content:", data_contents)

    return (snippets + data_contents, images)


def scrape_full_content(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all(['p', 'span'])
        full_text = ' '.join(para.get_text() for para in paragraphs)
        return full_text.strip() if full_text else "No text content found."
    except requests.exceptions.RequestException as e:
        return f"Request Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def scrape_images(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        image_tags = soup.find_all('img')
        links = [(img['src'], img['alt']) for img in image_tags if 'src' and 'alt' in img.attrs]

        return links if links else ["No images found."]
    except requests.exceptions.RequestException as e:
        return [f"Request Error: {str(e)}"]
    except Exception as e:
        return [f"Error: {str(e)}"]
