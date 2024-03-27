import os
import json
import webbrowser


def generate_report(json_data):
    if not os.path.isdir("report"):
        os.mkdir("report")

    print("Report directory exists or created successfully.")

    data = json.loads(json_data)

    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report</title>
            <style>
                /* Define your CSS styles here */
                .blue {{ color: blue; }}
                .green {{ color: green; }}
                .red {{ color: red; }}
                .orchid {{ color: orchid; }}
            </style>
        </head>
        <body>
            <h1>{data['team']}</h1>
    """

    for mise in data['mises']:
        html += f'<h2>{mise["name"]} ({mise["version"]})</h2>'
        html += '<table border="1">'
        html += '''
            <thead>
                <tr>
                    <th>Controller Name</th>
                    <th>Function Name</th>
                    <th>Method</th>
                    <th>Path</th>
                    <th>Annotation</th>
                    <th>Data Classification</th>
                    <th>Use Case</th>
                </tr>
            </thead>
            <tbody>
        '''

        for endpoint in mise['endpoints']:
            html += '<tr>'
            html += f'<td>{endpoint["controllerName"]}</td>'
            html += f'<td>{endpoint["functionName"]}</td>'
            html += f'<td>{endpoint["method"]}</td>'
            html += f'<td>{endpoint["path"]}</td>'
            html += f'<td>{endpoint["annotation"]}</td>'
            html += f'<td>{endpoint["dataClassification"]}</td>'
            html += f'<td>{endpoint["useCase"]}</td>'
            html += '</tr>'

        html += '''
            </tbody>
        </table>
        '''

    html += """
        </body>
        </html>
    """

    output_file_path = os.path.realpath('report/output.html')
    print(f"Output file path: {output_file_path}")

    with open(output_file_path, 'w') as f:
        f.write(html)

    print("HTML report generated successfully.")

    webbrowser.open('file://' + output_file_path)