# Contributing

Run the credential-free demo and tests before changing behavior:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

Use fictional test data. Keep database credentials, API keys, uploaded personal photos, and `.env` files out of commits. Add a regression test for behavior changes, especially wallet transactions, permissions, and AI failure states. Keep transaction callbacks free of network calls because Firebase can retry them.

Open an issue describing the problem and expected behavior before proposing a larger redesign. Pull requests should explain the user-visible change and how it was checked.
