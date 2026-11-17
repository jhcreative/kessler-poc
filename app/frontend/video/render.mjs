// The demo video's render (D4): a take (record.mjs's recordings and log) and beats.json in, the EDL, the frames of
// chrome, the MP4 and the captions out. All the judgement lives in the EDL (edl.json); everything after it is
// mechanism, so a caption fix re-renders without a reshoot: `node render.mjs <take-dir> <out-dir>`.
//
// Sync: each recording starts when its page opens, so the five don't share a clock. record.mjs inverted every page at
// one logged moment before the story and again after it; the frame where each recording goes dark gives that
// recording's offset, and the second flash measures drift. Both are written into the EDL.
import { chromium } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const [takeArg, outArg] = process.argv.slice(2);
if (!takeArg || !outArg) throw new Error("usage: node render.mjs <take-dir> <out-dir>");
const TAKE = resolve(takeArg), OUT = resolve(outArg);
const FRAMES = join(OUT, "frames");
mkdirSync(FRAMES, { recursive: true });
const here = fileURLToPath(new URL(".", import.meta.url));
const FONTS = resolve(here, "../public/fonts");
const script = JSON.parse(readFileSync(join(here, "beats.json"), "utf8"));
const take = JSON.parse(readFileSync(join(TAKE, "events.json"), "utf8"));
const FPS = 30;

// The frame (1920 × 1080): a 2 × 2 grid of the desktop views, the phone at full size on the right, captions below.
const W = 1920, H = 1080;
const L = { pad: 16, label: 30, gap: 14, tileW: 732, tileH: 428, phoneW: 390, phoneH: 844, bandY: 958 };
const col = [L.pad, L.pad + L.tileW + L.gap];
const rowLabel = [L.pad, L.pad + L.label + L.tileH + L.gap];
const rowTile = rowLabel.map((y) => y + L.label);
const phoneX = col[1] + L.tileW + 18;
const TILES = {
  coord: { x: col[0], y: rowTile[0], name: "Coordinator" },
  dispatch: { x: col[1], y: rowTile[0], name: "Dispatch" },
  controller: { x: col[0], y: rowTile[1], name: "Controller" },
  overview: { x: col[1], y: rowTile[1], name: "Overview" },
};
const PHONE = { x: phoneX, y: rowTile[0], name: "Tech's phone" };
const FOCUS = { x: L.pad, y: rowTile[0], w: L.tileW * 2 + L.gap, h: 862, cover: rowTile[1] + L.tileH - rowTile[0] };

// 1. Sync: when each recording sees the flashes.
function darkFrames(file) {
  const out = execFileSync("ffmpeg", ["-hide_banner", "-nostats", "-i", file, "-vf", "scale=64:-1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"], { encoding: "utf8", maxBuffer: 1 << 28, stdio: ["ignore", "pipe", "ignore"] });
  const frames = [];
  let t = null;
  for (const line of out.split("\n")) {
    const m = line.match(/pts_time:([\d.]+)/);
    if (m) t = Number(m[1]);
    const y = line.match(/YAVG=([\d.]+)/);
    if (y && t != null) frames.push({ t, y: Number(y[1]) });
  }
  if (frames.length < 50) throw new Error(`${file}: only ${frames.length} frames read`);
  // A flash: a frame far darker than the one before it.
  const starts = [];
  for (let i = 1; i < frames.length; i++) if (frames[i - 1].y - frames[i].y > 60 && (!starts.length || frames[i].t - starts.at(-1) > 2)) starts.push(frames[i].t);
  return { starts, duration: frames.at(-1).t };
}
const flashes = take.events.filter((e) => e.type === "flash");
if (flashes.length !== 2) throw new Error(`expected 2 flashes in the log, found ${flashes.length}`);
const sources = {};
for (const [view, file] of Object.entries(take.videos)) {
  const { starts, duration } = darkFrames(join(TAKE, file));
  if (starts.length !== 2) throw new Error(`${view}: expected 2 flashes in the video, found ${starts.length} (${starts.join(", ")})`);
  const zero = flashes[0].t / 1000 - starts[0]; // the wall-clock second at which this recording's t=0 sits
  const drift = starts[1] - (flashes[1].t / 1000 - zero);
  sources[view] = { file, zero, flash_s: starts, drift_ms: Math.round(drift * 1000), duration_s: duration };
  console.log(`sync ${view}: flashes at ${starts.map((s) => s.toFixed(2)).join(" and ")} s, drift ${Math.round(drift * 1000)} ms`);
}

