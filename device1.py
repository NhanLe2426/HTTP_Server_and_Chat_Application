import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from   daemon import AsynapRous
from   daemon import Response

app = AsynapRous()

@app.route("/", methods=['GET'])
def index(headers="guest", body="anonymous"):
    return b"BACKEND 1 WORKING"

if __name__ == "__main__":
    # Run on port 9000
    app.prepare_address(ip="0.0.0.0", port=9002)
    app.run()