from flask import Flask, render_template, jsonify, request, Response, send_from_directory
import json
import queue
import threading
import pytest
import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

result_queue = queue.Queue()
is_running = False


class LiveTestPlugin:
    def __init__(self, q):
        self.q = q

    def pytest_runtest_logreport(self, report):
        if report.when == 'call' or (report.when == 'setup' and report.failed):
            status = 'passed' if report.passed else 'failed' if report.failed else 'skipped'
            self.q.put({'type': 'result', 'test': report.nodeid, 'status': status})

    def pytest_sessionfinish(self, session, exitstatus):
        self.q.put({'type': 'done'})


def run_pytest_thread(selected_tests, q):
    global is_running
    is_running = True
    os.chdir(BASE_DIR)
    plugin = LiveTestPlugin(q)
    pytest.main(selected_tests + ['--html=report.html', '-v'], plugins=[plugin])
    is_running = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/tests')
def get_tests():
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '--collect-only', '-q', '--no-header'],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    tests = [line.strip() for line in result.stdout.split('\n') if '::' in line.strip()]
    return jsonify(tests)


@app.route('/api/run', methods=['POST'])
def run_tests():
    global result_queue, is_running
    if is_running:
        return jsonify({'status': 'already running'}), 400
    selected_tests = request.json.get('tests', [])
    result_queue = queue.Queue()
    threading.Thread(
        target=run_pytest_thread,
        args=(selected_tests, result_queue),
        daemon=True
    ).start()
    return jsonify({'status': 'started'})


@app.route('/api/stream')
def stream():
    def generate():
        while True:
            try:
                data = result_queue.get(timeout=1)
                yield f"data: {json.dumps(data)}\n\n"
                if data.get('type') == 'done':
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/report')
def report():
    return render_template('report_page.html')


@app.route('/report-raw')
def report_raw():
    if os.path.exists(os.path.join(BASE_DIR, 'report.html')):
        return send_from_directory(BASE_DIR, 'report.html')
    return "No report found. Run tests first.", 404


@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)


if __name__ == '__main__':
    import webbrowser
    webbrowser.open('http://localhost:5001')
    app.run(port=5001, debug=False, threaded=True)