// 2. The EDL: the story's span on the wall clock, the beats inside it, each with its layout and caption.
const beatEvents = take.events.filter((e) => e.type === "beat");
const end = take.events.find((e) => e.type === "story-end");
if (!end || beatEvents.length !== script.beats.length) throw new Error("the take is incomplete");
const main = { in: beatEvents[0].t / 1000 - 0.6, out: end.t / 1000 + 1.0 };
const segments = beatEvents.map((e, i) => {
  const b = script.beats.find((x) => x.id === e.id);
  const s = e.t / 1000 - main.in;
  const t = (i + 1 < beatEvents.length ? beatEvents[i + 1].t / 1000 : main.out) - main.in;
  return { beat: b.id, start: i === 0 ? 0 : +s.toFixed(3), end: +t.toFixed(3), layout: b.layout, view: b.view, caption: b.caption };
});
const open = script.cards.open, close = script.cards.close;
const edl = {
  title: "OneFamilyServices ops: one request, five views",
  output: { width: W, height: H, fps: FPS, codec: "h264 High, yuv420p, bt709, faststart", audio: "silent AAC (no music, no voice)" },
  music: null,
  take: { number: take.number, base: take.base, recorded: new Date(beatEvents[0].t).toISOString() },
  sources: Object.fromEntries(Object.entries(sources).map(([v, s]) => [v, { file: s.file, in_s: +(main.in - s.zero).toFixed(3), drift_ms: s.drift_ms }])),
  layout: { tiles: TILES, phone: PHONE, focus: FOCUS, tile: { w: L.tileW, h: L.tileH }, caption_band_y: L.bandY },
  cards: { open, close },
  main: { duration_s: +(main.out - main.in).toFixed(3) },
  segments,
};
for (const [v, s] of Object.entries(edl.sources)) if (s.in_s < 0) throw new Error(`${v} starts after the story does`);
writeFileSync(join(OUT, "edl.json"), JSON.stringify(edl, null, 2));

// 3. The chrome for each beat, and the two cards, drawn in HTML and captured as frames.
const css = `
@font-face { font-family: Plex; font-weight: 400; src: url(file://${FONTS}/ibm-plex-sans-400-latin.woff2); }
@font-face { font-family: Plex; font-weight: 500; src: url(file://${FONTS}/ibm-plex-sans-500-latin.woff2); }
@font-face { font-family: Plex; font-weight: 600; src: url(file://${FONTS}/ibm-plex-sans-600-latin.woff2); }
* { box-sizing: border-box; margin: 0; }
html, body { width: ${W}px; height: ${H}px; background: #1a2129; font-family: Plex, sans-serif; overflow: hidden; }
.label { position: absolute; height: ${L.label}px; line-height: ${L.label}px; font-size: 19px; font-weight: 600; color: #aab4c0; letter-spacing: .01em; }
.label.on { color: #F7941E; }
.frame { position: absolute; border: 3px solid #F7941E; border-radius: 3px; }
.band { position: absolute; left: 0; right: 0; top: ${L.bandY}px; bottom: 0; background: #11161c; display: flex; align-items: center; justify-content: center; padding: 0 80px; }
.caption { color: #fff; font-size: 33px; line-height: 1.3; font-weight: 500; text-align: center; text-wrap: balance; max-width: 1640px; }
.card { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; padding: 0 200px; background: #1a2129; }
.card h1 { color: #fff; font-size: 76px; font-weight: 600; line-height: 1.1; margin-bottom: 44px; text-wrap: balance; }
.card p { color: #d6dde5; font-size: 34px; line-height: 1.45; text-wrap: balance; max-width: 1400px; }
.card .rule { width: 96px; height: 6px; background: #F7941E; margin-bottom: 40px; }
.card .foot { color: #F7941E; font-size: 30px; font-weight: 500; margin-top: 56px; }
`;
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
function chromeHtml(seg) {
  const parts = [];
  const lbl = (x, y, text, on) => parts.push(`<div class="label${on ? " on" : ""}" style="left:${x}px;top:${y - L.label}px">${esc(text)}</div>`);
  const frame = (x, y, w, h) => parts.push(`<div class="frame" style="left:${x - 5}px;top:${y - 5}px;width:${w + 10}px;height:${h + 10}px"></div>`);
  if (seg.layout === "focus") {
    lbl(FOCUS.x, FOCUS.y, TILES[seg.view].name, true);
    frame(FOCUS.x, FOCUS.y, FOCUS.w, FOCUS.h);
  } else {
    for (const [v, t] of Object.entries(TILES)) {
      lbl(t.x, t.y, t.name, seg.view === v);
      if (seg.view === v) frame(t.x, t.y, L.tileW, L.tileH);
    }
  }
  lbl(PHONE.x, PHONE.y, PHONE.name, seg.view === "tech");
  if (seg.view === "tech") frame(PHONE.x, PHONE.y, L.phoneW, L.phoneH);
  parts.push(`<div class="band"><div class="caption">${esc(seg.caption)}</div></div>`);
  return `<!doctype html><meta charset="utf-8"><style>${css}</style><body>${parts.join("")}</body>`;
}
const cardHtml = (c) =>
  `<!doctype html><meta charset="utf-8"><style>${css}</style><body><div class="card"><div class="rule"></div><h1>${esc(c.title)}</h1>${c.lines.map((l) => `<p>${esc(l)}</p>`).join("")}<div class="foot">${esc(c.foot)}</div></div></body>`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H } });
