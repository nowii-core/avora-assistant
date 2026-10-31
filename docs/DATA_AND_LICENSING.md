# Dataset provenance and licensing

A model's code license does not license the text used to train it. Keep a record for each dataset with its source, retrieval date, language, licence/terms, transformation notes, and whether redistribution or commercial use is allowed.

## Optional starter source: Wikipedia

`python scripts/fetch_wikipedia.py --lang it --pages 200` obtains a small random sample through the MediaWiki API. It stores article titles, URLs and a licensing notice. Most Wikipedia text is under CC BY-SA 4.0 and/or GFDL, but exceptions can exist. Review source pages and your obligations before sharing a trained checkpoint, dataset, or commercial product. The sample downloader does not perform legal review or guarantee licensing eligibility.

Official references:
- Wikimedia content reuse: https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse
- Wikipedia reuse guidance: https://wikimediafoundation.org/what-we-do/wikimedia-projects/wikipedia/
- CC BY-SA 4.0 terms: https://creativecommons.org/licenses/by-sa/4.0/

## Before training

- Prefer original text, public-domain works verified for the relevant jurisdiction, or material whose licence explicitly permits the intended use.
- Do not assume that content being readable on the web makes it free for model training or redistribution.
- Keep an attribution/source ledger; retain page-level metadata for sources that need it.
- Exclude passwords, API keys, private chats, non-public personal data and other secrets.
- Remove exact duplicates and manually sample-check the corpus. This project does not yet implement semantic deduplication or a comprehensive PII detector.
- When source terms are unclear, leave the material out until clarified.
