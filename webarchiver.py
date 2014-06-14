from __future__ import print_function

import argparse
from collections import deque
import csv
import os
import string
import subprocess
import sys

from pocket import Pocket
import yaml

__author__ = 'krunic'

_DESTINATION_ARGUMENT = "destination_dir"
_FILE_ARGUMENT = "instapaper_csv"
_DELETE_POCKET = "delete_pocket"
_POCKET = "pocket"
_ERROR_LIST = "unprocessed_url_list"
_POCKET_CONSUMER_KEY = "pockat.consumer.key"
_REDIRECT_URI = "pocket.redirect.uri"
_POCKET_ACCESS_TOKEN = "pocket.access.token"
_CONFIG_FILE = "config.yaml"

def convert_to_valid_filename(topic):
    """
        Convert python path to valid filename

        :param topic: Topic to use

        :return: Valid filename, with all non-ASCII characters dropped from it
    """
    valid_filename_chars = "-_.() {letters}{digits}".format(letters=string.ascii_letters,
                                                            digits=string.digits)
    return ''.join(ch for ch in topic if ch in valid_filename_chars)

def get_pocket_instance():
    """
        Get Initialized pocket instance

        :return: Pocket instance
    """
    with open(_CONFIG_FILE) as f:
        yaml_config = f.read()

    config = yaml.load(yaml_config)
    return Pocket(config[_POCKET_CONSUMER_KEY], config[_POCKET_ACCESS_TOKEN])

def create_webarchive(url, destination_dir, topic):
    """
        Create webarchive

        :param url: URL to extract
        :param destination_dir: Destination dir to use
        :param topic: Topic to use

        :return: return code of the command
    """

    filename = convert_to_valid_filename(topic) + '.webarchive'
    destination_filename = os.path.join(destination_directory, filename)

    command = "webarchiver -url '{URL}' -output '{FILE}'".format(URL=url,
                                                             FILE=destination_filename)

    print('Calling:\n', command)
    return subprocess.call(command, shell=True)


def process_instapaper(csv_file, destination_directory, unprocessed_url_list):
    """
        Process instapaper

        :param csv_file: Instapaper export CSV file
        :param destination_directory: Destination directory
        :param unprocessed_url_list: File in which we should store errors
    """

    with open(unprocessed_url_list, 'wb') as error_file, open(csv_file, 'rb') as instapaper_file:
        reader = csv.reader(instapaper_file)
        writer = csv.writer(error_file)

        # Skip header
        reader.next()

        for row in reader:

            try:
                try:
                    url = row[0]
                    topic = row[1]
                except:
                    error_message = 'Error reading file {FILE}, line {LINE}'.format(FILE=csv_file,
                                                                                    LINE=reader.line_num)

                    print(error_message, file=sys.stderr)
                    continue

                return_code = create_webarchive(url, destination_directory, topic)

                # Add error to the unprocessed file list
                if return_code != 0:
                    writer.writerow([url, topic])
                    print("Error {CODE} while extracting[{URL}]".format(CODE=return_code,
                                                                        URL=url), file=sys.stderr)


            except csv.Error as e:
                print('Error reading file {FILE}, line {LINE}: {EXCEPTION}'.format(FILE=csv_file,
                                                                                   LINE=reader.line_num,
                                                                                   EXCEPTION=e),
                      file=sys.stderr)


def process_pocket(destination_directory, unprocessed_url_list, delete_pocket):
    """
        Process Pocket

        :param destination_directory: Destination directory
        :param unprocessed_url_list: File in which we should store errors
        :param delete_pocket: Should article be deleted from pocket
    """
    pocket_instance = get_pocket_instance()

    with open(unprocessed_url_list, 'wb') as error_file:
        writer = csv.writer(error_file)

        articles = pocket_instance.get()

        for article in articles[0]['list'].values():
            url = article['resolved_url']
            title = article['resolved_title']

            return_code = create_webarchive(url, destination_directory, title)

            if return_code == 0:
                # If we have successfully downloaded, delete from pocket
                if delete_pocket:
                    pocket_instance.delete(article['resolved_id']).commit()
            else:
                # Otherwise, add error to the unprocessed file list and leave it on pocket
                writer.writerow([url, title])
                print("Error {CODE} while extracting[{URL}]".format(CODE=return_code, URL=url), file=sys.stderr)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Use Instapaper CSV export file to convert all pages to webarchive',
                                     epilog='Note that webarchiver (https://github.com/newzealandpaul/webarchiver/) must be installed and in path')

    # We would use named argument so prepend -- to it
    parser.add_argument("-{PATH}".format(PATH=_DESTINATION_ARGUMENT),
                        type=str,
                        help='Path to the destination directory to use. Must already exist',
                        required=True)

    parser.add_argument("-{FILE}".format(FILE=_FILE_ARGUMENT),
                        type=str,
                        help='Path to the file to use',
                        required=False)

    parser.add_argument("-{ERROR_FILE}".format(ERROR_FILE=_ERROR_LIST),
                        type=str,
                        help='If URL fails to be processed, save it to this file (for future processing)',
                        required=True)

    parser.add_argument("-{POCKET}".format(POCKET=_POCKET),
                        help='Use pocket instead of instapaper',
                        required=False,
                        action='store_true')

    parser.add_argument("-{DELETE_POCKET}".format(DELETE_POCKET=_DELETE_POCKET),
                        help='Delete article from archive after you download it from Pocket',
                        required=False,
                        action='store_true')

    args = vars(parser.parse_args())

    destination_directory = args[_DESTINATION_ARGUMENT]
    unprocessed_url_list = args[_ERROR_LIST]
    delete_pocket = args[_DELETE_POCKET]

    if (not _FILE_ARGUMENT in args) and (not _POCKET in args):
        print("Must specify Instapaper of Pocket style", file=sys.stderr)
        sys.exit(1)

    if _POCKET in args:
        process_pocket(destination_directory, unprocessed_url_list, delete_pocket)
    else:
        # Instapaper
        csv_file = args[_FILE_ARGUMENT]
        process_instapaper(csv_file, destination_directory, unprocessed_url_list)
