# AI Evidence Log: Groww first-time SIP continuation discovery engine

_Generated 2026-11-05 | provider: gemini | tagging model: gemini-flash-lite-latest | synthesis model: gemini-flash-lite-latest_

## 1. Sources and volume analysed

| source     |   collected |   sip_keyword_match |   llm_tagged |   llm_relevant |
|:-----------|------------:|--------------------:|-------------:|---------------:|
| app_store  |          49 |                   5 |            5 |              3 |
| play_store |      210327 |               13712 |         3000 |            715 |
| tradingqna |         799 |                 431 |          431 |            120 |
| youtube    |        1379 |                 414 |          414 |            186 |
| TOTAL      |      212554 |               14562 |         3850 |           1024 |

**Pipeline:** collect -> keyword filter (SIP/MF terms, at least 6 words) -> LLM tagging with a fixed schema (15 items per request) -> counts, segment cross-tabs, opportunity scoring -> LLM synthesis.

**Coverage notes**

- play_store: a random sample of 3,000 of 13,712 keyword matches was tagged (seed 42, to fit the free API quota).
- Overall 1,024 of 3,850 tagged items (27%) were SIP-relevant.
- Items that could not be tagged in the last run: 0.
- **Not covered:** Reddit.
- App-store reviews over-represent technical complaints; community sources (TradingQ&A, YouTube) carry more of the 'should I continue' questions.


## 2. Golden set: 20 real items labelled by hand

- **relevant agreement:** 85% (n=20)
- **trigger agreement:** 75% (n=8, items I marked relevant)
- **action agreement:** 50% (n=8, items I marked relevant)

With n=8, one item moves trigger/action agreement by about 12 points, so read these as directional.

### Prompt iterations on the same golden set

| prompt version   | relevant   | trigger   | action    |
|:-----------------|:-----------|:----------|:----------|
| v2               | 75% (n=20) | 50% (n=8) | 0% (n=8)  |
| v3               | 85% (n=20) | 75% (n=8) | 50% (n=8) |
| v3 (current)     | 85% (n=20) | 75% (n=8) | 50% (n=8) |

### All 20 items

