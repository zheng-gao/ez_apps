# https://docs.pyfilesystem.org/en/latest/reference/errors.html

class iNode:
    def __init__(self, name: str, parent=None, is_file=False, content=None):
        self.name = name
        self.is_file = is_file
        self.content = content
        self.parent = parent
        self.inodes = dict()  # <string, iNode>

    def __str__(self):
        df = "f" if self.is_file else "d"
        return f"{df}  {self.name}"

    def get_inode(self, path: str):
        node = self
        for d in path.split("/"):
            if d:
                if d == "..":
                    node = node.parent
                elif d not in node.inodes:
                    raise FileNotFoundError(path)
                else:
                    node = node.inodes[d]
        return node


class FileSystem:
    def __init__(self):
        self.root = iNode("/")
        self.current = self.root

    def get_inode(self, path: str):
        return self.root.get_inode(path) if path.startswith("/") else self.current.get_inode(path)

    def basename(self, path: str):
        return path.split("/")[-1]

    def dirname(self, path:str):
        directories = "/".join(path.split("/")[:-1:])
        return  "/" + directories if path.startswith("/") else directories

    def pwd(self):
        # print(self.current.path)
        node = self.current
        directories = list()
        while node != self.root:
            directories.append(node.name)
            node = node.parent
        print(self.root.name + "/".join(directories[::-1]))

    def cd(self, path):
        self.current = self.get_inode(path)

    def ls(self, path: str = ""):
        inode = self.get_inode(path)
        result = [inode] if inode.is_file else list(inode.inodes.values())
        for r in result:
            print(r)

    def rm(self, path: str):
        dir_node = self.get_inode(self.dirname(path))
        if dir_node.is_file:
            raise DirectoryExpected
        del dir_node.inodes[self.basename(path)]

    def mkdir(self, path: str, create_intermediate_directories=False):
        if create_intermediate_directories:
            node = self.root if path.startswith("/") else self.current
            for d in path.split("/"):
                if d:
                    if d not in node.inodes:
                        node.inodes[d] = iNode(d, node)
                    node = node.inodes[d]
        else:
            dir_path = self.dirname(path)
            dir_node = self.get_inode(dir_path)
            if dir_node.is_file:
                raise DirectoryExpected(dir_path)
            basename = self.basename(path)
            dir_node.inodes[basename] = iNode(name=basename, parent=dir_node)

    def touch(self, path: str):
        dir_path = self.dirname(path)
        dir_node = self.get_inode(dir_path)
        if dir_node.is_file:
            raise DirectoryExpected(dir_path)
        basename = self.basename(path)
        dir_node.inodes[basename] = iNode(name=basename, parent=dir_node, is_file=True)

    def cat(self, path: str):
        inode = self.get_inode(path)
        if not inode.is_file:
            raise FileExpected(path)
        print(inode.content)

    def echo_to(self, path: str, content: str):
        basename = self.basename(path)
        dir_node = self.root.get_inode(self.dirname(path))
        if basename not in dir_node.inodes:
            dir_node.inodes[basename] = iNode(name=basename, parent=dir_node, is_file=True, content=content)
        else:
            node = dir_node.inodes[basename]
            if not node.is_file:
                raise FileExpected(path)
            node.content = node.content + content if node.content else content


"""
fs = FileSystem()
fs.mkdir("/var/tmp", True)
fs.echo_to("/var/tmp/test", "hello world")
fs.cd("/var/tmp")
fs.pwd()
fs.ls()
fs.cat("test")
fs.cd("../..")
fs.pwd()
fs.mkdir("/home")
for user in ["user_1", "user_2", "user_3"]:
    fs.mkdir(f"/home/{user}")
    fs.touch(f"/home/{user}/.profile")
    fs.echo_to(f"/home/{user}/.profile", f"ID={user}")
fs.ls("/")
fs.cd("/home")
fs.pwd()
fs.ls()
fs.cd("user_1")
fs.pwd()
fs.ls()
fs.cat(".profile")
fs.cat("/home/user_3/.profile")
fs.ls("/home/user_3")
fs.rm("/home/user_3")
fs.cd("..")
fs.pwd()
fs.ls()
fs.cd("..")
fs.pwd()

"""

"""
Distributed system: HDFS, Spark, Tachyon

save part of the tree to other hosts: /home/user_1

Turn it into service: REST API
"""

