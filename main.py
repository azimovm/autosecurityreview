import os, webbrowser
import shutil
import argparse
import sys
from git import Repo
from urllib.request import urlopen
import json
import difflib
import PySimpleGUI as sg
from export_json_map import extract_annotations, export_json
from generate_report import generate_report
import requests

# TODO: CLEAR button

json_table = {}

team_actual_name = ''


def get_matching_names(user_input_team):
    global team_actual_name
    with open('teams_hierarchy.json') as json_file:
        hierarchy = json.load(json_file)
        for key, value in hierarchy.items():
            if user_input_team.lower() in key.lower():
                team_actual_name = key
                matching_names = value

    return matching_names


def clear():
    if os.path.isdir(path_to_mises):
        os.mkdir(path_to_mises)

    if os.path.isdir("differences"):
        os.mkdir("differences")


path_to_mises = './mises'

layout = [

    [sg.Text('Please enter team name')],

    [sg.InputText('Piton')],

    [sg.Submit(), sg.Cancel()]
]


def clone_repo(repo_name, ssh_key_path=None):
    if not os.path.isdir(path_to_mises):
        os.mkdir(path_to_mises)

    if ssh_key_path:
        git_ssh_identity_file = ssh_key_path
    else:
        git_ssh_identity_file = os.path.expanduser('~/.ssh/id_rsa')

    git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
    os.environ['GIT_SSH_COMMAND'] = git_ssh_cmd
    remote = f"ssh://git@git.swisscom.com:7999/oce/{repo_name}"

    if os.path.exists(f"{path_to_mises}/{repo_name}"):
        print("already existing, pulling...")
        repo = Repo(f"{path_to_mises}/{repo_name}")
        repo.remotes.origin.pull()
    else:
        Repo.clone_from(remote, f"{path_to_mises}/{repo_name}")


def get_diffs(repo_name, tag):
    endpoints_list = []
    repo = Repo(f"{path_to_mises}/{repo_name}")
    commit_prod = repo.commit(tag)
    commit_master = repo.commit("master")
    controller_folder = find_path_by_folder_name("controller", f"./mises/" + repo_name)
    print(controller_folder)
    diff_index = commit_master.diff(commit_prod, controller_folder)
    dir = './differences/' + repo_name
    os.mkdir(dir)

    for diff_item in diff_index:

        # TODO: put meaningful name to txt1 and txt2, like master and target or similar
        txt2 = ""
        txt1 = ""

        if (diff_item.a_blob != None):
            txt1 = diff_item.a_blob.data_stream.read().decode('utf-8')
        if (diff_item.b_blob != None):
            txt2 = diff_item.b_blob.data_stream.read().decode('utf-8')

        all_diff = show_differences(txt2, txt1)

        file_path = diff_item.a_path.split("/")
        fileName = file_path[len(file_path) - 1]

        annotation1 = extract_annotations(txt1)
        annotation2 = extract_annotations(txt2)
        endpoints_list += export_json(annotation1, annotation2, fileName)

        print(dir + '/' + fileName)
        f = open(dir + '/' + fileName, "w")
        f.writelines(all_diff)
        f.close()

    return endpoints_list


def show_differences(s1, s2):
    diff = difflib.ndiff(s1.splitlines(), s2.splitlines())
    str = []
    for line in diff:
        if line.startswith('-') or line.startswith('+'):
            first_char = line[0]
            line = line[1:].lstrip()
            str.append(f"{first_char} {line}\n")
    return str


def find_path_by_folder_name(folder_name, root_folder):
    # TODO: in case there are more than 2 paths found it means this repo is wrongly configured
    #  and we should throw an error

    found_path = ""
    for root, dirs, files in os.walk(root_folder, topdown=False):
        for dir in dirs:
            if dir == folder_name and ("test" not in root):
                found_path = (os.path.join(root, dir))
                found_path = os.path.relpath(found_path, root_folder)

    return found_path


if __name__ == '__main__':

    window = sg.Window('Team name', layout)
    event, values = window.read()
    team_name = str(values[0]).lower()

team_mises = get_matching_names(team_name)

print(team_mises)

if os.path.isdir("differences"):
    shutil.rmtree("differences")

os.mkdir("differences")

json_table["team"] = team_actual_name
json_table["mises"] = []

for mise in team_mises:
    print("Analysing " + mise)
    try:
        clone_repo(mise)
        version = '10.4.0'
    except:
        print("couldn't find prod version!")
        continue
    print(version)
    try:
        json_table['mises'].append({
            'name': mise,
            'endpoints': get_diffs(mise, version),
            'version': version
        })
    except:
        print("Error occurred in appending json table")

with open('json_table.json', 'w') as convert_file:
    convert_file.write(json.dumps(json_table))

generate_report(json_table)
