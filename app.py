from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/report-data', methods=['GET'])
def get_report_data():
    # Here you can put the code to generate your JSON data
    # For example, if you already have json_table.json file, you can read it and return its content
    with open('json_table.json', 'r') as json_file:
        json_data = json_file.read()

    return jsonify(json_data)

if __name__ == '__main__':
    app.run(debug=True)  # Run the application in debug mode
