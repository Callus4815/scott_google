# Google Places Search Web App

A Vue.js frontend with Flask backend for searching Google Places and downloading results as CSV.

## Features

- 🔍 Search for businesses and services using Google Places API
- 📄 Display results in a beautiful card layout
- ⬇️ Load more results with pagination (up to 60 results)
- 📥 Download all results as CSV file
- 📱 Responsive design for mobile and desktop
- 🚀 Ready for Railway deployment

## Local Development

1. Install dependencies:
```bash
pip install -r requirements_flask.txt
```

2. Run the Flask app:
```bash
python app.py
```

3. Open http://localhost:5000 in your browser

## Railway Deployment

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Python app
3. Set environment variables if needed
4. Deploy!

## API Endpoints

- `GET /` - Main web interface
- `POST /api/search` - Initial search
- `POST /api/search/more` - Load more results
- `GET /api/download/<session_id>` - Download CSV
- `GET /api/health` - Health check

## Environment Variables

- `GOOGLE_API_KEY` - Your Google Places API key (required for production)

### Setting Environment Variables

**For Local Development:**
```bash
export GOOGLE_API_KEY="your_api_key_here"
python app.py
```

**For Railway Deployment:**
1. Go to your Railway project dashboard
2. Click on "Variables" tab
3. Add `GOOGLE_API_KEY` with your actual API key value
4. Railway will automatically restart your app with the new environment variable

## File Structure

```
├── app.py                 # Flask backend
├── templates/
│   └── index.html        # Vue.js frontend
├── requirements_flask.txt # Python dependencies
├── Procfile              # Railway process file
├── runtime.txt           # Python version
└── README.md            # This file
```
