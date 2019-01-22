#!/usr/bin/env python

import sys,re,os,requests
from contextlib import closing
from zipfile import ZipFile
from .util import format_isotime,format_commit_str

def download(url,savefile,**kwargs):
    try:
        with closing(requests.get(url,stream=True,**kwargs)) as r,open(savefile,'wb') as f:
            #total_size = int(r.headers['content-length'])
            #loops = total_size // 1024 + int(total_size % 1024 > 0)
            #for chunk in cmdprogress.ProgBar(max=loops).iter(r.iter_content(chunk_size=1024)):
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))

def extract(zipfile,todir):
    with ZipFile(zipfile, 'r') as z:
        z.extractall(todir)



def commit_data(repo,json):
    return {
        "repo":repo,
        "hash":json['sha'],
        "thash":json['commit']['tree']['sha'],
        "date":json['commit']['committer']['date'],
        "message":json['commit']['message']
    }

class GitHubSession():
    def __init__(self,username,password):
        self.user = username
        self.pw = password

    @property
    def auth(self):
        return (self.user,self.pw)


    def _repo_commits_batch(self,repo,page):
        url = "https://api.github.com/repos/{}/{}/commits?per_page=100&page={}".format(self.user,repo,page)
        try:
            with closing(requests.get(url,auth=self.auth)) as r:
                commits = [commit_data(repo,x) for x in r.json()]
                return commits
        except requests.exceptions.RequestException as e:
            print('Error during requests to {0} : {1}'.format(url, str(e)))
        

    def repo_commits(self,repo):
        commits,i = [],1
        batch = self._repo_commits_batch(repo,i)
        while len(batch)==100:
            commits,i = commits+batch,i+1
            batch = self._repo_commits_batch(repo,i)
        return commits+batch
    

    def commit_info(self,repo,chash):
        url = "https://api.github.com/repos/{}/{}/git/commits/{}".format(self.user,repo,chash)
        try:
            with closing(requests.get(url,auth=self.auth)) as r:
                json = r.json()
                return {
                    "repo":repo,
                    "hash":json['sha'],
                    "thash":json["tree"]["sha"],
                    "date":json["committer"]["date"],
                    "message":json["message"],
                }
        except requests.exceptions.RequestException as e:
            print('Error during requests to {0} : {1}'.format(url, str(e)))

    def download_commit(self,info,fmt,verify):
        repo,chash = info['repo'],info['hash']
        dirname = format_commit_str(info,fmt)
        endpath = os.path.join(os.getcwd(),dirname)
        if os.path.exists(endpath):
            print("Cannot download commit from '{}' repository, '{}' already exists in this directory".format(repo,dirname),file=sys.stderr)
            return
        if verify:
            if input("Download '{}' [y/n]:".format(dirname)).lower() != 'y':
                return
        else:
            print("Downloading '{}'".format(dirname),file=sys.stderr)
        zipurl = "https://github.com/{}/{}/archive/{}.zip".format(self.user,repo,chash)
        zipname = "{}-{}".format(repo,chash)
        zipfile = os.path.join(os.getcwd(),zipname+".zip")
        # Download
        download(zipurl,zipfile,auth=self.auth)
        # Extract
        extract(zipfile,os.getcwd())
        os.remove(zipfile)
        # Rename
        os.rename(os.path.join(os.getcwd(),zipname),endpath)


