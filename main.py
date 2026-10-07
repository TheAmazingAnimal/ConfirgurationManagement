import os
import re
import time
import base64
import zipfile
import argparse
import platform


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

def split_zip_path(path):
    path = path.replace('\\', '/')

    parts = [
        part
        for part in path.split('/')
        if part
    ]

    if any(part in ('.', '..') for part in parts):
        return None

    return parts


def ensure_dir(root, parts):
    node = root

    for part in parts:
        if part not in node.data:
            node.data[part] = Node(
                'dir',
                {'..': node}
            )

        elif node.data[part].file_type != 'dir':
            return None

        node = node.data[part]

    return node


def load_vfs_from_zip(vfs_path):
    if not os.path.isfile(vfs_path):
        raise FileNotFoundError(
            f"VFS ZIP archive '{vfs_path}' not found"
        )

    if not zipfile.is_zipfile(vfs_path):
        raise ValueError(
            f"VFS source '{vfs_path}' is not a ZIP archive"
        )

    root = Node('dir', {})

    with zipfile.ZipFile(vfs_path, 'r') as archive:
        for info in archive.infolist():
            parts = split_zip_path(info.filename)

            if parts is None:
                raise ValueError(
                    f"Invalid path in VFS archive: "
                    f"{info.filename}"
                )

            if not parts:
                continue

            if info.is_dir():
                ensure_dir(root, parts)
                continue

            parent = ensure_dir(root, parts[:-1])

            if parent is None:
                raise ValueError(
                    f"Path conflict in VFS archive: "
                    f"{info.filename}"
                )

            name = parts[-1]

            if name in parent.data:
                raise ValueError(
                    f"Duplicate path in VFS archive: "
                    f"{info.filename}"
                )

            raw_data = archive.read(info)

            encoded_data = base64.b64encode(raw_data).decode('ascii')

            parent.data[name] = Node(
                'file',
                {
                    'content_base64': encoded_data
                }
            )

    return root


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

        case ('date', *_):
            print('date: arguments are not supported')
            return node, False, False

        case ('uname',):
            print(platform.system())
            return node, True, False

        case ('uname', *_):
            print('uname: arguments are not supported')
            return node, False, False

        case ():
            print('Error: empty command')
            return node, False, False

        case (command, *_):
            print(f'{command}: command not found')
            return node, False, False

def repl(node):
    VFS_NAME = 'AmazingVFS'

    while True:
        try:
            command = input(f'{VFS_NAME}:{pwd(node)}$ ')
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        args = parse(command)

        node, success, should_exit = execute_command(args, node)

        if should_exit:
            break


def run_script(node, script_path):
    try:
        with open(script_path, 'r', encoding='utf-8') as script:
            for line_number, line in enumerate(script, start=1):
                command = line.strip()

                if not command or command.startswith('#'):
                    continue

                print(f'AmazingVFS:{pwd(node)}$ {command}')

                args = parse(command)
                node, success, should_exit = execute_command(args, node)

                if should_exit:
                    return node, True

                if not success:
                    print(f'Script stopped at line {line_number}: {command}')
                    return node, False

    except FileNotFoundError:
        print(f"Error: script file '{script_path}' not found")
        return node, False

    except OSError as error:
        print(f"Error: cannot read script: {error}")
        return node, False

    return node, True


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

    vfs_path = os.path.abspath(args.vfs_path)
    script_path = (os.path.abspath(args.script) if args.script else None)

    print('--- AmazingVFS configuration ---')
    print(f'VFS ZIP: {vfs_path}')

    print(f'Startup script: {script_path if script_path else "not specified"}')

    print('VFS mode: in-memory')
    print('--------------------------------')
    print()

    try:
        root = load_vfs_from_zip(vfs_path)
    except (FileNotFoundError, ValueError, zipfile.BadZipFile, OSError) as error:
        print(f'Error: cannot load VFS: {error}')
        return

    if script_path:
        root, success = run_script(root, script_path)

        if not success:
            return

    repl(root)


if __name__ == '__main__':
    main()
