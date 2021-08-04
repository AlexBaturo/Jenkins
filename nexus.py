#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Maxim Pinus <pinus@fintech.ru>
# FINTECH

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'FINTECH'
}

DOCUMENTATION = '''
---

author:
    - Maxim Pinus (<pinus@fintech.ru>)
'''

import os
import pycurl
import sys
from pprint import pprint
import json
from io import BytesIO
from datetime import datetime
from ansible.module_utils.basic import AnsibleModule

DEBUG_LVL = 0
header = 'accept: application/json'

# username = 'admin'
# password = 'admin'
# # search = 'sintezm-portal-aszi'
# # search = 'pszi-eod-0.0-14.el8.sz.noarch'
# search = 'python3-pyasn1'
# # format = 'raw'
# # repo = 'test_iso'
#
# format = 'yum'
# repo = 'test_build'
#
#
#
# # repos='http://10.254.112.88:8081/service/rest/v1/repositories'
# # url='http://10.254.112.88:8081/service/rest/v1/search?q=pszi-eod&repository=test_build&format=yum'
# url = 'http://10.254.112.88:8081'

class Nexus:

    def __init__(self, url, user, password, DEBUG_LVL, header):
        self.url = url
        self.user = user
        self.password = password
        self.DEBUG_LVL = DEBUG_LVL
        self.header = header

    def connect_api(self, nexus_api_url, delete=False, path_to_file=None, post_data=None):
        data = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, nexus_api_url)
        crl.setopt(crl.USERPWD, "%s:%s" % (self.user, self.password))
        crl.setopt(crl.HTTPHEADER, [ self.header ])
        crl.setopt(crl.VERBOSE, self.DEBUG_LVL)
        crl.setopt(crl.SSL_VERIFYPEER, 0)
        if delete:
            crl.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        if path_to_file:
            crl.setopt(pycurl.UPLOAD, 1)
            crl.setopt(pycurl.READFUNCTION, open(path_to_file, 'rb').read)
            # Set size of file to be uploaded.
            crl.setopt(pycurl.INFILESIZE, os.path.getsize(path_to_file))
        if post_data:
            crl.setopt(crl.HTTPHEADER, ["accept: application/json", "Content-Type: application/json"])
            crl.setopt(pycurl.POST, 1)
            crl.setopt(pycurl.POSTFIELDS, post_data)
        crl.setopt(crl.WRITEDATA, data)
        crl.perform()
        return data

    def get_data(self):
        data = self.connect_api(self.url)
        dictionary = json.loads(data.getvalue())
        return dictionary

    def search_iso(self, search, repo, format):
        nexusApi = self.url + '/service/rest/v1/search?q=' + search + '&repository=' + repo + '&format=' + format
        data = self.connect_api(nexusApi)
        dictionary = json.loads(data.getvalue())
        my_dict = dict()
        latest_date = datetime(1, 1, 1)
        while True:
            for i in dictionary["items"]:
                if search in i['group']:
                    date_list=i['group'].split('/')[-1].split('-')
                    current_date=datetime(int(date_list[0]), int(date_list[1]), int(date_list[2]))
                    if current_date > latest_date:
                        latest_date = current_date
                        my_dict.update({ 'name': i['group'].split('/')[3], 'url': i["assets"][0]["downloadUrl"]})
                else:
                    break
            if dictionary['continuationToken'] is None:
                break
            nexusApi = self.url + '/service/rest/v1/search?continuationToken=' + dictionary['continuationToken'] + '&q=' + search + '&repository=' + repo + '&format=' + format
            data = self.connect_api(nexusApi)
            dictionary = json.loads(data.getvalue())
        return my_dict

    def search_art(self, search, repo, format):
        nexusApi = self.url + '/service/rest/v1/search?q=' + '\"{}\"'.format(search) +  '&repository=' + repo + '&format=' + format #'&version=0.0-9.el8.sz' +
        data = self.connect_api(nexusApi)
        dictionary = json.loads(data.getvalue())
        #pprint(dictionary)
        version_dict = dict()
        latest_version = 0
        while True:
            for i in dictionary["items"]:
                if search == i['name']:  #or search == i['name']:
                    version_list = i['version'].split('-')[1].split('.')
                    current_version = int(version_list[0])
                    if current_version > latest_version:
                        latest_version = current_version
                        version_dict.update({'version': i['version'], 'url': i["assets"][0]["downloadUrl"]})
                else:
                    break
            if dictionary['continuationToken'] is None:
                break
            nexusApi = self.url + '/service/rest/v1/search?continuationToken=' + dictionary['continuationToken'] + '&q=' + '\"{}\"'.format(search) + '&repository=' + repo + '&format=' + format
            data = self.connect_api(nexusApi)
            dictionary = json.loads(data.getvalue())
        return version_dict

    def remove_art(self, search, repo):
        nexusApi = "{0}/repository/{1}/{2}".format(self.url, repo, search)
        self.connect_api(nexusApi, delete=True)

    def upload_art(self, search, repo, path_to_file):
        nexusApi = "{0}/repository/{1}/{2}".format(self.url, repo, search)
        self.connect_api(nexusApi, path_to_file=path_to_file)

    def create_repo(self, repo, format, depth):
        nexusApi = "{0}/service/rest/beta/repositories/{1}/hosted".format(self.url, format)
        post_data = json.dumps({"name": repo,
                                "online": "true",
                                "storage": {"blobStoreName": "default", "strictContentTypeValidation": "false", "writePolicy": "allow"},
                                format: {"repodataDepth": depth, "deployPolicy": "STRICT"}})
        self.connect_api(nexusApi, post_data=post_data)

    def remove_repo(self, repo):
        nexusApi = "{0}/service/rest/v1/repositories/{1}".format(self.url, repo)
        self.connect_api(nexusApi, delete=True)

# art_search(header, url, username, password, DEBUG_LVL, search, repo, format)
# iso_search(header, url, username, password, DEBUG_LVL, search, repo, format)


def main():


    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'absent', 'create', 'search_iso', 'search_art', 'upload_art', 'remove_art', 'create_repo', 'remove_repo']),
            user = dict(required=True),
            repo_url = dict(required=True),
            path_to_file = dict(),
            password = dict(required=True),
            search = dict(),
            repo = dict(),
            format = dict(),
            depth = dict()
        )
    )

    state         = module.params['state']
    user          = module.params['user']
    repo_url           = module.params['repo_url']
    password      = module.params['password']
    search        = module.params['search']
    repo          = module.params['repo']
    format        = module.params['format']
    path_to_file  = module.params['path_to_file']
    depth = module.params['depth']

    nexus = Nexus(repo_url, user, password, DEBUG_LVL, header)
    if state == 'search_iso':
        c = nexus.search_iso(search, repo, format)
        module.exit_json(changed=False, msg=c)
    if state == 'search_art':
        c = nexus.search_art(search, repo, format)
        module.exit_json(changed=False, msg=c)
    if state == 'present':
        c = nexus.get_data()
        module.exit_json(changed=False, msg=c)
    if state == 'remove_art':
        c = nexus.remove_art(search, repo)
        module.exit_json(changed=False, msg=c)
    if state == 'upload_art':
        c = nexus.upload_art(search, repo, path_to_file)
        module.exit_json(changed=False, msg=c)
    if state == 'create_repo':
        c = nexus.create_repo(repo, format, depth)
        module.exit_json(changed=False, msg=c)
    if state == 'remove_repo':
        c = nexus.remove_repo(repo)
        module.exit_json(changed=False, msg=c)


if __name__ != "__main__":
    sys.exit()

main()
