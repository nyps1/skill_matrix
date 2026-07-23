from app import create_app, setup_database

app = create_app()
setup_database(app)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