async function shot(html, file) {
  // From a file, so the page may load the app's own font files (file:// from about:blank is refused).
  const htmlFile = file.replace(/\.png$/, ".html");
  writeFileSync(htmlFile, html);
  await page.goto("file://" + htmlFile, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => Promise.all([...document.fonts].map((f) => f.load().catch(() => {}))));
  const fonts = await page.evaluate(() => [...document.fonts].map((f) => `${f.family} ${f.weight} ${f.status}`));
  if (!fonts.length || fonts.some((f) => !f.endsWith("loaded"))) throw new Error(`fonts: ${fonts.join(", ")}`);
  const runts = await page.evaluate(() => {
    // PQ-5e: a caption or card line may not end on a runt (a last line of one or two words).
    const bad = [], checked = [];
    for (const el of document.querySelectorAll(".caption, .card p, .card h1")) {
      const r = document.createRange();
      r.selectNodeContents(el);
      const lines = new Map();
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        const words = n.textContent.split(/(\s+)/);
        let off = 0;
        for (const w of words) {
          if (w.trim()) {
            const wr = document.createRange();
            wr.setStart(n, off); wr.setEnd(n, off + w.length);
            const top = Math.round(wr.getClientRects()[0]?.top ?? 0);
            lines.set(top, (lines.get(top) ?? 0) + 1);
          }
          off += w.length;
        }
      }
      const counts = [...lines.entries()].sort((a, b) => a[0] - b[0]).map((e) => e[1]);
      checked.push(`${counts.join("+")} words`);
      if (counts.length > 1 && counts.at(-1) <= 2) bad.push(el.textContent);
    }
    return { bad, checked };
  });
  // PQ-5a: show the check ran, and on what (words per rendered line, for every block).
  runtLog.push(`${file.split("/").pop()}: ${runts.checked.join(", ")}`);
  if (!runts.checked.length) throw new Error(`runt check found no text in ${file}`);
  if (runts.bad.length) console.log(`RUNT in ${file}: ${runts.bad.join(" | ")}`);
  await page.screenshot({ path: file });
}
const runtLog = [];
const chromeFiles = [];
for (const [i, seg] of segments.entries()) {
  const f = join(FRAMES, `beat-${String(i + 1).padStart(2, "0")}-${seg.beat}.png`);
  await shot(chromeHtml(seg), f);
  chromeFiles.push(f);
}
await shot(cardHtml(open), join(FRAMES, "card-open.png"));
await shot(cardHtml(close), join(FRAMES, "card-close.png"));
await browser.close();
writeFileSync(join(OUT, "runt-check.txt"), runtLog.join("\n") + "\n");
console.log(`runt check: ${runtLog.length} frames checked, lines per block in runt-check.txt`);

