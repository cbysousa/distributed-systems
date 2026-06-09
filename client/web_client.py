from flask import Flask, jsonify, render_template, request

import gateway_api


app = Flask(__name__)


METRICS_BY_SOURCE_TYPE = {
    "weather": [
        "temperature_celsius",
        "humidity_percent",
    ],
    "air_quality": [
        "co2_ppm",
        "particulate_matter_ug_m3",
        "air_quality_index",
    ],
    "lamppost": [
        "luminosity_percent",
        "energy_consumption_kwh",
    ],
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sources")
def api_sources():
    try:
        data = gateway_api.list_sources()
        data["metrics_by_source_type"] = METRICS_BY_SOURCE_TYPE
        return jsonify(data)
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/readings")
def api_readings():
    source_name = request.args.get("source", "").strip()
    metric = request.args.get("metric", "").strip()

    try:
        data = gateway_api.list_readings(source_name, metric)
        return jsonify(data)
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/aggregate", methods=["POST"])
def api_aggregate():
    body = request.get_json(force=True)

    try:
        data = gateway_api.aggregate(
            source_name=body.get("source_name", ""),
            metric=body.get("metric", ""),
            operation=body.get("operation", "avg"),
            window_seconds=int(body.get("window_seconds", 0)),
        )
        return jsonify(data)
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/lamppost/<source_name>/turn-on", methods=["POST"])
def api_lamppost_turn_on(source_name):
    try:
        return jsonify(gateway_api.lamppost_turn_on(source_name))
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/lamppost/<source_name>/turn-off", methods=["POST"])
def api_lamppost_turn_off(source_name):
    try:
        return jsonify(gateway_api.lamppost_turn_off(source_name))
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/lamppost/<source_name>/state", methods=["POST"])
def api_lamppost_state(source_name):
    try:
        return jsonify(gateway_api.lamppost_get_state(source_name))
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/lamppost/<source_name>/luminosity", methods=["POST"])
def api_lamppost_luminosity(source_name):
    body = request.get_json(force=True)
    luminosity = float(body.get("luminosity_percent", 50))

    try:
        return jsonify(gateway_api.lamppost_set_luminosity(source_name, luminosity))
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/lamppost/<source_name>/failure", methods=["POST"])
def api_lamppost_failure(source_name):
    try:
        return jsonify(gateway_api.lamppost_simulate_failure(source_name))
    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)