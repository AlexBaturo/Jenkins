
import requests
import json
import os

class GithubApi:
    def __init__(self, url, user, token, repo):
        self.url = url
        self.user = user
        self.token = token
        self.repo = repo

    def commitPush(self):
        # Получаем ссылку на последний коммит
        ref = requests.get('{0}/repos/{1}/{2}/git/matching-refs/heads/master'.format(self.url, self.user, self.repo), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        # Получаем хэш последнего коммита
        shaHead = ref.json()[0]['object']['sha']
        # Получаем инфу о последнем коммите в ветке master
        commitHead = requests.get('{0}/repos/{1}/{2}/git/commits/{3}'.format(self.url, self.user, self.repo, shaHead), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        # Получаем хэш дерева
        shaTree = commitHead.json()['tree']['sha'] 
        # Загрузка измененных файлов
        #data = {"content": self.getChangedFiles()}
        changedFilesData = {"content": "README.md"}  
        blob = requests.post('{0}/repos/{1}/{2}/git/blobs'.format(self.url, self.user, self.repo), json=changedFilesData, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        shaBlob = blob.json()['sha']
        # инфа дерева последнего коммита
        tree = requests.get('{0}/repos/{1}/{2}/git/trees/{3}'.format(self.url, self.user, self.repo, shaTree), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        # создаем дерево
        changedFilesData = {"tree":[{"path":"README.md","mode":"100644","type":"blob","sha": shaBlob}]}
        treeHead = requests.post('{0}/repos/{1}/{2}/git/trees'.format(self.url, self.user, self.repo), json=changedFilesData, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        shaTreeHead = treeHead.json()['sha']
        #print(treeHead.json())
        #Создание коммита
        commitInfo = {"message":"from api","tree": shaTreeHead, "parents": [shaHead] }
        commitRespons = requests.post('{0}/repos/{1}/{2}/git/commits'.format(self.url, self.user, self.repo), json=commitInfo, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        shaNewCommit = commitRespons.json()['sha']

        updateInfo = {"sha": shaNewCommit}
        updateResponse = requests.post('{0}/repos/{1}/{2}/git/refs/heads/master'.format(self.url, self.user, self.repo), json=updateInfo, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        print(updateResponse.json())
        #curl -u AlexBaturo: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  -X PATCH   -H "Accept: application/vnd.github.v3+json"   https://api.github.com/repos/AlexBaturo/Jenkins/git/refs/heads/master   -d '{"sha":"90f5a1500731930765652a98623cf650624a9214"}'
        #Обновление коммита

    def getChangedFiles(self):
        bash_command = "git status"
        result_os = os.popen(bash_command).read()
        is_change = False
        prepare_result = list()
        for result in result_os.split('\n'):
            if result.find('modified') != -1:
                prepare_result.append(result.replace('\tmodified:   ', ''))
                return ",".join(prepare_result)

url = "https://api.github.com"
user = "AlexBaturo"
token = "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"
repo = "Jenkins"

test = GithubApi(url, user, token, repo)
test.commitPush()
#test.getChangedFiles()