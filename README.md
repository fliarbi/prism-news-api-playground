# Prism News API Playground

**Live app:** [GitHub Pages](https://fliarbi.github.io/prism-news-api-playground/) · [Hugging Face Space](https://huggingface.co/spaces/fliarbi/prism-news-api-playground)

The live versions run the Streamlit app in your browser with [stlite](https://github.com/whitphx/stlite) (Python via WebAssembly), so nothing is sent to a server except your own API requests.

Paste your own Prism News API key, pick an endpoint (overview, trends, geography, themes, headlines) and filters, and see the JSON plus a chart. The key is never stored.

## How to get a key

Sign in to the [Fliar dashboard](https://fliarbi.com/radar/dashboard?tab=radarapi), open **API keys**, choose **Create or manage API keys** and create a key with **News only** or **All data** access. The Free plan gives 1,000 requests a month.

## Privacy

The key is typed into a password field, sent only to `radar-api.fliarbi.com` in the `X-API-Key` header for the request you run, and never written to disk, logs, the URL or browser storage.

## Links

- All 60 news datasets: https://fliarbi.github.io/news-datasets/
- Prism News API: https://github.com/fliarbi/prism-news-api
- Contact: b2b@fliarbi.com

App code: MIT.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