// 4. ffmpeg: the chrome as a stream, each recording trimmed to the story and placed, focus beats on top, cards around.
const concat = segments.map((s, i) => `file '${chromeFiles[i]}'\nduration ${(s.end - s.start).toFixed(3)}`).join("\n") + `\nfile '${chromeFiles.at(-1)}'\n`;
writeFileSync(join(FRAMES, "chrome.txt"), concat);
const dur = edl.main.duration_s;
const views = ["coord", "dispatch", "controller", "overview", "tech"];
const args = ["-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", join(FRAMES, "chrome.txt")];
for (const v of views) args.push("-i", join(TAKE, sources[v].file));
args.push("-loop", "1", "-framerate", String(FPS), "-t", String(open.seconds), "-i", join(FRAMES, "card-open.png"));
args.push("-loop", "1", "-framerate", String(FPS), "-t", String(close.seconds), "-i", join(FRAMES, "card-close.png"));
args.push("-f", "lavfi", "-t", String(dur + open.seconds + close.seconds), "-i", "anullsrc=channel_layout=stereo:sample_rate=48000");
const f = [];
f.push(`[0:v]fps=${FPS},scale=${W}:${H},format=yuv420p,trim=duration=${dur},setpts=PTS-STARTPTS[bg0]`);
const within = (v) => segments.filter((s) => s.layout === "focus" && s.view === v).map((s) => `between(t,${s.start},${s.end})`).join("+");
views.forEach((v, i) => {
  const s = edl.sources[v];
  const base = `[${i + 1}:v]trim=start=${s.in_s}:duration=${dur},setpts=PTS-STARTPTS,fps=${FPS},format=yuv420p`;
  if (v === "tech") f.push(`${base},scale=${L.phoneW}:${L.phoneH}:flags=lanczos[t_${v}]`);
  else {
    f.push(`${base},split=2[a_${v}][b_${v}]`);
    f.push(`[a_${v}]scale=${L.tileW}:${L.tileH}:flags=lanczos[t_${v}]`);
    f.push(`[b_${v}]scale=${FOCUS.w}:${FOCUS.h}:flags=lanczos,pad=${FOCUS.w}:${FOCUS.cover}:0:0:color=0x1a2129[f_${v}]`);
  }
});
let cur = "bg0", n = 0;
const over = (src, x, y, enable) => {
  const next = `bg${++n}`;
  f.push(`[${cur}][${src}]overlay=${x}:${y}:eof_action=pass${enable ? `:enable='${enable}'` : ""}[${next}]`);
  cur = next;
};
for (const [v, t] of Object.entries(TILES)) over(`t_${v}`, t.x, t.y);
over("t_tech", PHONE.x, PHONE.y);
for (const v of Object.keys(TILES)) if (within(v)) over(`f_${v}`, FOCUS.x, FOCUS.y, within(v));
f.push(`[${cur}]setsar=1[main]`);
f.push(`[6:v]format=yuv420p,setsar=1[co]`, `[7:v]format=yuv420p,setsar=1[cc]`);
f.push(`[co][main][cc]concat=n=3:v=1:a=0[out]`);
writeFileSync(join(FRAMES, "filter.txt"), f.join(";\n"));
const mp4 = join(OUT, "jahnel-poc-one-request-five-views.mp4");
args.push("-filter_complex_script", join(FRAMES, "filter.txt"), "-map", "[out]", "-map", "8:a",
  "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(FPS),
  "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
  "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", mp4);
execFileSync("ffmpeg", args, { stdio: ["ignore", "ignore", "inherit"] });

// 5. Captions as data: the SRT, cards included, on the final timeline.
const ts = (s) => {
  const ms = Math.round(s * 1000);
  const p = (x, k = 2) => String(x).padStart(k, "0");
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
};
const cues = [
  { s: 0, e: open.seconds, text: `${open.title}\n${open.foot}` },
  ...segments.map((s) => ({ s: s.start + open.seconds, e: s.end + open.seconds, text: s.caption })),
  { s: open.seconds + dur, e: open.seconds + dur + close.seconds, text: `${close.title}\n${close.lines.join(" ")}` },
];
writeFileSync(join(OUT, "jahnel-poc-one-request-five-views.srt"), cues.map((c, i) => `${i + 1}\n${ts(c.s)} --> ${ts(c.e)}\n${c.text}\n`).join("\n"));
console.log(`render: ${mp4}, ${(dur + open.seconds + close.seconds).toFixed(1)} s`);
