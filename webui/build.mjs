#!/usr/bin/env node
/**
 * WebUI builder — single source of truth for the five agent front-ends.
 * Emits a shared stylesheet, a hub page, and one branded page per agent.
 * Run:  node webui/build.mjs   (re-generates everything into webui/)
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const DIR = dirname(fileURLToPath(import.meta.url));

const AGENTS = [
  { slug: "memory-echo", track: "T1 · MemoryAgent", name: "Echo", accent: "#5eead4",
    tagline: "Governed memory under a token budget.",
    blurb: "Embeds memories, recalls them under a strict token budget, and forgets on schedule — the reference agent for the shared brain.",
    models: ["text-embedding-v3", "qwen-plus"],
    demo: { label: "Recall a memory", placeholder: "When is the hackathon due?", button: "Retrieve" } },
  { slug: "showrunner", track: "T2 · AI Showrunner", name: "Showrunner", accent: "#f0abfc",
    tagline: "Turns brain events into a short script.",
    blurb: "Reads recent cross-agent memory_events and dramatizes what the collective has been doing into a short video script.",
    models: ["qwen-plus"],
    demo: { label: "Generate a scene", placeholder: "Dramatize the last 5 events", button: "Write" } },
  { slug: "git-committer", track: "T3 · Agent Society", name: "Committer", accent: "#fdba74",
    tagline: "A debating society for your diffs.",
    blurb: "Pedant, Architect, and Skeptic personas review a diff against shared code conventions, then synthesize one Conventional Commit message.",
    models: ["qwen3-coder-plus", "qwen-plus"],
    demo: { label: "Review a diff", placeholder: "def add(a,b): return a-b", button: "Review" } },
  { slug: "open-translate", track: "T4 · Autopilot", name: "Translate", accent: "#93c5fd",
    tagline: "Glossary-honoring translation with HITL.",
    blurb: "Translates with a shared glossary and translation memory; new terms route to a human-in-the-loop review queue before becoming shared.",
    models: ["qwen-plus"],
    demo: { label: "Translate text", placeholder: "Hello, world", button: "Translate" } },
  { slug: "skippy-concierge", track: "T5 · EdgeAgent", name: "Skippy", accent: "#fca5a5",
    tagline: "Multimodal home concierge that acts.",
    blurb: "Maps a request (text, image, or audio) to a device action over the registry, grounded in device manuals.",
    models: ["qwen-vl-max", "qwen3-omni-flash", "qwen-plus"],
    demo: { label: "Ask Skippy", placeholder: "Dim the living room lights", button: "Act" } },
];

const STYLE = `:root{--bg:#0b0f14;--card:#131a22;--ink:#e6edf3;--mut:#8b98a5;--line:#222c37}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
a{color:inherit;text-decoration:none}.wrap{max-width:980px;margin:0 auto;padding:40px 24px}
header.site{display:flex;align-items:baseline;justify-content:space-between;gap:16px;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:28px}
header.site h1{font-size:20px;margin:0;letter-spacing:.3px}header.site .sub{color:var(--mut);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;transition:.15s transform,.15s border-color}
.card:hover{transform:translateY(-3px)}
.tag{font:12px/1 ui-monospace,monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.12em}
.card h2{margin:.5em 0 .2em;font-size:19px}.card p{color:var(--mut);font-size:14px;margin:.3em 0 1em}
.pill{display:inline-block;font:12px/1 ui-monospace,monospace;padding:5px 9px;border-radius:999px;border:1px solid var(--line);color:var(--mut);margin:0 6px 6px 0}
.hero{display:flex;align-items:center;gap:14px;margin-bottom:8px}.dot{width:14px;height:14px;border-radius:50%}
.demo{margin-top:22px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px}
.demo label{display:block;font-size:13px;color:var(--mut);margin-bottom:8px}
.demo textarea{width:100%;min-height:84px;background:#0e141b;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:12px;font:14px/1.5 ui-monospace,monospace;resize:vertical}
.demo .row{display:flex;gap:10px;margin-top:12px;align-items:center}
button.go{border:0;border-radius:10px;padding:11px 18px;font-weight:600;color:#0b0f14;cursor:pointer}
.out{margin-top:14px;white-space:pre-wrap;font:13px/1.55 ui-monospace,monospace;color:var(--ink);min-height:22px}
.note{color:var(--mut);font-size:12px}.back{color:var(--mut);font-size:14px}
footer{margin-top:40px;color:var(--mut);font-size:13px;border-top:1px solid var(--line);padding-top:16px}`;

const shell = (title, body) => `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title><link rel="stylesheet" href="/style.css"></head>
<body><div class="wrap">${body}<footer>qwen-agent-collective · five agents, one shared brain · <span class="note">Global AI Hackathon with Qwen Cloud</span></footer></div></body></html>`;

function hub() {
  const cards = AGENTS.map(a => `<a class="card" href="/${a.slug}.html" style="border-top:3px solid ${a.accent}">
    <div class="tag">${a.track}</div><h2>${a.name}</h2><p>${a.tagline}</p>
    ${a.models.map(m => `<span class="pill">${m}</span>`).join("")}</a>`).join("\n");
  return shell("Qwen Agent Collective", `
   <header class="site"><h1>Qwen Agent Collective</h1><span class="sub">five specialist agents · one shared brain</span></header>
   <p class="note" style="margin-top:-12px;margin-bottom:24px">Pick an agent to open its console.</p>
   <div class="grid">${cards}</div>`);
}

function page(a) {
  return shell(`${a.name} — ${a.track}`, `
   <header class="site"><h1>${a.name}</h1><span class="sub">${a.track}</span></header>
   <a class="back" href="/">← all agents</a>
   <div class="hero" style="margin-top:18px"><span class="dot" style="background:${a.accent}"></span>
     <strong style="font-size:20px">${a.tagline}</strong></div>
   <p style="color:var(--mut);max-width:62ch">${a.blurb}</p>
   <div>${a.models.map(m => `<span class="pill">${m}</span>`).join("")}</div>
   <div class="demo">
     <label for="in">${a.demo.label}</label>
     <textarea id="in" placeholder="${a.demo.placeholder}"></textarea>
     <div class="row"><button class="go" style="background:${a.accent}" onclick="run()">${a.demo.button}</button>
       <span class="note">calls <code>/api/${a.slug}</code> when the backend is wired</span></div>
     <div class="out" id="out"></div>
   </div>
   <script>
   async function run(){
     const out=document.getElementById('out'), q=document.getElementById('in').value.trim();
     if(!q){out.textContent='Enter something first.';return}
     out.textContent='…';
     try{
       const r=await fetch('/api/${a.slug}',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({input:q})});
       if(!r.ok) throw new Error('HTTP '+r.status);
       const j=await r.json(); out.textContent=j.output||JSON.stringify(j,null,2);
     }catch(e){ out.textContent='[demo] backend not wired yet ('+e.message+').\\nThis console is ready; connect /api/${a.slug} to the ${a.name} agent.'; }
   }
   </script>`);
}

mkdirSync(DIR, { recursive: true });
writeFileSync(join(DIR, "style.css"), STYLE);
writeFileSync(join(DIR, "index.html"), hub());
for (const a of AGENTS) writeFileSync(join(DIR, `${a.slug}.html`), page(a));
console.log(`built: style.css, index.html, ${AGENTS.map(a => a.slug + ".html").join(", ")}`);
