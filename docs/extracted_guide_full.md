# Build Your Own Skew Map — How to See What Options Traders Are Actually Paying For (and the Weekend Version You Can Build Yourself)

Price tells you what a stock did. The options chain tells you what people are paying to be protected from what it does next. That gap is the whole map — here's how to read it, the five traps that make most people read it backwards, and how to build a working version yourself over a weekend.

By berttrading — a swing trader sharing how I research, not an advisor.

> Educational only. Nothing here is financial advice or a recommendation to buy or sell any stock. This is a positioning layer — where to look — not a signal and not a buy list. Do your own research and manage your own risk.


---

> 

How this is laid out. Parts 1–3 are the read — what skew is, the four quadrants, and the five mistakes that make most people read it backwards. Ten minutes, and it's useful on its own even if you never build anything. Parts 4–6 are the build: a spreadsheet you can stand up in an afternoon and run in 15–20 minutes a week. Part 7 onward is what the finished version looks like once it's running.

If you read one section, make it Part 2. That's the entire framework in one table.

Every screenshot here is a single day's board. The numbers on it moved the next morning — that's the point of a daily map. What doesn't move is how you read it, which is what the rest of this page is about.

I run a skew map every afternoon. It scores a few hundred names on what the options market is charging for downside protection versus upside, cross-references that against how the stock actually traded, and sorts everything into four buckets. It takes about twelve seconds to run and it took me two weeks and one genuinely embarrassing bug to get right.

What you need isn't my version — it's the read, and a simple version you can actually maintain. You can build one with your broker's option chain, any free screener, and a spreadsheet.

This is mine, from the close on August 17. Top strip first — where money moved, and which sector is paying most for protection:

![image](attachment:bcb0e8ba-98f2-45b4-9751-7894b96301c2:skew-10-kpi-strip.png)

Read it left to right: money in, money out, most-hedged sector. The thing to look for isn't the biggest number — it's a sector where dollars are leaving while the price is still rising. Flow and price disagreeing is the whole reason this strip sits at the top instead of a return column.

Then the written read:

![image](attachment:c3ab9cad-3a71-40d7-8143-2c66503e8664:skew-01-todays-read.png)

Written from the numbers underneath, same rules every day — so a quiet day reads quiet and I can't talk myself into anything. The sentence type worth waiting for is the caution flag — a name that keeps rallying while someone underneath it pays heavily for crash protection. A stock going up while somebody buys expensive insurance on it isn't enthusiasm, it's hedging, and it means tighten rather than exit. A tool that can only tell you what went up would never surface that sentence at all.

> 

This thing runs every weekday after the close and posts inside my Swing Trading Desk. I'm going to show you how to read it, then how to build your own — and if by the end you'd rather just have mine every morning, that link works too. Read first.


---


## Part 1 — What skew actually is (in one page)

The idea, before any jargon. Insuring a house on a floodplain costs more than insuring the same house on a hill — the price of protection tells you something the house's value doesn't. Options are insurance on a stock, and the price of that insurance isn't symmetrical: protection against a fall usually costs more than a bet on a rise. Sometimes far more. Occasionally it flips entirely. That gap, and which way it leans, is the whole signal. Everything below is just how to measure it.

Now the mechanics. Every option on a stock has an implied volatility — the market's price for how much that stock might move. Here's the thing most people never notice: those numbers aren't the same across strikes.

Take any stock. Look at an out-of-the-money put and an out-of-the-money call that are equally unlikely to pay off — equally far out, opposite directions. On most equities, most of the time, the put is more expensive. That difference is skew. The names where that flips are the entire reason this map exists.

The shape of the measurement:

> 

Skew = (OTM put IV − OTM call IV) ÷ ATM IV

Positive = puts cost more = protection is bid

Negative = calls cost more = upside is bid = someone is paying up to be long

How far out those two strikes sit, and whether you divide by ATM at all, are decisions #1 and #3 in Part 4 — both worth settling deliberately rather than by default.

Dividing by at-the-money IV is what makes a utility comparable to a semiconductor — it turns "puts are 4 vol points richer" into a percentage of that stock's own volatility.

Two things that matter more than the formula:

Skew is positioning, not prediction. It does not tell you where a stock is going. It tells you what people are paying to be positioned a certain way, which is a very different and much more honest thing. A name with heavy put skew isn't going down — it's a name where protection is expensive, which sometimes means everyone's already scared and sometimes means they're right.

