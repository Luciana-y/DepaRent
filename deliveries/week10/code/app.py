from flask import Flask, render_template, request, jsonify
from inference import Estimator

app = Flask(__name__, template_folder='templates')
est = Estimator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    distrito = data.get('distrito')
    try:
        estimated = est.predict(distrito)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'distrito': distrito, 'estimated_rent': float(estimated)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
