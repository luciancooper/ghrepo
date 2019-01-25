import os
from .util import iter_reduce,cli_color,splitpath

__all__ = ["CommitFile","ChangedCommitFile","CommitTree"]

class CommitFile():
    def __init__(self,path,sha):
        self.sha = sha
        self.path = splitpath(path)

    def __str__(self):
        return os.path.join(*self.path)

    def inpath(self,path):
        if len(self.path)-1 < len(path):
            return False
        for p1,p2 in zip(self.path,path):
            if p1 != p2:
                return False
        return True

    @property
    def treestr(self):
        return str(self)

    def __len__(self):
        return len(self.path)

    @property
    def filename(self):
        return self.path[-1]

    @property
    def filetype(self):
        """returns file extension"""
        try:
            file = self.path[-1]
            i = file.rindex('.')
            return file[i+1:]
        except ValueError:
            return ''

    @staticmethod
    def _cmp_(p1,p2):
        # [-1 : p1 < p2] [1 : p1 > p2]
        for d1,d2 in zip(p1[:-1],p2[:-1]):
            if d1 == d2:
                continue
            return -1 if d1 < d2 else 1
        n1,n2 = len(p1),len(p2)
        if n1 != n2:
            return -1 if n1 < n2 else 1
        f1,f2 = p1[-1],p2[-1]
        return 1 if f1 > f2 else -1 if f1 < f2 else 0

    def cmp(self,other):
        # _cmp_ where p1=self & p2=other
        if not isinstance(other,CommitFile):
            raise ValueError("Cannot compare to object of type {}".format(type(other).__name__))
        return self._cmp_(self.path,other.path)

    def __eq__(self,other):
        # self == other
        if not isinstance(other,CommitFile):
            return False
        return self._cmp_(self.path,other.path) == 0

    def __ne__(self,other):
        # self != other
        if not isinstance(other,CommitFile):
            return True
        return self._cmp_(self.path,other.path) != 0

    def __lt__(self, other):
        # self  < other
        if not isinstance(other,CommitFile):
            raise ValueError("Cannot compare to object of type {}".format(type(other).__name__))
        return self._cmp_(self.path,other.path) == -1

    def __le__(self, other):
        # self <= other
        if not isinstance(other,CommitFile):
            raise ValueError("Cannot compare to object of type {}".format(type(other).__name__))
        return self._cmp_(self.path,other.path) <= 0

    def __gt__(self, other):
        # self > other
        if not isinstance(other,CommitFile):
            raise ValueError("Cannot compare to object of type {}".format(type(other).__name__))
        return self._cmp_(self.path,other.path) == 1

    def __ge__(self, other):
        # self >= other
        if not isinstance(other,CommitFile):
            raise ValueError("Cannot compare to object of type {}".format(type(other).__name__))
        return self._cmp_(self.path,other.path) >= 0


def changestr(additions,deletions):
    changes = ((cli_color("+%i"%additions,"32;1"),) if additions>1 else ())+((cli_color("-%i"%deletions,"31;1"),) if deletions>1 else ())
    return " [%s]"%",".join(changes) if len(changes) > 0 else ""




class ChangedCommitFile(CommitFile):
    def __init__(self,json):
        super().__init__(json["filename"],json["sha"])
        self.status = json["status"]
        self.additions = json["additions"]
        self.deletions = json['deletions']
        self.changes = json['changes']
        if self.status == 'renamed':
            self.prevpath = json['previous_filename']

    # cyan = 36
    # yellow = 33
    # green = 32
    # red = 31
    @property
    def treestr(self):
        path = str(self)
        if self.status == "added":
            return "{} [{}]".format(cli_color(path,32),cli_color("+%i"%self.additions,"32;1"))
        if self.status == "removed":
            return "{} [{}]".format(cli_color(path,31),cli_color("-%i"%self.deletions,"31;1"))
        if self.status == "modified":
            return cli_color(path,33) + changestr(self.additions,self.deletions)
        if self.status == "renamed":
            return "{} ({}){}".format(cli_color(path,33),cli_color(self.prevpath,"33;1"),changestr(self.additions,self.deletions))
        raise ValueError("Unknown ChangedCommitFile type {}".format(self.status))


def maketree(paths,lvl=0):
    i,n = 0,len(paths)
    while i < n and len(paths[i])-lvl == 1:
        i=i+1
    if i == n:
        return ["├── {}".format(f.treestr) for f in paths[:-1]]+["└── {}".format(paths[-1].treestr)]
    ftree = ["├── {}".format(f.treestr) for f in paths[:i]]
    groups = [i]+[x for x in range(i+1,n) if paths[x].path[lvl]!=paths[x-1].path[lvl]]
    for i1,i2 in iter_reduce(groups):
        ftree += ["├── {}".format(paths[i1].path[lvl])]+["│   {}".format(f) for f in maketree(paths[i1:i2],lvl+1)]
    i = groups[-1]
    return ftree + ["└── {}".format(paths[i].path[lvl])]+["    {}".format(f) for f in maketree(paths[i:],lvl+1)]



class CommitTree():
    def __init__(self,files,repo,sha,date,message,additons,deletions):
        self.files = files
        self.repo = repo
        self.hash = sha
        self.date = date
        self.message= message
        self.additions = additons
        self.deletions = deletions

    def __getitem__(self,k):
        if hasattr(self,k):
            return getattr(self,k)
        raise KeyError("CommitTree has no key '{}'".format(k))

    def tree(self):
        head = ["{} Files{}".format(len(self.files),changestr(self.additions,self.deletions))]
        return "\n".join(head+maketree(self.files))