| id                                   | source     | text                                                                                                                                                             | human_relevant   | ai_relevant   | human_trigger              | ai_trigger                 | human_action     | ai_action        |
|:-------------------------------------|:-----------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|:--------------|:---------------------------|:---------------------------|:-----------------|:-----------------|
| as_14734412063                       | app_store  | Unable to modify SIP. Unable to modify SIP, Now migrating to zerodha                                                                                             | true             | true          | app_bug                    | app_bug                    | stopped          | considering_stop |
| as_14708297683                       | app_store  | Excellent Investment App. Groww is a user-friendly platform for investing in stocks, mutual funds, and IPOs. The interface is simple, and managing investments i | false            | false         | none                       | none                       | unknown          | unknown          |
| tq_372736                            | tradingqna | @Sunil_Sethy If you are looking for Non-demat based MF only platform, Then Kuvera is the right one. Direct MF in non-Demat form -You can track the same in       | false            | false         | none                       | none                       | unknown          | unknown          |
| tq_32080                             | tradingqna | What is the main use of pause and play option in mutual fund or sip on Zerodha MF platform?. how it helps for ELSS scheme?                                       | false            | false         | none                       | none                       | unknown          | unknown          |
| yt_Ugza2uSmWYU20TLlx494AaABAg        | youtube    | I'm step up my sip by value and top-up my fund                                                                                                                   | true             | true          | none                       | none                       | continuing       | continuing       |
| yt_Ugwyu7NUhH4halUsBlZ4AaABAg        | youtube    | Hii Mere sip 1000 hai par Same date pe jada cut ho Kar raha hai jaise 4 bar ya 5 bar to use kaise stop karu                                                      | true             | true          | none                       | mandate_or_payment_failure | unknown          | considering_stop |
| 2e1eff9e-c9a2-4ec3-a899-cdf126222e43 | play_store | Sent mf report to your email, still dashboard not updated from last 5 days.                                                                                      | false            | false         | none                       | none                       | unknown          | unknown          |
| 04833e45-888a-4183-8d11-bad77cc10680 | play_store | It is worst app. Customer support never function. And you can't contact the grievances redressal tab or anything. I made a switch in one of my mutual fund a wee | true             | true          | support_service            | support_service            | considering_stop | considering_stop |
| 29171100-715f-4abd-b8db-59c9c35f7c79 | play_store | Worst app ,first I invested in mutual fund through sipping but then it asked for autopay registered ,i cancel my sipping ,but my money didn't return ,it said se | true             | true          | mandate_or_payment_failure | mandate_or_payment_failure | stopped          | stopped          |
| bb770f5d-f4d0-4b5f-b117-12f00d82152c | play_store | Most shares are literally a scam, they just hold our share during downfall. And in mutual funds they just not return all the money, they took initial money we s | false            | false         | none                       | none                       | unknown          | unknown          |
| ba9adeb5-77ac-402d-96f9-f47fbf3c2e4d | play_store | Interface is good. But you can't add more shares once mandate is done nor can you create another mandate(unless you cancelled it). The worst part is their custo | true             | false         | mandate_or_payment_failure | none                       | blocked          | unknown          |
| cc55ce2e-d307-46a5-abc4-5dd514df718c | play_store | After update my stocks dashboard showes empty And mutual fund dashboard showing my investment....plz look into this                                              | false            | true          | none                       | app_bug                    | unknown          | blocked          |
| b998ce3c-0c37-4d90-9797-921dd8f92c55 | play_store | unit allocation is so slow process...i would rather use sbi mf app                                                                                               | true             | true          | app_bug                    | app_bug                    | considering_stop | considering_stop |
| 28fb3f09-46be-46c2-89e0-b3ccea97296f | play_store | Update - The mutual fund part works well, the new Fixed deposit part had a bajaj finance fd with best rates. However it was removed from the Groww app and now i | false            | false         | none                       | none                       | unknown          | unknown          |
| cbbc4347-5dbd-4aa2-9199-f08cc999bfca | play_store | Need improvement in terms of stock section rest mutual fund and gold great                                                                                       | false            | false         | none                       | none                       | unknown          | unknown          |
| 089b9905-ff10-4517-93ee-d7d79658a9c6 | play_store | Best App for mf or Stock, but not best option buy sell major problem                                                                                             | false            | false         | none                       | none                       | unknown          | unknown          |
| f3f4a72b-3776-44f9-bee6-9aa84899a935 | play_store | My journey starts with Groww in Mutual fund and Stock market. I am very much glad to say I just love this app soo much and in my friend circle I strongly recomm | true             | false         | none                       | none                       | started          | unknown          |
| 8c7cce6a-05b0-4bea-bf62-81af280ef27d | play_store | This is very best application for investment and It is also best for mutual fund application. I love this application.                                           | false            | false         | none                       | none                       | unknown          | unknown          |
| 12cbf402-c175-487d-8032-648c1ae3cc45 | play_store | This has a great mutual funds tracker where you can import and track all your mutual funds on the app. Highly Recommended.                                       | false            | false         | none                       | none                       | unknown          | unknown          |
| 4519d3f9-42e8-4045-b9e1-b2bdb69c732e | play_store | With next billion grow it comes start direct investment in mutual fund it's easy to invest in top funds through this app                                         | false            | false         | none                       | none                       | unknown          | unknown          |


### Where the engine disagreed with me (5 items)

| id                                   | source     | text                                                                                                                                                             | human_relevant   | ai_relevant   | human_trigger              | ai_trigger                 | human_action   | ai_action        | notes                                                |
|:-------------------------------------|:-----------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|:--------------|:---------------------------|:---------------------------|:---------------|:-----------------|:-----------------------------------------------------|
| as_14734412063                       | app_store  | Unable to modify SIP. Unable to modify SIP, Now migrating to zerodha                                                                                             | true             | true          | app_bug                    | app_bug                    | stopped        | considering_stop |                                                      |
| yt_Ugwyu7NUhH4halUsBlZ4AaABAg        | youtube    | Hii Mere sip 1000 hai par Same date pe jada cut ho Kar raha hai jaise 4 bar ya 5 bar to use kaise stop karu                                                      | true             | true          | none                       | mandate_or_payment_failure | unknown        | considering_stop | want to stop BECAUSE OF AMOUNT DEBIT RECURRING BAISS |
| ba9adeb5-77ac-402d-96f9-f47fbf3c2e4d | play_store | Interface is good. But you can't add more shares once mandate is done nor can you create another mandate(unless you cancelled it). The worst part is their custo | true             | false         | mandate_or_payment_failure | none                       | blocked        | unknown          |                                                      |
| cc55ce2e-d307-46a5-abc4-5dd514df718c | play_store | After update my stocks dashboard showes empty And mutual fund dashboard showing my investment....plz look into this                                              | false            | true          | none                       | app_bug                    | unknown        | blocked          |                                                      |
| f3f4a72b-3776-44f9-bee6-9aa84899a935 | play_store | My journey starts with Groww in Mutual fund and Stock market. I am very much glad to say I just love this app soo much and in my friend circle I strongly recomm | true             | false         | none                       | none                       | started        | unknown          |                                                      |