The level is structural. The change is the signal. Some names always carry put skew — that's just what that stock is. Comparing MU's skew to KO's skew tells you almost nothing. Comparing MU's skew today to MU's skew five days ago tells you a lot. This is the single biggest upgrade you can make to how you read it.


---


## Part 2 — The four quadrants

Here's where it becomes a map instead of a number. Put skew on one axis and the stock's one-month return on the other, and every name lands in one of four boxes. Each box means something specific.

Here's what that looks like plotted on every name I cover:

![image](attachment:56ed7e7e-c426-4caa-aec0-cb2fa0ab1287:skew-02-name-radar-quadrants.png)

Every dot is a stock; orange is my watchlist; hollow means a chain too thin to trust. The corner that earns its keep is bottom-left: names that fell on the month while somebody kept paying up for upside anyway. Top-right is the mirror image — rising, with protection being bought underneath. Neither is a signal on its own. Both are short lists you would never have assembled by scrolling a watchlist.

The same four boxes live inside the tool as a permanent explainer, because I got tired of re-deriving them:

![image](attachment:7b87fe06-93af-45bc-90c7-caca7533d0bc:skew-11-how-to-read.png)

The four verdicts, written down once so I never re-argue them at 4pm on a red day. If you build one thing off this page, build this card — deciding in advance what each box means is most of the discipline, and it's free.

One detail worth stealing: the map re-plots on three horizons, but the ranked list underneath stays anchored to one. A name that looks like a contrarian bid on the month and a chase on the day is telling you something — you just have to pick which clock is the official one.

![image](attachment:dd9064bc-c4d1-417a-99b6-8748ddcec6c0:skew-12-radar-timeframe.png)

Same names, three horizons. A stock that reads contrarian bid on the month but chase on the day is telling you the turn already started without you. Toggle the lens — but keep the verdict anchored to one clock, because changing both at once is how you talk yourself into anything.

The reason I care most about contrarian bid is that it's the only quadrant where two sources of information disagree. When price and positioning point the same way, you've learned nothing you couldn't get from a chart. When they split, something is happening that price hasn't shown you yet — sometimes it's an informed bid, sometimes it's a dated catalyst, and sometimes it's nothing. But it's the only box worth investigating, and that's what a research layer is for.


---


## Part 3 — The five traps

This is the part I'd actually pay for, so it's the part I'm giving you first. Every one of these cost me something — either a rebuild, a day of debugging, or a read that was confidently wrong.


### 1. Never quote an index put/call ratio. Ever.

You've seen people post "SPY put/call is at X, the market is terrified." That number is not a sentiment reading. It's a windowing decision wearing a sentiment costume.

Here's why: about 86% of SPY put open interest sits below 0.10 delta — lottery-ticket crash hedges nobody expects to pay off. So the number you get depends entirely on which strikes you decide to count. Measuring the whole chain, I get about 3.8. Measuring a sane delta band, about 2. I've seen a well-followed version of this tool publish 0.91 — and I swept twenty-four different windows trying to reproduce it and could not.

Same day. Same underlying. Three answers, one of which I still can't recreate. Single-name and sector put/call are far less tail-dominated and stay usable. Index put/call is a coin flip with a decimal point.


### 2. Don't compare sectors using normalized skew

Remember dividing by ATM IV? That's exactly right for comparing names inside a sector, and it quietly lies to you across sectors — because ATM IV varies by roughly 3x between Utilities and Semis. Divide by a small number and you get a big percentage.

Run that across the market and Utilities, Real Estate and Staples float to the top of your fear rankings basically every day, for arithmetic reasons. For cross-sector comparison, use raw volatility points, not the normalized percentage. Keep the normalized version for ranking names within a group, where it belongs.

![image](attachment:402e80c9-406f-4922-98c5-c179eae856e9:skew-13-sector-skew-bars.png)

Longer bar = puts pricier than calls = more fear premium sitting in that sector. The dashed lines are SPY, QQQ and IWM, so you can see at a glance whether a sector carries more hedging than the index it lives inside. This chart is level only — and level on its own is never the trade, which is exactly why the map below crosses it with price.


### 3. Check agreement before you trust any sector reading

A sector's skew is an average, and averages hide things. Before you say "energy is getting hedged," check what share of the names in that sector are actually leaning that way.

