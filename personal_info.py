# Reference: https://www.blakeporterneuro.com/learning-python-project-3-scrapping-data-from-steams-community-market/

def get_steam_cookie(file_name_with_personal_info='personal_info.txt'):
    try:
        with open(file_name_with_personal_info, 'r') as f:
            cookie_value = f.readlines()[0]
    except FileNotFoundError:
        cookie_value = None

    return cookie_value


def get_cookie_dict(cookie_value):
    cookie = {'steamLoginSecure': cookie_value}
    return cookie
