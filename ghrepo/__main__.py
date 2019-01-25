
#!/usr/bin/env python

import sys,re,os
import pydecorator
from .session import GHSession
from .util import cmp_iso

# ----------- Sort Commits ----------- #

@pydecorator.mergesort(duplicate_values=True)
def sort_commits(a,b):
    return cmp_iso(a['date'],b['date'])

# -------------- Commands -------------- #

def _ls(session,args):
    from .util import ls_commit_format
    commits = session.allcommits()
    print("{} Commits in repository '{}'".format(len(commits),session.repo),file=sys.stderr)
    for c in sort_commits(commits):
        print(ls_commit_format(c,args.format),file=sys.stdout)


def _get(session,args):
    from .util import get_commit_format
    if args.commit == None:
        commits = session.allcommits()
        print("{} Commits in repository '{}'".format(len(commits),session.repo),file=sys.stderr)
    else:
        commits = [session.commitinfo(args.commit)]
    for c in commits:
        dirname = get_commit_format(c,args.format)
        endpath = os.path.join(os.getcwd(),dirname)
        if os.path.exists(endpath):
            print("Cannot download commit from '{}' repository, '{}' already exists in this directory".format(session.repo,dirname),file=sys.stderr)
            continue
        if args.verify and input("Download '{}' (y/n) [y]:".format(dirname)).lower() != 'y':
            continue
        print("Downloading '{}'".format(dirname),file=sys.stderr)
        session.download_commit(c['hash'],endpath)

def _tree(session,args):
    from .util import ls_commit_format,cli_color
    ctree = session.commit_tree(args.commit,filetype=args.filetype,exclude=args.exclude,include=args.include)
    print(cli_color(ls_commit_format(ctree,args.format),36),file=sys.stdout)
    print(ctree.tree(),file=sys.stdout)

def _cfile(session,args):
    from .util import ls_commit_format,cli_color
    from .tree import changestr,maketree
    info,cfiles = session.commitfiles(args.commit)
    ctree = ["{} Files{}".format(len(cfiles),changestr(info['additions'],info['deletions']))]+maketree(cfiles)
    print(cli_color(ls_commit_format(info,args.format),36),file=sys.stdout)
    print("\n".join(ctree),file=sys.stdout)


def main():
    import argparse,getpass
    parser = argparse.ArgumentParser(prog='ghrepo',description='Github Repo Tools')
    subparsers = parser.add_subparsers(title="Available sub commands",metavar='command')

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('-u',type=str,dest='username',metavar='USERNAME',required=True,help='Github Username')
    base_parser.add_argument('-p',type=str,dest='password',metavar='PASSWORD',help='Github Password')
    base_parser.add_argument('-r',type=str,dest='repo',metavar='REPOSITORY',required=True,help='Target Github Repository')
    # ------------------------------------------------ ls ------------------------------------------------ #

    parser_ls = subparsers.add_parser('ls',parents=[base_parser], help='list commits for repository',description="list commits for github repository")
    parser_ls.add_argument('-f','--format',type=str,default="%h %d %t\n%M",help='Display format for each commit')
    parser_ls.set_defaults(run=_ls)

    # ------------------------------------------------ get ------------------------------------------------ #

    parser_get = subparsers.add_parser('get',parents=[base_parser], help='download commit trees from repository',description="downloads commit trees from a github repository")
    parser_get.add_argument('-c','--commit',type=str,help='Optional hash of commit to target')
    parser_get.add_argument('-v','--verify',action='store_true',help='Verify each commit before download')
    parser_get.add_argument('-f','--format',type=str,default="%r-%d_%t_%h",help='Naming format for downloaded directory')
    parser_get.set_defaults(run=_get)

    # ------------------------------------------------ cfile ------------------------------------------------ #

    parser_cfile = subparsers.add_parser('cfile',parents=[base_parser], help='print commit file changes',description="commit file changes")
    parser_cfile.add_argument('-c','--commit',type=str,required=True,help='hash of commit to get changed files for')
    parser_cfile.add_argument('-f','--format',type=str,default="%r-%d_%t_%h",help='display format for tree header')
    parser_cfile.set_defaults(run=_cfile)

    # ------------------------------------------------ tree ------------------------------------------------ #

    parser_tree = subparsers.add_parser('tree',parents=[base_parser], help='print commit as tree',description="commit file trees")
    parser_tree.add_argument('-c','--commit',type=str,required=True,help='hash of commit for file tree')
    parser_tree.add_argument('-f','--format',type=str,default="%r-%d_%t_%h",help='display format for tree header')
    parser_tree.add_argument('-ft','--filetype',dest='filetype',action='append',metavar='filetype',help='file type filter')
    parser_tree_paths = parser_tree.add_mutually_exclusive_group(required=False)
    parser_tree_paths.add_argument('-exc','--exclude',dest='exclude',action='append',metavar='path',help='paths to exclude from tree')
    parser_tree_paths.add_argument('-inc','--include',dest='include',action='append',metavar='path',help='paths to include in tree')
    parser_tree.set_defaults(run=_tree)


    args = parser.parse_args()
    if args.password == None:
        password = getpass.getpass("github password:")
    else:
        password = args.password
    session = GHSession(args.username,password,args.repo)
    args.run(session,args)