## 3. Places where AI output was rejected or corrected

**1. 5346b028-c190-43ac-80b0-0fc9ab422b63**  
AI said: v1: trigger=app_confusion, action=stopped  
Corrected to: trigger=app_bug, action=blocked  
Why: Review text: 'Unable to start new SIP app keepscrashing.' v1 prompt guessed actions that the text never stated. The schema had no category for app errors. Added app_bug and blocked, and told the model not to guess.

**2. v2 prompt, golden set**  
AI said: v2: action agreement 0% (n=8)  
Corrected to: v3: 50% (n=8)  
Why: The v2 rule ('only explicit actions') overcorrected: clear intent like 'would rather use another app' became unknown. Rebalanced the rule to accept clearly stated intent. No golden-set text was copied into the prompt, to keep the test fair.

**3. cc55ce2e-d307-46a5-abc4-5dd514df718c**  
AI said: v3: relevant=true, trigger=app_bug, action=blocked  
Corrected to: relevant=false  
Why: 'After update my stocks dashboard shows empty': a display bug was treated as a blocked SIP. Kept as a known failure; it slightly over-counts app errors.



## 4. Industry context used in the metric decomposition

| month   |   new_sips_registered_lakh |   sips_discontinued_or_matured_lakh |   stoppage_ratio_pct |   sip_inflow_crore | source_url                                                                                                                                                  | note                                    |
|:--------|---------------------------:|------------------------------------:|---------------------:|-------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------|
| 2026-01 |                      74.11 |                               55.46 |                74.83 |              31002 | https://www.angelone.in/news/mutual-funds/sip-stoppage-ratio-rises-to-over-75-percent-in-february-as-monthly-inflows-dip                                    | inflow from finnovate.in                |
| 2026-02 |                      65.72 |                               49.7  |                75.62 |              29845 | https://www.finnovate.in/learn/blog/february-2026-sip-inflows-and-stoppage-ratio                                                                            | SIP accounts 10.45 crore                |
| 2026-03 |                      52.82 |                               53.38 |               101.1  |              32087 | https://www.angelone.in/news/mutual-funds/mutual-fund-sip-stoppage-ratio-hits-over-100-in-march-inflows-touch-record-32-087-crore                           |                                         |
| 2026-04 |                      50.71 |                               51.29 |               101.14 |              31115 | https://cafemutual.com/news/press-news/37704-mutual-fund-sip-stoppage-ratio-continues-above-100-even-as-investors-contribute-record-rs-31115-crore-in-april |                                         |
| 2026-05 |                      54.16 |                               51.7  |                95.5  |                    | https://www.angelone.in/news/mutual-funds/mutual-fund-sips-stoppage-ratio-falls-to-95-as-new-registrations-rise                                             |                                         |
| 2026-06 |                            |                                     |                91    |                    | https://www.bajajbroking.in/share-market-news/fewer-investors-are-stopping-sips-stoppage-ratio-falls-to-81-9-percent-in-july                                | counts not in source; ratio approximate |
| 2026-07 |                      61.44 |                               50.29 |                81.9  |                    | https://www.bajajbroking.in/share-market-news/fewer-investors-are-stopping-sips-stoppage-ratio-falls-to-81-9-percent-in-july                                | inflow above 31000                      |
| 2026-08 |                      66.39 |                               53.82 |                81.1  |              32297 | https://www.indmoney.com/blog/mutual-funds/sip-stoppage-ratio-explained                                                                                     |                                         |
| 2026-09 |                      63.26 |                               49.68 |                78.53 |              32490 | https://www.5paisa.com/blog/sip-stoppage-ratio-falls-78-53-percent-record-inflows                                                                           |                                         |

Stoppage ratio = SIPs discontinued or matured ÷ new SIPs registered, industry-wide (all investors, not only first-time). Monthly figures from AMFI as reported by the linked news sources.