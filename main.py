import os
import re
import time
import json
import argparse


class Node:
    def __init__(self, file_type, data=None):
        self.file_type = file_type
        self.data = data if data is not None else {}


env = os.environ.copy()


def cd(node, name):
    if name == '..':
        if '..' in node.data:
            return node.data['..'], True

        print("cd: ..: No such file or directory")
        return node, False

    if name not in node.data:
        print(f"cd: {name}: No such file or directory")
        return node, False

    if node.data[name].file_type != 'dir':
        print(f"cd: {name}: Not a directory")
        return node, False

    return node.data[name], True


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
    success = True

    for name in names:
        if any(char in name for char in ['.', '/', '\\']):
            print(f"mkdir: cannot create directory '{name}'")
            success = False
            continue

        if name in node.data:
            print(
                f"mkdir: cannot create directory "
                f"'{name}': File exists"
            )
            success = False
            continue

        node.data[name] = Node(
            'dir',
            {'..': node}
        )
    return success

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

def node_to_dict(node):
    result = {
        'file_type': node.file_type,
        'data': {}
    }

    for name, child in node.data.items():
        if name != '..':
            result['data'][name] = node_to_dict(child)

    return result


def dict_to_node(data, parent=None):
    node = Node(data['file_type'], {})

    if parent is not None:
        node.data['..'] = parent

    for name, child_data in data['data'].items():
        node.data[name] = dict_to_node(
            child_data,
            node
        )

    return node


def save_vfs(root, vfs_path):
    os.makedirs(vfs_path, exist_ok=True)

    file_path = os.path.join(vfs_path, 'vfs.json')

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(node_to_dict(root), file, ensure_ascii=False, indent=4)


def load_vfs(vfs_path):
    file_path = os.path.join(vfs_path, 'vfs.json')

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    return dict_to_node(data)


def execute_command(args, node):
    match args:
        case ('exit',):
            print('Exit CLI')
            return node, True, True

        case ('ls',):
            ls(node)
            return node, True, False

        case ('ls', *_):
            print('ls: arguments are not supported')
            return node, False, False

        case ('cd', name):
            node, success = cd(node, name)
            return node, success, False

        case ('cd',):
            print('cd: missing operand')
            return node, False, False

        case ('cd', *_):
            print('cd: too many arguments')
            return node, False, False

        case ('mkdir', *names):
            if not names:
                print('mkdir: missing operand')
                return node, False, False

            success = mkdir(node, names)
            return node, success, False

        case ('pwd',):
            print(pwd(node))
            return node, True, False

        case ('echo', *args):
            print(*args)
            return node, True, False

        case ('date',):
            print(time.asctime())
            return node, True, False

        case ():
            print('Error: empty command')
            return node, False, False

        case (command, *_):
            print(f'{command}: command not found')
            return node, False, False

def repl(node, vfs_path):
    VFS_NAME = 'AmazingVFS'

    while True:
        command = input(f'{VFS_NAME}:{pwd(node)}$ ')

        args = parse(command)

        node, success, should_exit = execute_command(args, node)

        if success:
            save_vfs(node_root(node), vfs_path)

        if should_exit:
            break

def node_root(node):
    while '..' in node.data:
        node = node.data['..']

    return node

def run_script(node, script_path, vfs_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as script:
            for line_number, line in enumerate(script,start=1):
                command = line.strip()

                if not command:
                    continue

                print(f'AmazingVFS:{pwd(node)}$ {command}')

                args = parse(command)
                node, success, should_exit = execute_command(args,node)

                if success:
                    save_vfs(node_root(node), vfs_path)

                if should_exit:
                    return node

                if not success:
                    print(
                        f'Script stopped at line '
                        f'{line_number}: {command}'
                    )
                    return node

    except FileNotFoundError:
        print(f"Error: script file '{script_path}' not found")
        return node

    except OSError as error:
        print(f"Error: cannot read script: {error}")
        return node

    return node

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='AmazingVFS'
    )

    parser.add_argument(
        '--vfs-path',
        required=True,
        help='Physical VFS storage location'
    )

    parser.add_argument(
        '--script',
        required=False,
        help='Path to start script'
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    print('--- AmazingVFS configuration ---')
    print(f'VFS path: {os.path.abspath(args.vfs_path)}')
    print(
        f'Startup script: '
        f'{os.path.abspath(args.script) if args.script else "not found"}'
    )
    print('--------------------------------')
    print()

    root = load_vfs(args.vfs_path)

    if root is None:
        src = Node('dir', {})
        repo = Node('dir',{'src': src})
        root = Node('dir',{'repo': repo})

        src.data['..'] = repo
        repo.data['..'] = root

        save_vfs(root, args.vfs_path)

    if args.script:
        root = run_script(root, args.script, args.vfs_path)

    repl(root, args.vfs_path)


if __name__ == '__main__':
    main()