So pick an agreement threshold, and below it refuse to call it a sector move at all. Mine prints the agreement figure next to every sector row and auto-attaches a caveat when it's too low. Where exactly you set that line is a judgment call — the discipline that matters is setting it once, in advance, and never nudging it because a story you like is sitting just under it.

This is why I look at sectors as a grid of names rather than one number — you can see instantly whether a sector is leaning together or being dragged by two tiles:

![image](attachment:e90dfab5-4d8a-42e4-b6ac-f9366445cff4:skew-03-treemap.png)

Twelve biggest names per sector, colored by which side is bid, sized by dollars traded. The reason I look at a grid rather than a sector average: on most days the biggest tech names are split, some with puts bid and some with calls bid. "Tech is fearful" is almost always the wrong sentence, and the split is the actual information. One loud outlier tile is also exactly what drags a sector average when you haven't checked agreement first.


### 4. One bad quote can invert an entire name

This is the embarrassing one. Early on, my system printed Duke Energy at a skew of −1.43 — a screaming upside bid on a utility, which should have been my first clue. The truth was around +0.20. One bad option mark on one leg did it.

Worse: that single bad name dragged my whole validation correlation from 0.90 down to 0.14. One number, and the entire map became untrustworthy — while still looking perfectly plausible.

So: pick a sanity ceiling and hard-reject above it. Decide the level at which you stop believing your own number and assume a bad mark — and set it by asking what's plausible for that kind of stock, not by looking at your data and drawing a line under the ugliest point. And if a name has a thin option chain — a handful of strikes, tiny open interest — treat every number it produces as noise, no matter how dramatic. Show it if you like, but label it and never act on it.


### 5. A dated catalyst is not sentiment

If a name has earnings next week, the front-week options will be expensive. That's not fear — that's an event with a date on it, priced correctly.

Before reading any elevated skew as sentiment, check the earnings calendar. If there's a catalyst inside the expiry you're measuring, you're looking at event premium, not positioning. The tell is comparing the near-term expiry to the monthly: a big gap that collapses after the event was always just the event.

> 

That's the read — the part that took me longest to learn and the part I'd have paid for. Everything below is construction.

If you'd rather skip the construction: this map lands in the Swing Trading Desk every trading day, already built and already read, alongside the weekly watchlist and every trade I take.

→ See it inside the Desk


---


## Part 4 — Build your own

No code, no API, no data subscription. Your broker's option chain, any free screener, and a spreadsheet.

> 

Build it on your own numbers. Every decision below has a range of defensible answers, and the right one depends on your universe, your holding period, and how much noise you can stand.

This matters more than it sounds: a number you didn't choose is a number you can't debug. Mine once printed a utility at a screaming upside bid for days and looked beautiful doing it — I only caught it because I knew exactly what I'd set and why. Run settings you inherited from somebody else and the first time your board goes strange, you won't know which dial moved.

So below: the decision, why it matters, and what breaks if you get it wrong.

First, the one piece of jargon. Skew is measured between two strikes that are equally far out in probability terms. Delta is the industry's shorthand for that probability — an approximation rather than the exact number, but it's the one already printed on every chain you can open: Fidelity, Schwab, Robinhood, Webull, tastytrade, thinkorswim, all of them. A 25-delta option is loosely a 1-in-4 shot, and somewhere around there is the common convention. Which level you actually pick is decision #1 below.

And the honest cost, up front: an afternoon making these seven decisions, about an hour for your first pass, then 15–20 minutes a week. Six weeks before the change-based columns start meaning anything. Do it four times and you'll start recognizing names by their skew signature before you check the chart — which is the whole return on the exercise.

This version is free and it stays free. It also has a hard ceiling, and you'll hit it somewhere around week three. I've written out exactly where it is at the bottom of this page — go read that first if you'd rather know before you start than after.


### The seven decisions you have to make


### The weekly loop

1. Pick your universe. 15 to 25 names you already follow. These are the names you're going to rank.
Then pick a second, broader list you did not choose — a sector ETF's holdings page is free and neutral. That one is your sector benchmark, per decision #4. Ranking your own picks against your own picks tells you nothing; it just launders your existing bias back to you as a signal. Decide your own minimum names-per-sector before a sector read counts, and write it at the top of the sheet.

