
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

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Not Found</h1>", 404

@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Server Error</h1>", 500

# Application entry point
if __name__ == '__main__':
    import os
    
    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created!")
        except Exception as e:
            print(f"⚠️  Database error: {e}")
    
    # Run app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
