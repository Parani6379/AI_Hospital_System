from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 55)
    print("  AIHAS - Hospital Automation System")
    print("  URL: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)