import requests

from core.apps.shared.utils.get_text_from_file import extract_text


def check_file(file):
    try:
        text = extract_text(file)
        data = {
            "txt_inp": text
        }
        response = requests.post("https://plagiat.ai/check_txt2", data=data)
        return response.json(), True
    except requests.exceptions.RequestException:
        return "", False
