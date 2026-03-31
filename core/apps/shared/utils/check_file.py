import requests

from core.apps.shared.utils.get_text_from_file import extract_text


def check_file(file = None, text = None):
    try:
        txt = ""
        if file is not None:
            txt = extract_text(file)
        elif text is not None:
            txt = text
        data = {
            "txt_inp": txt
        }
        response = requests.post("https://plagiat.ai/check_txt2", data=data)
        return response.json(), True
    except requests.exceptions.RequestException:
        return "", False
