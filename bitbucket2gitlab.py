# -*- coding: utf-8 -*-
import os
import requests
import urllib3

# Отключаем warning - Unverified HTTPS request is being made
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Присваиваем переменным результат конкатенации адреса до bitbucket и gitlab с контекстным путём до API
bitbucket_url = os.getenv("bitbucket_url")
gitlab_url = os.getenv("gitlab_url")

# Присваиваем переменным Bearer tokens
bitbucket_bearer = os.getenv("bitbucket_bearer_password")
gitlab_bearer = os.getenv("gitlab_bearer_password")

# Создаём словари для хранения key-value данных
bitbucket_projects = dict()
gitlab_projects = dict()


# Проверяем данные в необходимых для работы переменных
def validate_env():
    if bitbucket_bearer is None:
        print("Missing environment variable - bitbucket_bearer_password")
        return False

    if gitlab_bearer is None:
        print("Missing environment variable - gitlab_bearer_password")
        return False

    if os.getenv("bamboo_raiffeisen_bitbucket_url") is None:
        print("Missing environment variable - raiffeisen_bitbucket_url")
        return False
    else:
        global bitbucket_url
        bitbucket_url += "rest/api/1.0/"

    if os.getenv("bamboo_raiffeisen_gitlab_url") is None:
        print("Missing environment variable - raiffeisen_gitlab_url")
        return False
    else:
        global gitlab_url
        gitlab_url += "api/v4/"

    return True


# Получаем ответ от битбакета
def get_bitbucket_projects(bb_path, bb_bearer):
    custom_headers = {"Authorization": "Bearer " + bb_bearer,
                      "Content-Type": "application/json"}
    resp = requests.get(bitbucket_url + bb_path, verify=False, headers=custom_headers)
    if resp.status_code != 200:
        print("Cannot connect to bitbucket", bb_path)
        print(resp.text)
        exit(1)
    for project in resp.json()["values"]:
        bitbucket_projects[project["key"]] = project["name"]

    return bitbucket_projects


# Получаем ответ от гитлаба
def get_gitlab_projects(gl_path, gl_bearer):
    custom_headers = {"Authorization": "Bearer " + gl_bearer,
                      "Content-Type": "application/json"}
    resp = requests.get(gitlab_url + gl_path, verify=False, headers=custom_headers)
    if resp.status_code != 200:
        print("Cannot connect to gitlab", gl_path)
        print(resp.text)
        exit(1)
    for project in resp.json():
        gitlab_projects[project["name"]] = project["id"]

    return gitlab_projects


# Находим одинаковые и правим имена, как в битбакете
def set_gitlab_projects(bb_projects, gl_projects, gl_path, gl_bearer):
    bitbucket_set = set(bb_projects.keys())
    gitlab_set = set(gl_projects.keys())
    same_set = bitbucket_set & gitlab_set

    custom_headers = {"Authorization": "Bearer " + gl_bearer,
                      "Content-Type": "application/json"}
    for x in same_set:
        gitlab_key = gl_projects[x]
        gitlab_name = bb_projects[x]
        if bb_projects.get(x) == x:
            continue
        requests.put(gitlab_url + gl_path + str(gitlab_key) + "?name=" + gitlab_name,
                     verify=False, headers=custom_headers)
        print("Changed: " + x + " to " + gitlab_name)

    return True


def main():
    if not validate_env():
        exit(1)

    get_bitbucket_projects("projects?limit=1000", bitbucket_bearer)
    get_gitlab_projects("groups", gitlab_bearer)
    set_gitlab_projects(bitbucket_projects, gitlab_projects, "groups/", gitlab_bearer)


if __name__ == "__main__":
    main()
