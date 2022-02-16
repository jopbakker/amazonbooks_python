#!/usr/bin/env python3

import argparse
import logging
import sys
import os
import lxml
import requests
import csv
from bs4 import BeautifulSoup
from asyncore import read
from multiprocessing.spawn import old_main_modules



parser = argparse.ArgumentParser()

parser.add_argument("-a", "--author",
                    dest="check_author",
                    help="Custom author check - [Default: all]",
                    default='all',
                    action='store')
parser.add_argument("-aL", "--author-list",
                    dest="author_list",
                    help="Custom filename for the csv file containing authors and urls - [Default: authors.csv]",
                    default='authors.csv',
                    action='store')
parser.add_argument("--author-file-folder",
                    dest="author_files_folder",
                    help="Custom authors file location - [Default: authors]",
                    default='authors',
                    action='store')
parser.add_argument("--log-level",
                    dest="log_level",
                    help="Set the level of logs to show (Options: DEBUG, INFO, WARNING, ERROR, CRITICAL) - [Default: WARNING]",
                    default='WARNING',
                    action='store')

requiredNamed = parser.add_argument_group('required named arguments')

requiredNamed.add_argument("-Pu", "--pushover-user-token",
                    dest="user_token",
                    help="Pushover user token",
                    required=True,
                    action='store')
requiredNamed.add_argument("-Pa", "--pushover-api-token",
                    dest="api_token",
                    help="Pushover API token",
                    required=True,
                    action='store')

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=args.log_level.upper())

def read_input_csv(author_list):
    logging.info(f"Parsing the data from the author-list file: {author_list}")
    with open(author_list, 'r') as file:
        reader = csv.DictReader(file)
        author_list = []
        for row in reader:
            author_list.append(row)
    
    return author_list

def download_html(author_url):
    logging.info(f"Downloading the HTML code from {author_url}")
    raw_html = requests.get(author_url).text
    
    return raw_html

def read_html(input_html):
    soup = BeautifulSoup(input_html, 'lxml')
    logging.debug(f"Extracting specified tags from the HTML file {input_html}")
    books_html_tags = soup.find_all('span', {"class": "a-size-medium"})
    logging.debug(f"Found the following tags: {books_html_tags}")
    books = []
    for book in books_html_tags:
        books.append(book.text.strip())

    books.sort()
    return books

def read_author_file(author, author_files_folder):
    if not os.path.isfile(author_files_folder+"/"+author):
        logging.error(f"No author file found. Creating new file.")
        open(author_files_folder+"/"+author, 'a').close()

    logging.debug(f"Reading the file: {author_files_folder}/{author}")
    with open(author_files_folder+"/"+author, 'r') as file:
        known_books_by_author = [line.rstrip() for line in file]

    known_books_by_author.sort()
    return known_books_by_author

def compare_author_books(author, author_files_folder, author_url, input_html):
    existing_author_books = read_author_file(author, author_files_folder)
    new_author_books = read_html(input_html)
    logging.info(f"Comparing the known books for {author} against the books found on {author_url}")
    new_books = list(set(new_author_books) - set(existing_author_books))
    
    return new_books

def send_pushover_message(author, new_books, user_token, api_token):
    logging.info(f"Sending pushover message: {new_books} by {author}")
    new_books = " | \n".join(new_books)
    payload = {"title": author, "message": new_books, "user": user_token, "token": api_token }
    requests.post('https://api.pushover.net/1/messages.json', data=payload, headers={'User-Agent': 'Python'})

def do_all(author, author_url, author_files_folder,user_token, api_token):
    raw_html = download_html(author_url)
    new_books = compare_author_books(author, author_files_folder, author_url, raw_html)

    if new_books:
        with open(author_files_folder+"/"+author, 'a') as file:
            logging.info(f"Writing new books for {author} to {author_files_folder}/{author}")
            for book in new_books:
                logging.debug(f"Adding {book} to {author_files_folder}/{author}")
                file.write(book + "\n")
        send_pushover_message(author, new_books, user_token, api_token)
    else:
        logging.warning(f"No new books found for {author}")


def main():
    logging.info(f"Executing the script with the following arguments: {sys.argv[1:]}")
    author = args.check_author
    author_files_folder = args.author_files_folder
    author_list = read_input_csv(args.author_list)

    if author == "all":
        for row in author_list:
            author = row["author"]
            author_url = row["url"]
            do_all(author, author_url, author_files_folder, args.user_token, args.api_token)
    else:
        for row in author_list:
            if row["author"] == author:
                author_url = row["url"]
                do_all(author, author_url, author_files_folder, args.user_token, args.api_token)
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt Detected.")
        print("Exiting...")
        exit(0)
