# Stalkin'

A small social network where posts are stock portfolios instead of photos.
Sign up, add your holdings, follow other people, and like/comment on their
portfolios. Current prices are pulled live so gains/losses stay up to date.

## Setup

```powershell
cd C:\Users\USER\portfolio-social
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python app.py
```

Then open http://127.0.0.1:5000

### Live prices need a free Finnhub API key

Current prices come from [Finnhub](https://finnhub.io/register) (free tier,
no credit card). After signing up, copy your API key and put it in a `.env`
file in this folder:

```
FINNHUB_API_KEY=your_key_here
```

Without a key, holdings will just show "price unavailable" — everything else
still works.

`init_db.py` seeds two demo accounts you can log in with right away:

- `alice` / `password123`
- `bob` / `password123`

(bob already follows alice, so logging in as bob shows a populated feed.)

## Notes

- Data is stored in `instance/portfolio.db` (SQLite), created automatically.
- Live prices come from [Finnhub](https://finnhub.io) and are cached in memory
  for 5 minutes per ticker (60 seconds for failed lookups) to stay well
  within the free tier's 60 requests/minute limit.
- Adding a holding validates the ticker against the live price API — a typo
  like `ZZZZINVALID` will be rejected on the form instead of saving.
- `SECRET_KEY` and `FINNHUB_API_KEY` can both be set in `.env`; a dev
  fallback is used for `SECRET_KEY` if it's missing.
