
# Create database tables on startup
with app.app_context():
    db.create_all()
    print("✅ Database tables created!")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
