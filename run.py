from app import create_app, setup_database

import sys

app = create_app()
setup_database(app)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("Starting production server with Waitress on http://0.0.0.0:5000")
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
