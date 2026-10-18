from flask import Flask, jsonify, render_template, request

from inference import Estimator

app = Flask(__name__, template_folder="templates")
est = Estimator()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    distrito = data.get("distrito")
    try:
        estimated = est.predict(distrito)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify({"distrito": distrito, "estimated_rent": float(estimated)})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