1. Apply your expiry rule (decision #2) and use it for every name without exception. Monthlies, roughly a month or two out, is the sane neighbourhood; the exact window is yours. Same rule every week or nothing is comparable to anything.
1. Pull three numbers per name from that chain: at-the-money IV, plus the put IV and call IV at your chosen delta (decision #1), mirrored either side.
1. Compute skew: put IV against call IV, normalized however you settled decision #3.
1. Add price context: the stock's 1-month % return. Also compute that return minus SPY's — plot the raw return on the map (that's what mine does) and keep the vs-SPY number in a column next to it, because everything looks strong in a strong month.
1. Add volume context: today's volume ÷ its average volume. Free on any screener. Set your own heavy/light cutoffs — pick them once, write them at the top of the sheet, and don't move them mid-week.
1. Plot it. Scatter chart, x-axis = 1-month return, y-axis = skew. You now have the four quadrants from Part 2, with your names sitting in them.
Expect it to look lopsided, and don't assume you broke it. Positive put skew is the resting state for most equities, so if you crosshair at zero, the majority of your names will pile into the top half and the two negative-skew boxes will look almost empty. That's not a bug — that's why those two boxes are the interesting ones and why they're never crowded. If you'd rather have a genuinely centred map, put the crosshair on the median of your own list instead of at zero. Either is defensible. Just write down which one you chose, because the two maps say different things.

1. Save the file with the date. This is the step everyone skips and it's the one that makes the whole thing work — because next week you can compute the change — and as Part 1 says, the level is structural but the change is the actual signal. Six weeks in, you'll have something genuinely rare.
1. When you outgrow the sheet, connect it to institutional data. Hand-entry caps you at roughly twenty names, once a week. Going past that means pulling chains and price history programmatically, which needs a plan on the stock side and a plan on the options side — around $30 a month each. The options side is the one that matters: it has to carry per-contract implied volatility and greeks, not just prices. That's the unlock, and it's the moment this stops being a spreadsheet and starts being a system.

### The sheet

One upgrade once the sheet works: make it sliceable. Being able to cut the same board by sector and by size is what turns a list into a tool — "is this a tech thing or a small-cap thing" is a question you'll ask constantly, and it should take one click, not a rebuild.

![image](attachment:d2492864-987e-4371-8cb6-29c2b04ae43f:skew-14-filter-chips.png)

The same board, sliced. "Is this a tech story or a small-cap story?" is a question you'll ask constantly, and it should cost one click rather than a rebuild. In a spreadsheet this is just a filter row — but decide up front that every view is sliceable, because retrofitting it later is miserable.


---


## Part 5 — Reading a row out loud

I force every name through the same sentence, in the same order, every single day. Not because it's elegant — because a fixed template stops me from telling myself a story about the ones I already like.

> 

[Ticker] — traders are paying [slightly / clearly / heavily] more for [puts / calls], which is more [fear / upside] than [X%] of its sector. The stock is [up/down X%] on the month [vs SPY], on [heavy / normal / light] volume. That puts it in [quadrant].

Here's mine writing that sentence by itself — this is a real row from August 17, hovered:

![image](attachment:98ab157b-2e6a-4167-abe9-d749d3b20bed:skew-04-tooltip-read.png)

Read it against the template above, in order: what they're paying for → how that ranks inside its own sector → price context → volume → verdict. The pattern this one catches: a stock up hard on the month with the put side still bid, carrying more fear premium than most of its sector. That is not a top call. It reads as someone insuring a winner they intend to keep — which is a tighten-your-stop signal rather than an exit signal, and those two get confused constantly.

And the same sentence follows the name everywhere — here it is again off a dot on the map instead of a row in the table:

![image](attachment:5277d59d-6a40-4f56-be1b-8ae722c78942:skew-15-radar-dot-tooltip.png)

Same sentence, different surface — a dot on the map instead of a row in the table. The consistency matters more than any individual number here: it means I can't accidentally tell myself two different stories about the same stock depending on where I happened to click. Whatever the read is, it follows the name everywhere.

You can write that sentence by hand from your spreadsheet in about fifteen seconds a name. That's the point — the automation isn't the insight, the sentence is.

Two rules on that sentence. Say the quadrant out loud — it forces a verdict instead of a vibe. And end with the action, which for a skew map is almost always "watchlist" or "leave it," because this layer tells you where to look and it is structurally incapable of telling you when.


---


## Part 6 — If you're going to automate it, read this first

> 

Should you automate it? Open Part 6 above for the honest answer: eight failure modes that never throw an error, and the only reliable way to catch them is building the whole thing twice and diffing the output every day. I did it because I wanted to know exactly how every number on my screen was made. That's a real reason — it just isn't a good enough reason for most people.

If you'd rather skip to the part that pays: I post this map every trading day inside the Swing Trading Desk, already built and already read.

→ See the daily map inside the Desk


---


## Part 7 — Where skew stops and the rest of the board starts

Skew answers one question: what are people paying to be positioned. It cannot tell you where the money is actually moving. Those are different signals and they're at their most useful when they disagree — so on my board the skew map sits alongside a flow layer.

Money flow by industry, ranked, with a plain verdict on each row:

![image](attachment:327224cd-715a-4519-9fbc-d184cea82bdf:skew-16-industry-flows.png)

Sorted by one-month return against SPY, with a participation column beside it — a theme leading on 100% of its names is the healthy kind of move, one leading on a third of them is two stocks wearing a costume. The comparison that pays is monthly against weekly: when a theme's whole month happened in the last five days, that's a different situation from one that's been grinding, even though the month column looks identical.

Every row explains itself the same way the names do:

![image](attachment:322bd9b6-1a44-49bc-a1d0-9d88bce721ac:skew-19-industry-tooltip.png)

Hovering any theme gives the read plus the biggest names inside it — so a line like "this theme is leading and extending" resolves immediately into three tickers you can actually go look at. That's the step most dashboards skip, and it's the one that matters: a theme you can't convert into names isn't a signal, it's a headline.

The same four-quadrant idea, applied to themes instead of individual names:

![image](attachment:6af0d969-87d2-42ed-961c-c7af78855732:skew-17-theme-rotation.png)

The same four quadrants, run on themes instead of individual names. Right of the line = beating SPY; above it = still accelerating; the tail behind each dot is the last three weeks, so you see direction rather than just position. Themes travel clockwise — Improving → Leading → Weakening → Lagging. The quadrant nobody respects is Weakening — still winning, quietly losing steam. That's the one people add to, because the month-to-date number still looks great.

And where the money physically went, week over week:

![image](attachment:751367b9-5227-44fb-9be0-0050a2baf1e3:skew-18-turnover-migration.png)

Where the dollars actually went, this month against last. The column that stops you making a mistake is breadth, on the right: a sector can gain share of the market's entire volume while only a fifth of its names participate — which is one or two stocks, not a rotation. Share moved plus breadth thin is a headline. Share moved plus breadth broad is a trend.

You do not need any of this to start. It's here so you know what the spreadsheet grows into, and so you can decide which layer is worth your Sunday.


---


## How I'd actually use this

A skew map is a where-to-look layer. That's the whole job. It is not a buy list, it does not produce entries, and the fastest way to lose money with it is to treat a quadrant as a signal.

Here's how the four buckets actually change my week:

* Contrarian bid → these go on the watchlist. Not bought — watched. Then I pull up the chart and start asking the questions this layer can't answer.
* Chase → I already know about these, everyone does. If I don't own it, I'm late; the map's job here is to stop me from feeling clever about a crowded trade.
* Hedged rally → about things I already own. Rally the options market doesn't trust, so I tighten.
* Fear → nothing. Cheap and falling with protection getting more expensive is not a bargain.
Once you've got the map, the last step is ranking — which of the interesting names is most interesting today:

![image](attachment:c8c062ee-6a9a-4325-8eda-2dcbee32c469:skew-05-action-board.png)

The ranked shortlist, and the reason the verdict column exists. Two rows can carry the identical signal — the options crowd leaning bullish against their sector peers — and mean opposite things: on a name that already fell, it reads FRESH LOOK, contrarian bid; on a name that already ran, it reads MOMENTUM, crowded. Same evidence, different verdict, decided by where price already is. The footer says the quiet part out loud: these still need your chart, your zone and your risk before any of them is a trade.

And then the honest part: the map hands you a shortlist, and a shortlist is not a trade. It tells you a name is interesting today. It cannot tell you the level to watch, where the idea is wrong, or whether today is the day. Those come off the chart, and they're a completely separate skill.

That gap is where people lose money on genuinely good ideas. You can be right about which name and still lose, because you were wrong about where and when.


---


## The whole point: every name gets a bucket

Here's what I actually want you to take away. It isn't any single number on this page — it's that nothing is left unclassified.

![image](attachment:4134d245-68bc-4435-9e24-54771ecd67b2:skew-20-coverage-note.png)

777 names with skew computed, ranked by 21-day average dollar volume — $724.5B of it — and the sixteen that failed a chain check are named individually rather than quietly dropped. That last part is the tell for whether any dataset is honest: a system that hides what it couldn't cover is hiding the size of its own blind spot.

Every one of those names comes out the other side wearing a verdict. Contrarian bid — falling, but someone's paying for upside, so it goes on the watchlist. Crowded — working, everyone knows, so don't chase it. Hedged rally — tighten. Fear — leave it. Look back at the action board above: every row carries its label in plain English, in the same words every single day.

That's the difference between having a tool and having an opinion. When you open a board where all several hundred names are already sorted, you're not hunting for something interesting — you're choosing between things that have already been filtered, with the reasoning attached. And on the days nothing is interesting, it tells you that too, which is the part that saves the most money.

Underneath it all sits the full database — every covered name, every column, sortable:

![image](attachment:c9519861-6b19-4587-9d76-24181c2ec0c9:skew-06-explorer.png)

This is the part that takes weeks to build and a data subscription to feed. Your spreadsheet gives you the same read on 20 names — which is most of the value, on 20 names. What it can't give you is the other several hundred, a read on a Tuesday you didn't have a spare hour, or the level to watch on the day one of them finally turns interesting.


---


## The ceiling on the free version — and what it costs to get past it

I'd rather you hear this from me now than find it out in week three.

The spreadsheet genuinely works, and it genuinely stays free. Your broker's chain already prints implied volatility and delta on every contract, and nobody charges you to look at it. On 15 to 25 names, once a week, you will get the same read I get. That is not a watered-down demo — for one watchlist, it is most of the value.

Here's where it stops:

* You can't scale it by hand. Twenty names is a comfortable Sunday. A hundred names is not a longer Sunday, it's a second job — and the whole point of a map is seeing the names you weren't already watching.
* Your sector benchmark stays too small to lean on. Decision #4 says your benchmark needs its own broad, neutral universe. Typing one in by hand every week isn't realistic, so in practice your sector reads stay directional at best.
* Every change-based column is blank for six weeks. And the change is the reading that actually matters — Part 1, first principle.
* One snapshot a week means you see Wednesday on Sunday. A name that flips from contrarian bid to fear midweek simply doesn't reach you until after it's happened.
And every one of those fixes lands on the same requirement — step 9 above. All of them need option chains pulled programmatically, and free feeds hand you a last price and maybe one blended volatility figure. Delta-anchored work needs per-contract implied volatility and greeks, and nobody gives that away.

So the real fork was never "free versus paid." It's this:

If your goal is to understand how this works — build it. I mean that. I learned more from my own bugs than from the finished dashboard, and you can't buy that. Everything on this page is what you need to start.

If your goal is to use it every day, read the last three rows honestly. You'd be standing up two data subscriptions, spending weeks building a system around them, and accepting eight failure modes that never throw an error — to arrive at something that still can't tell you where to enter. Mine is already running, already read, with the levels and the live trades attached.

That's the whole comparison. I'd rather put it in front of you than let you find it out in week three.

> 

The part this can't do — timing. This map gives you which names are worth investigating and why. What it can't give you is where to watch and when a name becomes a trade — the level, the invalidation, the entry. That's chart work, and it's what I walk through every week inside the Swing Trading Desk: the names I'm watching and exactly how I'm reading them, while you work your 9-to-5.

What actually lands in the Desk: the skew map every trading day, already read · the weekly watchlist with exact entry, stop and target levels · every trade I take posted live as I take it, not screenshotted afterwards · a room of other people doing this around a 9-to-5. $69/month, cancel any time.

My track record, not a promise of yours: $65K → $300K+ over 24 months · $129K in a year, part-time · ~9x the S&P.

→ See how I trade — inside the Desk


---

Methodology and thresholds reflect my own build as of August 2026. Options data is messy and every number here is a modelling choice — check your own before you act on it.

Built by berttrading.

> Educational content, not financial advice. Do your own research.
