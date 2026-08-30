# API

```bash
### Serving Endpoints
uv run uvicorn main:app --port 8005 --reload

### URI redirection with ngrok
brew install --cask ngrok
ngrok config add-authtoken "<YOUR_AUTHTOKEN>"

ngrok http 8005

Forwarding                    https://a1b2-34-56-78-90.ngrok.app -> http://localhost:8005
```

