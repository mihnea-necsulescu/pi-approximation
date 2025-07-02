import json
import logging
from typing import Iterator

from flask import Flask, request, jsonify, Response
from flask.typing import ResponseReturnValue
from flask_cors import CORS

from generator import generate_random_points

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def format_sse(data: str, event: str = None) -> str:
    """Format data for SSE"""

    msg = f'data: {data}\n\n'
    if event:
        msg = f'event: {event}\n{msg}'
    return msg


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/generatePoints", methods=["POST"])
def generate_points() -> ResponseReturnValue:
    """Stream random points for pi approximation via SSE"""

    data = request.get_json()
    if not data or "num_points" not in data:
        logger.warning("Request missing 'num_points' parameter")
        return jsonify({"error": "num_points is required"}), 400

    num_points = data["num_points"]

    if not isinstance(num_points, int) or num_points <= 0:
        logger.warning(f"Invalid 'num_points' parameter: {num_points}")
        return jsonify({"error": "num_points must be a positive integer"}), 400

    batch_size = min(10000, num_points)  # todo make default batch size configurable
    logger.info(f"Starting point generation: {num_points} total points, batch size: {batch_size}")

    def generate_points_stream() -> Iterator[str]:
        """Generator function that yields random points for SSE stream"""

        points_sent = 0

        logger.info(f"SSE stream started for {num_points} points")
        yield format_sse(json.dumps({
            "total_points": num_points
        }), event="start")

        while points_sent < num_points:
            # check how many points to send in this batch
            points_in_batch = min(batch_size, num_points - points_sent)

            batch_points = generate_random_points(points_in_batch)
            points_sent += points_in_batch

            logger.info(f"Sending {points_sent}/{num_points} points")

            batch_data = {
                "points": batch_points,
                "points_sent": points_sent
            }

            yield format_sse(json.dumps(batch_data), event="batch")

        logger.info(f"Point generation completed: {points_sent} points sent")
        yield format_sse(json.dumps({
            "total_points": points_sent
        }), event="end")

    return Response(
        generate_points_stream(),
        mimetype="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
