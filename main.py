import os
import re
import time


class Node:
    def __init__(self, file_type, data=None):
        self.file_type = file_type
        self.data = data if data is not None else {}


env = os.environ.copy()


def cd(node, name):
    if name == '..':
        if '..' in node.data:
            return node.data['..']

        print("cd: ..: No such file or directory")
        return node

    if name not in node.data:
        print(f"cd: {name}: No such file or directory")
        return node

    if node.data[name].file_type != 'dir':
        print(f"cd: {name}: Not a directory")
        return node

    return node.data[name]


def pwd(node):
    if '..' in node.data:
        parent = node.data['..']

        for name, child in parent.data.items():
            if name != '..' and child is node:
                return pwd(parent) + name + '/'

    return '/'


def ls(node):
    for name in sorted(node.data):
        if name != '..':
            print(name, end=' ')

    print()


def mkdir(node, names):
    for name in names:
        if any(char in name for char in ['.', '/', '\\']):
            print(f"mkdir: cannot create directory '{name}'")
            continue

        if name in node.data:
            print(
                f"mkdir: cannot create directory "
                f"'{name}': File exists"
            )
            continue

        node.data[name] = Node(
            'dir',
            {'..': node}
        )


def parse(command):
    def replace_variable(match):
        name = match.group(1)
        return env.get(name, '')

    command = re.sub(
        r'\$([A-Za-z_][A-Za-z0-9_]*)',
        replace_variable,
        command
    )

    return command.split()


def repl(node):
    VFS_NAME = 'AmazingVFS'

    while True:
        command = input(f'{VFS_NAME}:{pwd(node)}$ ')
        args = parse(command)

        match args:
            case ('exit',):
                print('Exit CLI')
                return

            case ('ls',):
                ls(node)

            case ('ls', *_):
                print('ls: arguments are not supported')

            case ('cd', name):
                node = cd(node, name)

            case ('cd',):
                print('cd: missing operand')

            case ('cd', *_):
                print('cd: too many arguments')

            case ('mkdir', *names):
                if not names:
                    print('mkdir: missing operand')
                else:
                    mkdir(node, names)

            case ('pwd',):
                print(pwd(node))

            case ('echo', *args):
                print(*args)

            case ('date',):
                print(time.asctime())

            case ():
                print('Error: empty command')

            case (command, *_):
                print(f'{command}: command not found')


src = Node('dir', {})

repo = Node(
    'dir',
    {
        'src': src
    }
)

root = Node(
    'dir',
    {
        'repo': repo
    }
)

src.data['..'] = repo
repo.data['..'] = root

repl(root)