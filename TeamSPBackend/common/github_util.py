# -*- coding: utf-8 -*-
import json
import os
import logging
import re
import sys
import time

import requests
import zipfile
import io
import shutil

from TeamSPBackend.settings.base_setting import BASE_DIR
from TeamSPBackend.project.models import ProjectCoordinatorRelation

logger = logging.getLogger('django')

GITHUB = 'https://github.com/'
GITHUB_API_BASE_URL = 'https://api.github.com/'
GITHUB_API_REPOS_URL = GITHUB_API_BASE_URL + 'repos'

REPO_PATH = BASE_DIR + '/resource/repo/'
COMMIT_DIR = BASE_DIR + '/resource/commit_log'

GIT_CLONE_COMMAND = 'git clone {} {}'
GIT_CHECKOUT_COMMAND = 'git -C {} checkout {}'
GIT_UPDATE_COMMAND = 'git -C {} pull origin HEAD'
GIT_LOG_COMMAND = 'git -C {} log --pretty=format:%H%n%an%n%at%n%s --shortstat --no-merges'
GIT_LOG_PR_COMMAND = 'git -C {} log --pretty=format:%H%n%an%n%at%n%s --shortstat --merges'
GIT_LOG_AUTHOR = ' --author={}'
GIT_LOG_AFTER = ' --after={}'
GIT_LOG_BEFORE = ' --before={}'
GIT_LOG_PATH = ' --> {}'

# using Understand for analyze Metrics
# For Mac
# UND_PATH = '/Applications/Understand.app/Contents/MacOS/'
# For Linux Server
UND_PATH = '~/comp90082sp/understand/scitools/bin/linux64/'

# set Understand License
UND_LICENSE = 'und -setlicensecode XfA7YbMwUZ9OCYJd'
os.system(UND_LICENSE)

# understand und command line for loading a git repo and generate metrics
UND_METRICS = UND_PATH + 'und create -db {} -languages python C++ Java add {} {} analyze'

# Using Python API for get metrics
GET_METRICS_PY_PATH = os.path.dirname(
    os.path.abspath(__file__)) + '/get_und_metrics.py'
GET_METRICS_PY = 'python3 ' + GET_METRICS_PY_PATH + ' {} {}'
# storage metrics.json
METRICS_FILE_PATH = BASE_DIR + '/resource/understand/'


def construct_certification(repo, space_key):
    # filter null username and password
    user_info = ProjectCoordinatorRelation.objects.filter(space_key=space_key).exclude(
        git_username__isnull=True, git_password__isnull=True)
    if len(user_info) == 0:
        return -1  # -1 means there is no user data
    username = user_info[0].git_username  # 'chengzsh3'
    password = user_info[0].git_password  # 'Czs0707+'
    if len(username) == 0 or len(password) == 0:
        return -2  # -2 means there doesn't exist git username and pwd
    return repo[0:8] + username + ':' + password + '@' + repo[8:]


def getAuthInfo(space_key):
    # filter null username and password
    user_info = ProjectCoordinatorRelation.objects.filter(space_key=space_key).exclude(
        git_username__isnull=True, git_password__isnull=True)
    if len(user_info) == 0:
        return -1  # -1 means there is no user data
    username = user_info[0].git_username  # 'chengzsh3'
    password = user_info[0].git_password  # Personal Access Token
    if len(username) == 0 or len(password) == 0:
        return -2  # -2 means there doesn't exist git username and pwd
    return {"username": username, "password": password}


def init_git():
    if not os.path.exists(REPO_PATH):
        os.mkdir(REPO_PATH)
    if not os.path.exists(COMMIT_DIR):
        os.mkdir(COMMIT_DIR)


def convert(repo: str):
    return '-'.join(repo.replace(GITHUB, '').split('/'))


def check_path_exist(path):
    return os.path.exists(path)


def process_changed(changed):
    file_pattern = re.findall('\d+ file', changed)
    insert_pattern = re.findall('\d+ insert', changed)
    delete_pattern = re.findall('\d+ delet', changed)

    file = 0 if not file_pattern else int(file_pattern[0].strip(' file'))
    insert = 0 if not insert_pattern else int(
        insert_pattern[0].strip(' insert'))
    delete = 0 if not delete_pattern else int(
        delete_pattern[0].strip(' delet'))
    return file, insert, delete


