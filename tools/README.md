# 🎬 Reel-Builder

Erzeugt Faceless-Reels (1080x1920, 9:16) mit Text-Overlays im Schwarz/Gold-Stil
für @feierabend.cashflow. Ton bewusst weggelassen — Trending-Sound in der
Instagram-App draufpacken (Algorithmus-Boost).

## Nutzung
```
python3 tools/reel_builder.py tools/reels/tag1.json tools/output/tag1.mp4
```

## Hintergrund
- `{"type":"gradient"}` → generierter dunkler Look, kein Footage nötig
- `{"type":"clips","files":["a.mp4","b.mp4"]}` → echte Stock-Clips (Pexels/Mixkit)

## Voraussetzungen
- ffmpeg
- Font liegt in `tools/fonts/Anton-Regular.ttf`
