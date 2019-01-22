import sys,re,os,requests,argparse
from contextlib import closing
from zipfile import ZipFile
import pydecorator
import getpass

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

def format_isotime(d):
    year,month,day,hour,minute = d[:4],d[5:7],d[8:10],d[11:13],d[14:16]
    # second = d[17:19]
    return "{}-{}-{}_{}-{}".format(year,month,day,hour,minute)


# ----------- Sort Commits ----------- #

@pydecorator.mergesort(duplicate_values=True)
def sort_commits(a,b):
    t0,t1 = a['date'],b['date']
    y0,y1 = int(t0[:4]),int(t1[:4])
    if y0 != y1: return -1 if y0 < y1 else 1
    m0,m1 = int(t0[5:7]),int(t1[5:7])
    if m0 != m1: return -1 if m0 < m1 else 1
    d0,d1 = int(t0[8:10]),int(t1[8:10])
    if d0 != d1: return -1 if d0 < d1 else 1
    H0,H1 = int(t0[11:13]),int(t1[11:13])
    if H0 != H1: return -1 if H0 < H1 else 1
    M0,M1 = int(t0[14:16]),int(t1[14:16])
    if M0 != M1: return -1 if M0 < M1 else 1
    S0,S1 = int(t0[17:19]),int(t1[17:19])
    return -1 if S0 < S1 else 1


# -------------- Github Session -------------- # 

def commit_data(json):
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
                commits = [commit_data(x) for x in r.json()]
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

    def download_commit(self,info,verify):
        repo,chash = info['repo'],info['hash']
        dirname = "{}_{}".format(format_isotime(info['date']),chash[:8])
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


def ls(session,args):
    commits = session.repo_commits(args.repo)
    print("{} Commits in repository '{}'".format(len(commits),args.repo),file=sys.stderr)
    message = args.message
    fullhash = args.fullhash
    for c in sort_commits(commits):
        time = format_isotime(c['date'])
        chash = c['hash'] if fullhash==True else c['hash'][:8]
        print("{} {}".format(chash,time),file=sys.stdout)
        if message:
            print('\n'.join('\t'+x for x in c['message'].split('\n')),file=sys.stdout)

def get(session,args):
    if args.commit != None:
        info = session.commit_info(args.repo,args.commit)
        session.download_commit(info,args.verify)
        return
    commits = session.repo_commits(args.repo)
    print("{} Commits in repository '{}'".format(len(commits),args.repo),file=sys.stderr)
    for c in commits:
        session.download_commit(c,args.verify)

def main():
    parser = argparse.ArgumentParser(prog='ghrepo',description='Github Repo Tools')
    subparsers = parser.add_subparsers(title="Available sub commands",metavar='command')

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('-u',type=str,dest='username',metavar='USERNAME',required=True,help='Github Username')
    base_parser.add_argument('-p',type=str,dest='password',metavar='PASSWORD',help='Github Password')
    base_parser.add_argument('-r',type=str,dest='repo',metavar='REPOSITORY',required=True,help='Target Github Repository')
    # ------------------------------------------------ ls ------------------------------------------------ #

    parser_ls = subparsers.add_parser('ls',parents=[base_parser], help='list commits for repository',description="list commits for github repository")
    parser_ls.add_argument('-m','--message',action='store_true',help='Display Commit Message')
    parser_ls.add_argument('-fh','--fullhash',action='store_true',help='Display the full Commit Hash')
    parser_ls.set_defaults(run=ls)

    # ------------------------------------------------ get ------------------------------------------------ #

    parser_get = subparsers.add_parser('get',parents=[base_parser], help='download commit trees from repository',description="downloads commit trees from a github repository")
    parser_get.add_argument('-c','--commit',type=str,help='Optional hash of commit to target')
    parser_get.add_argument('-v','--verify',action='store_true',help='Verify each commit before download')
    parser_get.set_defaults(run=get)

    args = parser.parse_args()
    if args.password == None:
        password = getpass.getpass("github password:")
    else:
        password = args.password
    session = GitHubSession(args.username,password)
    args.run(session,args)


if __name__ == '__main__':
    main()
