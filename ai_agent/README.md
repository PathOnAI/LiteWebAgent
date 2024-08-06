# README
## 1. Set up
### 1.1 Environment Setup
```bash
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Create .env file

```
cp env.example .env
```

install pandoc
```
brew install pandoc
```

Update the API keys in the `.env` file

```
python resume_test.py
python airbnb_test.py
python amazon_test.py
```