#!/usr/bin/env python
import pydecorator
import os,requests
from contextlib import closing
from zipfile import ZipFile
from .tree import *
from .util import splitpath

class TruncatedError(Exception):
    pass



class GHSession():
    def __init__(self,username,password,repository):
        self.user = username
        self.pw = password
        self.repo = repository

    @property
    def auth(self):
        return (self.user,self.pw)

    def _getjson(self,url):
        try:
            with closing(requests.get(url,auth=self.auth)) as r:
                return r.json()
        except requests.exceptions.RequestException as e:
            print('Error during requests to  {}: {}'.format(url, str(e)))


    def commitinfo(self,chash):
        url = "https://api.github.com/repos/{}/{}/git/commits/{}".format(self.user,self.repo,chash)
        json = self._getjson(url)
        return {
            "repo":self.repo,
            "hash":json['sha'],
            "thash":json["tree"]["sha"],
            "date":json["committer"]["date"],
            "message":json["message"],
        }

    @pydecorator.list
    def allcommits(self):
        commits,page = [],1
        batchurl = "https://api.github.com/repos/{}/{}/commits?per_page=100&page={}".format(self.user,self.repo,page)
        batch = self._getjson(batchurl)
        while len(batch)==100:
            commits,page = commits+batch,page+1
            batchurl = "https://api.github.com/repos/{}/{}/commits?per_page=100&page={}".format(self.user,self.repo,page)
            batch = self._getjson(batchurl)
        for json in (commits+batch):
            yield {
                "repo":self.repo,
                "hash":json['sha'],
                "thash":json['commit']['tree']['sha'],
                "date":json['commit']['committer']['date'],
                "message":json['commit']['message']
            }

    def filetree_sha(self,thash):
        url = "https://api.github.com/repos/{}/{}/git/trees/{}".format(self.user,self.repo,thash)
        json = self._getjson(url)
        if json['truncated'] == True:
            raise TruncatedError("File tree is truncted")
        for f,sha in [(x['path'],x['sha']) for x in json['tree'] if x['type']!='tree']:
            yield f,sha
        for st,sthash in [(x['path'],x['sha']) for x in json['tree'] if x['type']=='tree']:
            for f,sha in self.filetree_sha(sthash):
                yield os.path.join(st,f),sha

    def filetree(self,thash):
        return [f for f,sha in self.filetree_sha(thash)]

    def commitfiles(self,chash):
        url = "https://api.github.com/repos/{}/{}/commits/{}".format(self.user,self.repo,chash)
        json = self._getjson(url)
        info = {
            'repo':self.repo,
            'hash':chash,
            'thash':json["commit"]['tree']['sha'],
            'date':json["commit"]["committer"]["date"],
            'message':json["commit"]["message"],
            'additions':json['stats']['additions'],
            'deletions':json['stats']['deletions']
        }
        return info,sorted([ChangedCommitFile(x) for x in json['files']])


    @staticmethod
    def _merge_filetree(commits,filetree):
        i1,i2,n1,n2 = 0,0,len(commits),len(filetree)
        while i1<n1 and i2<n2:
            z = commits[i1].cmp(filetree[i2])
            if z < 0:
                yield commits[i1]
                i1 = i1+1
            elif z > 0:
                yield filetree[i2]
                i2 = i2+1
            else:
                assert commits[i1].sha == filetree[i2].sha, "Files (%s , %s) Do not have same sha"%(commits[i1],filetree[i2])
                yield commits[i1]
                i1,i2 = i1+1,i2+1
        while i1<n1:
            yield commits[i1]
            i1 = i1+1
        while i2<n2:
            yield filetree[i2]
            i2 = i2+1

    def commit_tree(self,sha,filetype=None,exclude=None,include=None):
        """
        filetype -> filetypes to use in file tree
        exclude -> paths to exclude from file tree
        """
        url = "https://api.github.com/repos/{}/{}/commits/{}".format(self.user,self.repo,sha)
        json = self._getjson(url)
        treehash = json["commit"]['tree']['sha']
        date = json["commit"]["committer"]["date"]
        message = json["commit"]["message"]
        stats = json['stats']
        commit_files = sorted([ChangedCommitFile(x) for x in json['files']])
        file_tree = sorted([CommitFile(*x) for x in self.filetree_sha(treehash)])
        if filetype != None:
            if type(filetype) == str: filetype = [filetype]
            file_tree = [f for f in file_tree if f.filetype in filetype]
        if exclude != None:
            if type(exclude) == str: exclude = [exclude]
            exclude = [splitpath(p) for p in exclude]
            file_tree = [f for f in file_tree if not any(f.inpath(x) for x in exclude)]
        if include != None:
            if type(include) == str: include = [include]
            include = [splitpath(p) for p in include]
            file_tree = [f for f in file_tree if any(f.inpath(x) for x in include)]
        return CommitTree([*self._merge_filetree(commit_files,file_tree)],self.repo,sha,date,message,stats['additions'],stats['deletions'])

        return CommitTree([*self._merge_filetree(commit_files,file_tree)],self.repo,sha,date,message,stats['additions'],stats['deletions'])

    def download_commit(self,chash,topath):
        zipurl = "https://github.com/{}/{}/archive/{}.zip".format(self.user,self.repo,chash)
        dirpath = os.path.dirname(topath)
        zippath = os.path.join(dirpath,"{}-{}".format(self.repo,chash))
        # Download
        try:
            with closing(requests.get(zipurl,stream=True,auth=self.auth)) as r,open(zippath+".zip",'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
        except requests.exceptions.RequestException as e:
            print('Error during requests to {0} : {1}'.format(zipurl, str(e)))
        # Extract
        with ZipFile(zippath+".zip", 'r') as z:
            z.extractall(dirpath)
        # Remove Zipfile
        os.remove(zippath+".zip")
        # Rename
        os.rename(zippath,topath)
