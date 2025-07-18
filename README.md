# Pinterest Feed Live Wallpaper
![Preview](preview.png)

## What is this?

This project turns your **Pinterest board** or **RSS feed** into a **dynamic, real-time live wallpaper** for your **Windows desktop**, powered by a custom Flask server and [Wallpaper Engine](https://store.steampowered.com/app/431960/Wallpaper_Engine/).

You get:
- A beautiful, ever-updating **Pinterest-style grid** of your saved pins.
- Infinite scroll, just like Pinterest itself.
- Runs as your live wallpaper background — not just a static image or slideshow.
- Fully local — no third-party server, no cloud service, just your machine.

---

##  Why did I make this?

Pinterest is where I curate things that inspire me — art, moodboards, aesthetics, ideas.  
I don’t just want to **visit** my inspiration — I want it **living** on my desktop, all the time.  
This project makes my Pinterest **home feed** or **specific board** part of my workspace,  
keeping me surrounded by visuals that spark new ideas.

---

##  How does it work?

- `server.py` → A **Flask server** that fetches your Pinterest RSS feed, parses the image links, and serves them through a `/images` API.
- `slideshow.html` → A minimal **HTML/CSS/JS page** that displays the images in a Pinterest-style infinite grid.
- `Wallpaper Engine` → Loads `http://localhost:5000/` as a **live desktop wallpaper** by embedding the HTML page.

---


##  How to run it

 **Run the server**  
```bash
python server.py
