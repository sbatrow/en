#!/usr/bin/env python3
'''
Copyright (C) 2020  HCTools

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from sys import stdin, stdout, stderr

from argparse import ArgumentParser
from pathlib import Path

from base64 import b64decode
from base64 import b64encode

from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import unpad

DEFAULT_FILE_EXTENSION = '.tmt'

# passwords to derive the key from
PASSWORDS = {
    '.tut': b'fubvx788b46v',
    '.sks': b'dyv35224nossas!!',
    '.tmt': b'fubvx788B4mev',
}

# some utility functions



def human_bool_to_bool(human_bool):
    return 'y' in human_bool

def main():
    # parse arguments
    parser = ArgumentParser()
    parser.add_argument('file', help='file to decrypt')

    output_args = parser.add_mutually_exclusive_group()
    output_args.add_argument('--output', '-o', help='file to output to')
    output_args.add_argument('--stdout', '-O', action='store_true', help='output to stdout', default=True)

    args = parser.parse_args()

    # open file
    encrypted_contents = open(args.file, 'r').read()

    # determine the file's extension
    file_ext = Path(args.file).suffix
    
    if file_ext not in PASSWORDS:
        warn(f'Unknown file extension, defaulting to {DEFAULT_FILE_EXTENSION}')
        file_ext = DEFAULT_FILE_EXTENSION

    # split the file
    split_base64_contents = encrypted_contents.split('.')

    if len(split_base64_contents) != 3:
        raise ValueError('Unsupported file.')

    split_contents = list(map(b64encode, split_base64_contents))

    # derive the key
    decryption_key = PBKDF2(PASSWORDS[file_ext], split_contents[0], hmac_hash_module=SHA256)

    # decrypt the file
    cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=split_contents[1])
    decrypted_contents = cipher.decrypt_and_verify(split_contents[2][:-16], split_contents[2][-16:])

    # decide where to write contents
    if args.output:
        output_file_path = Path(args.output)

        # check if the file exists
        if output_file_path.exists() and output_file_path.is_file():
            # check if the user agrees to overwrite it
            if not human_bool_to_bool(ask(f'A file named "{args.output}" already exists. Overwrite it? (y/n)')):
                # if user doesn't, quit
                exit(0)
        
        # write the contents to the file
        output_file = open(output_file_path, 'wb')
        output_file.write(decrypted_contents)
    elif args.stdout:
        # convert the config to UTF-8
        config = decrypted_contents.encode('utf-8')

        # write it to stdout
        stdout.write(config)
        stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        error(err)
