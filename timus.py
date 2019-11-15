#!/usr/bin/env python3

import os
import getpass
import requests
from lxml import html 

def get_judge_number(judge_id):
    """ I GUESS """
    judge_number = judge_id
    while len(judge_number) > 0 and not judge_number.isdigit():
        judge_number = judge_number[:-1]
    return judge_number

def get_problem_id_from_url(url):
    pos = url.find('num=')
    return url[pos + 4:]

def get_submission_id_from_url(url):
    patt = 'getsubmit.aspx/'
    pos = url.find(patt)
    return url[pos + len(patt):]

def remove_ext(s):
    pos = s.find('.')
    return s[:pos]

def get_submissions_list(session, judge_number, accepted_only = False):
    url = 'http://acm.timus.ru/status.aspx'
    params = {
        'author': judge_number,
        'count': 100 
    }
    if accepted_only:
        params['status'] = 'accepted'

    submissions = []
    while True:
        print('getting submissions from {}, with params = {}'.format(url, params))
        response = session.get(url, params = params)
        tree = html.fromstring(response.text)
        table = tree.xpath('.//table[@class="status"]')
        rows = table[0].xpath('.//tr')
        last_submission_id = None
        for row in rows:
            if (not 'even' in row.classes) and (not 'odd' in row.classes):
                continue
            submission_url = row.xpath('.//td[@class="id"]/a')[0].attrib['href']
            problem_url = row.xpath('.//td[@class="problem"]/a')[0].attrib['href']
            message = 'Accepted'
            accepted = len(row.xpath('./td[@class="verdict_ac"]')) > 0
            if not accepted:
                message = row.xpath('.//td[@class="verdict_rj"]')[0].text
            submissions.append({
                'problem_url': problem_url,
                'submission_url': submission_url,
                'verdict': message
            })
            last_submission_id = remove_ext(get_submission_id_from_url(submission_url))
        footer = tree.xpath('.//td[@class="footer_right"]/a')
        cont = False
        for element in footer:
            if element.text != 'To the top':
                cont = True
        if not cont:
            break
        assert(last_submission_id != None)
        params['from'] = last_submission_id

    return submissions 

def get_submission_code(session, judge_id, password, url):
    data = {
        'Action': 'getsubmit',
        'JudgeId': judge_id,
        'Password': password
    }
    response = session.post(url, data)
    return response.text

if __name__ == '__main__':
    judge_id = input('Judge ID: ')
    password = getpass.getpass('Password: ')
    accepted_only = bool(input('Accepted only: '))
    session = requests.session()
    print('getting submissions ...')
    submissions = get_submissions_list(session, get_judge_number(judge_id), accepted_only)
    print('found {} submissions'.format(len(submissions)))
    solutions_folder = 'timus_solutions'
    if not os.path.exists(solutions_folder):
        os.makedirs(solutions_folder)
    for submission in submissions:
        submission_id = get_submission_id_from_url(submission['submission_url'])
        problem_id = get_problem_id_from_url(submission['problem_url'])
        print('problem id: {}, submission id: {}'.format(problem_id, submission_id))
        code = get_submission_code(session, judge_id, password, 'http://acm.timus.ru/' + submission['submission_url'])
        content = ""
        content = content + '// {}\n'.format(submission['problem_url'])
        content = content + '// {}\n'.format(submission['verdict'])
        content = content + '\n'
        content = content + code
        with open('{}/{}-{}'.format(solutions_folder, problem_id, submission_id), 'w', encoding='utf-8') as f:
            f.write(content)
