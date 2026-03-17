
    print("✅ Database tables created!")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    import os
    
    # Create database tables on first run
    with app.app_context():
        db.create_all()
        print("✅ Database initialized!")
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