def pull_repo(repo, space_key):
    repo = construct_certification(repo, space_key)
    if repo == -1 or repo == -2:
        return repo
    path = REPO_PATH + convert(repo)

    if check_path_exist(path):
        git_update = GIT_UPDATE_COMMAND.format(path)
        logger.info('[GIT] Path: {} Executing: {}'.format(path, git_update))

        os.system(git_update)
        return 1  # 1 means valid

    git_clone = GIT_CLONE_COMMAND.format(repo, path)
    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_clone))
    os.system(git_clone)
    return 1


def get_commits(repo, space_key, author=None, branch=None, after=None, before=None):
    state = pull_repo(repo, space_key)
    if state == -1 or state == -2:
        return state
    repo = construct_certification(repo, space_key)
    repo_path = REPO_PATH + convert(repo)
    path = COMMIT_DIR + '/' + convert(repo) + '.log'

    git_log = GIT_LOG_COMMAND.format(repo_path)
    if author:
        git_log += GIT_LOG_AUTHOR.format(author)
    if after:
        git_log += GIT_LOG_AFTER.format(after)
    if before:
        git_log += GIT_LOG_BEFORE.format(before)
    git_log += GIT_LOG_PATH.format(path)

    if not branch:
        branch = 'master'

    os.system(GIT_CHECKOUT_COMMAND.format(repo_path, branch))

    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_log))
    os.system(git_log)

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return None

    commits = list()
    for i in range(0, len(lines), 6):
        # hash_code = lines[i].strip()
        author = lines[i + 1].strip()
        date = int(lines[i + 2].strip())

        commit = dict(
            # hash=hash_code,
            author=author,
            date=date,
        )
        commits.append(commit)
    return commits


def extractInfoFromRepo(repoURL):
    repoParts = repoURL.split('/')
    owner = repoParts[3]
    repo = repoParts[4]

    return {'owner': owner, 'repo': repo}


def getBranches(repo, spacekey):
    authInfo = getAuthInfo(spacekey)
    if authInfo == -1 or authInfo == -2:
        return authInfo

    # repoInfo contains owner and repo info
    repoInfo = extractInfoFromRepo(repo)
    owner = repoInfo['owner']
    repository = repoInfo['repo']
    username = authInfo['username']
    password = authInfo['password']

    r = requests.get(
        f"{GITHUB_API_REPOS_URL}/{owner}/{repository}/branches",
        auth=(username, password))
    response = json.loads(r.text)
    return response


def getCommitsForBranch(branch, repo, spacekey):
    authInfo = getAuthInfo(spacekey)
    if authInfo == -1 or authInfo == -2:
        return authInfo

    # repoInfo contains owner and repo info
    repoInfo = extractInfoFromRepo(repo)
    owner = repoInfo['owner']
    repository = repoInfo['repo']
    username = authInfo['username']
    password = authInfo['password']

    r = requests.get(
        f"{GITHUB_API_REPOS_URL}/{owner}/{repository}/commits?sha={branch}",
        auth=(username, password))

    response = json.loads(r.text)
    return response


def getTreeForBranch(branch, repo, spacekey):
    authInfo = getAuthInfo(spacekey)
    if authInfo == -1 or authInfo == -2:
        return authInfo

    # repoInfo contains owner and repo info
    repoInfo = extractInfoFromRepo(repo)
    owner = repoInfo['owner']
    repository = repoInfo['repo']
    username = authInfo['username']
    password = authInfo['password']

    r = requests.get(
        f"{GITHUB_API_REPOS_URL}/{owner}/{repository}/git/trees/{branch}?recursive=1",
        auth=(username, password))

    response = json.loads(r.text)["tree"]

    return response


def deleteRepo():
    dirpath = "./repos"
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)


def getTreeNode(node):
    return {
        "id": node,
        "name": node,
        "children": []
    }


def getTreeView(file_name):
    res = getTreeNode(file_name)

    for root, dirs, files in os.walk(f"./repos/{file_name}", topdown=False):
        for name in files:
            # print(os.path.join(root, name))
            res["children"].append({
                "id": name,
                "name": name,
                "children": []
            })
        for name in dirs:
            # print(os.path.join(root, name))
            res["children"].append({
                "id": name,
                "name": name,
                "children": []
            })

    return res


