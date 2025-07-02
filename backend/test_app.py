import json
from typing import List, Dict, Any, Iterator

import pytest
from flask.testing import FlaskClient

from app import app


@pytest.fixture
def client() -> Iterator[FlaskClient]:
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def parse_sse_messages(response_data: bytes) -> List[Dict[str, Any]]:
    """Parse SSE response data into events"""
    events = []
    message_blocks = response_data.decode('utf-8').strip().split('\n\n')

    for block in message_blocks:
        if not block.strip():
            continue

        event = {}
        for line in block.strip().split('\n'):
            if line.startswith('event: '):
                event['event'] = line[7:]
            elif line.startswith('data: '):
                event['data'] = json.loads(line[6:])

        if 'event' in event and 'data' in event:
            events.append(event)

    return events


class TestGeneratePointsEndpoint:

    def test_missing_num_points(self, client):
        response = client.post('/generatePoints',
                               json={},
                               content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert 'num_points is required' in data['error']

    def test_invalid_num_points_type(self, client):
        response = client.post('/generatePoints',
                               json={'num_points': 'invalid'},
                               content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert 'must be a positive integer' in data['error']

    def test_negative_num_points(self, client):
        response = client.post('/generatePoints',
                               json={'num_points': -1},
                               content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert 'must be a positive integer' in data['error']

    def test_zero_num_points(self, client):
        response = client.post('/generatePoints',
                               json={'num_points': 0},
                               content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert 'must be a positive integer' in data['error']

    def test_sse_event_sequence_small(self, client):
        response = client.post('/generatePoints',
                               json={'num_points': 50},
                               content_type='application/json')

        assert response.status_code == 200

        events = parse_sse_messages(response.data)

        assert len(events) == 3  # start + batch + end

        start_event = events[0]
        assert start_event['event'] == 'start'
        assert start_event['data']['total_points'] == 50

        end_event = events[-1]
        assert end_event['event'] == 'end'
        assert end_event['data']['total_points'] == 50

        batch_event = events[1]
        assert batch_event['event'] == 'batch'
        assert batch_event['data']['points_sent'] == 50

        points = batch_event['data']['points']
        assert isinstance(points, list)
        assert all(isinstance(point, list) and len(point) == 2 for point in points)
        assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in points)

    def test_sse_event_sequence_large(self, client):
        response = client.post('/generatePoints',
                               json={'num_points': 1000001},
                               content_type='application/json')

        assert response.status_code == 200
        events = parse_sse_messages(response.data)

        batch_events = [e for e in events if e['event'] == 'batch']
        assert len(batch_events) == 101  # 100 batches of 10000 + 1

        end_event = events[-1]
        assert end_event['data']['total_points'] == 1000001
