
import requests
import json
import os

class GithubApi:
    def __init__(self, url, user, token, repo, workBranch):
        self.url = url
        self.user = user
        self.token = token
        self.repo = repo
        self.workBranch = workBranch

    def commitPush(self):
        # РџРѕР»СѓС‡Р°РµРј СЃСЃС‹Р»РєСѓ РЅР° РїРѕСЃР»РµРґРЅРёР№ РєРѕРјРјРёС‚
        ref = requests.get('{0}/repos/{1}/{2}/git/matching-refs/heads/{3}'.format(self.url, self.user, self.repo, self.workBranch), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        # РџРѕР»СѓС‡Р°РµРј С…СЌС€ РїРѕСЃР»РµРґРЅРµРіРѕ РєРѕРјРјРёС‚Р°
        shaHead = ref.json()[0]['object']['sha']
        # РџРѕР»СѓС‡Р°РµРј РёРЅС„Сѓ Рѕ РїРѕСЃР»РµРґРЅРµРј РєРѕРјРјРёС‚Рµ РІ РІРµС‚РєРµ workBranch
        commitHead = requests.get('{0}/repos/{1}/{2}/git/commits/{3}'.format(self.url, self.user, self.repo, shaHead), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        # РџРѕР»СѓС‡Р°РµРј С…СЌС€ РґРµСЂРµРІР°
        shaTree = commitHead.json()['tree']['sha'] 
        
        # РЎРѕР±РёСЂР°РµРј РЅР°Р·РІР°РЅРёСЏ С„Р°Р№Р»РѕРІ, РєСЂРѕРјРµ .git
        files = os.listdir()
        files.remove('.git')
        fileShaBlobDict = dict()
        # Р—Р°РіСЂСѓР·РєР° СЃРѕРґРµСЂР¶РёРјРѕРіРѕ С„Р°Р№Р»РѕРІ
        for file in files:

            changedFilesData = {"content":  open(file,"r").read()}  
            blob = requests.post('{0}/repos/{1}/{2}/git/blobs'.format(self.url, self.user, self.repo), json=changedFilesData, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
            fileShaBlobDict[file] = blob.json()['sha']
        # РЎРѕР·РґР°РЅРёРµ РёРЅС„РѕСЂРјР°С†РёРё Рѕ С„Р°Р№Р»Р°С…
        changedFilesData = {"tree" : []}
        for file, shaBlob in fileShaBlobDict.items():
            changedFilesData["tree"].append({"path":file,"mode":"100644","type":"blob","sha": shaBlob})

        # РёРЅС„Р° РґРµСЂРµРІР° РїРѕСЃР»РµРґРЅРµРіРѕ РєРѕРјРјРёС‚Р°
        tree = requests.get('{0}/repos/{1}/{2}/git/trees/{3}'.format(self.url, self.user, self.repo, shaTree), auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        
        # СЃРѕР·РґР°РµРј РґРµСЂРµРІРѕ
        #changedFilesData = {"tree":[{"path":"README.md","mode":"100644","type":"blob","sha": shaBlob1}, {"path":"testfile.jenkins","mode":"100644","type":"blob","sha": shaBlob2}]}
        treeHead = requests.post('{0}/repos/{1}/{2}/git/trees'.format(self.url, self.user, self.repo), json=changedFilesData, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        
        shaTreeHead = treeHead.json()['sha']
        #print(treeHead.json())
        #РЎРѕР·РґР°РЅРёРµ РєРѕРјРјРёС‚Р°
        commitInfo = {"message":"from api","tree": shaTreeHead, "parents": [shaHead] }
        commitRespons = requests.post('{0}/repos/{1}/{2}/git/commits'.format(self.url, self.user, self.repo), json=commitInfo, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        shaNewCommit = commitRespons.json()['sha']

        updateInfo = {"sha": shaNewCommit}
        updateResponse = requests.post('{0}/repos/{1}/{2}/git/refs/heads/{3}'.format(self.url, self.user, self.repo, self.workBranch), json=updateInfo, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        
        #curl -u AlexBaturo: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  -X PATCH   -H "Accept: application/vnd.github.v3+json"   https://api.github.com/repos/AlexBaturo/Jenkins/git/refs/heads/dev   -d '{"sha":"90f5a1500731930765652a98623cf650624a9214"}'
        #РћР±РЅРѕРІР»РµРЅРёРµ РєРѕРјРјРёС‚Р°



    def pullRequest(self):
        pullRequestInfo = {"head":"dev","base":"master", "title" : "fromApi"}
        pullRequestRespons = requests.post('{0}/repos/{1}/{2}/pulls'.format(self.url, self.user, self.repo), json=pullRequestInfo, auth=(self.user, self.token), headers={"Accept" : "application/vnd.github.v3+json"})
        print(pullRequestRespons.json())

url = "https://api.github.com"
user = "AlexBaturo"
token = "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"
repo = "Jenkins"
workBranch = "dev"

test = GithubApi(url, user, token, repo, workBranch)
test.commitPush()
test.pullRequest()
