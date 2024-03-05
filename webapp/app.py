from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock database for demonstration
shells_db = []

@app.route('/shells', methods=['GET'])
def get_shells():
    asset_ids = request.args.getlist('assetIds')
    filtered_shells = [shell for shell in shells_db if shell['id'] in asset_ids] if asset_ids else shells_db
    return jsonify(filtered_shells)

@app.route('/shells', methods=['POST'])
def create_shell():
    shell_data = request.json
    shells_db.append(shell_data)  # Add shell to mock database
    return jsonify(shell_data), 201

if __name__ == '__main__':
    app.run(debug=True)
