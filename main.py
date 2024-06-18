import os
import shutil
from git import Repo
import json
import difflib
import PySimpleGUI as sg
from export_json_map import extract_annotations, export_json
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

json_table = {}
json_raw = {}


team_actual_name = ''


def get_mise_name(team_name):
    global team_actual_name
    with open('teams_hierarchy.json') as json_file:
        hierarchy = json.load(json_file)
        for key, value in hierarchy.items():
            if team_name.lower() in key.lower():
                team_actual_name = key
                matching_names = value

    return matching_names


def clear():
    if os.path.isdir(path_to_mises):
        os.mkdir(path_to_mises)

    if os.path.isdir("differences"):
        os.mkdir("differences")


path_to_mises = './mises'


# layout = [
#
#     [sg.Text('Please enter team name')],
#
#     [sg.InputText('B2B_Piton')],
#
#     [sg.Submit(), sg.Cancel()]
# ]


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
    controller_folder = find_path_by_folder_name(
        "controller", f"./mises/" + repo_name)
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
    found_path = ""
    for root, dirs, files in os.walk(root_folder, topdown=False):
        for dir in dirs:
            if dir == folder_name and ("test" not in root):
                found_path = (os.path.join(root, dir))
                found_path = os.path.relpath(found_path, root_folder)

    return found_path


def get_response_data(path):
    try:
        with open(path, 'r') as raw_data:
            content = raw_data.read()
        return json.loads(content)
    except Exception as e:
        print(f"File path couldn't be found {path}: {e}")


def clone_repo_github(repo_title):
    if not os.path.isdir(path_to_mises):
        os.mkdir(path_to_mises)

    remote = f"https://github.com/azimovm/{repo_title}.git"

    if os.path.exists(f"{path_to_mises}/{repo_title}"):
        print("already existing, pulling...")
        repo = Repo(f"{path_to_mises}/{repo_title}")
        repo.remotes.origin.pull()
    else:
        Repo.clone_from(remote, f"{path_to_mises}/{repo_title}")


@app.route('/report-data', methods=['GET'])
def get_report_data():
    return jsonify(get_response_data("./json_table.json"))


@app.route('/config-data', methods=['POST'])
def properties_reciver():
    data = request.get_json()
    mise = data.get('mise')
    version = data.get('version')
    print(f"Received mise: {mise}, version: {version}")
    if mise and version:
        execute_scan(mise, version)
        return jsonify({"message": "Data received and script started successfully"})
    else:
        return jsonify({"error": "Mise or version not provided"}), 400


def execute_scan(mise, version):

    test_mise = get_mise_name(mise)

    print(test_mise)
    if os.path.isdir("differences"):
        shutil.rmtree("differences")

    os.mkdir("differences")

    json_table["mises"] = []
    for mise in test_mise:
        print("Analysing " + mise)
        try:
            clone_repo(mise)
            version = version

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


if __name__ == '__main__':
    # Start the Flask server after generating the JSON data
    app.run(host='127.0.0.1', port=5000)