def extractAndLoadRepo(repo):
    z = zipfile.ZipFile(io.BytesIO(repo.content))
    z.extractall("./repos")
    return next(os.walk('./repos'))[1][0]


def getRepoAsTreeView(repo, spacekey):
    authInfo = getAuthInfo(spacekey)
    if authInfo == -1 or authInfo == -2:
        return authInfo

    # repoInfo contains owner and repo info
    repoInfo = extractInfoFromRepo(repo)
    owner = repoInfo['owner']
    repository = repoInfo['repo']
    username = authInfo['username']
    password = authInfo['password']

    url = f"{GITHUB_API_REPOS_URL}/{owner}/{repository}/zipball"
    r = requests.get(url, auth=(username, password))
    file_name = extractAndLoadRepo(r)
    return getTreeView(file_name)


def getWeeklyCommits(repo, spacekey):
    authInfo = getAuthInfo(spacekey)
    if authInfo == -1 or authInfo == -2:
        return authInfo

    # repoInfo contains owner and repo info
    repoInfo = extractInfoFromRepo(repo)
    owner = repoInfo['owner']
    repository = repoInfo['repo']
    username = authInfo['username']
    password = authInfo['password']

    r = requests.get(
        f"{GITHUB_API_REPOS_URL}/{owner}/{repository}/stats/commit_activity",
        auth=(username, password))

    response = json.loads(r.text)
    return response


def get_pull_request(repo, author=None, branch=None, after=None, before=None):
    pull_repo(repo)

    repo_path = REPO_PATH + convert(repo)
    path = COMMIT_DIR + '/' + convert(repo) + '.log'

    git_log = GIT_LOG_PR_COMMAND.format(repo_path)
    if author:
        git_log += GIT_LOG_AUTHOR.format(author)
    if after:
        git_log += GIT_LOG_AFTER.format(after)
    if before:
        git_log += GIT_LOG_BEFORE.format(before)
    git_log += GIT_LOG_PATH.format(path)

    if not branch:
        branch = 'master'

    os.system(GIT_CHECKOUT_COMMAND.format(repo_path, branch))

    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_log))
    os.system(git_log)

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        raise Exception('git log error')

    commits = list()
    for i in range(0, len(lines), 4):
        hash_code = lines[i].strip()
        author = lines[i + 1].strip()
        date = int(lines[i + 2].strip()) * 1000
        description = lines[i + 3].strip()

        commit = dict(
            hash=hash_code,
            author=author,
            date=date,
            description=description,
        )
        commits.append(commit)
    return commits


def get_und_metrics(repo, space_key):
    state = pull_repo(repo, space_key)
    if state == -1 or state == -2:
        return state
    und_file = convert(repo) + '.und'
    metrics_file = convert(repo) + '.json'
    # bug-fixed: keep the same with  pull_repo()
    repo = construct_certification(repo, space_key)
    path = REPO_PATH + convert(repo)
    st_time = time.time()
    # Get .und , add files and analyze them
    und_metrics = UND_METRICS.format(und_file, path, und_file)
    logger.info('[Understand] File {} Executing: {}'.format(
        und_file, und_metrics))
    os.system(und_metrics)

    # Get metrics.json by using another .py script
    get_metrics_by_py = GET_METRICS_PY.format(und_file, metrics_file)
    logger.info('[Understand Python API Get Metrics] get_metrics_by_py: {} '.format(
        get_metrics_by_py))
    os.system(get_metrics_by_py)

    metrics_file = METRICS_FILE_PATH + metrics_file
    with open(metrics_file, 'r') as fp:
        tmp_dict = json.load(fp)
    metrics = tmp_dict
    end_time = time.time()
    cost_time = round(end_time - st_time, 2)
    logger.info('[Understand] File {} Get Metrics: {} , cost : {} seconds'.format(
        und_file, metrics, cost_time))
    return metrics

# if __name__ == '__main__':
#     init_git()
#     pull_repo('https://github.com/LikwunCheung/TeamSPBackend')
#     get_commits('https://github.com/LikwunCheung/TeamSPBackend')
