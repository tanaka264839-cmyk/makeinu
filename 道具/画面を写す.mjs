// 負け犬の癒し：見た目の確かめ。裏で Chrome（無ければ Edge）を立て、スマホの幅で開いて写す・操作して位置を測る。
// Playwright のブラウザは別の会話と共用で取り合いになるので使わない。入れる物はゼロ（Node 24 の WebSocket と、入っているブラウザ）。
// 使い方：node 画面を写す.mjs <手順.json> <写す先フォルダ> [場のURL 既定 http://127.0.0.1:8765]
// 手順の1段：{名前, 開く, 幅, 高さ, 暗い, 全部, する, 読み込む, 測る, 期待}。開くの中の {場} は場のURLに置き換える。
// 期待があれば、測った値と比べて合否を出す。名乗るなど書き込む段があるので、記録の写しで立てた場に向けて使う。
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [手順の場所, 写す先, 場 = "http://127.0.0.1:8765"] = process.argv.slice(2);
const 手順 = JSON.parse(readFileSync(手順の場所, "utf8").replace(/^﻿/, "")); // PowerShell が書いた手順は頭に BOM が付く
mkdirSync(写す先, { recursive: true });
const ブラウザ = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].find(existsSync);
const 港 = 9334;
const 立てた = spawn(ブラウザ, [
  "--headless=new", `--remote-debugging-port=${港}`, `--user-data-dir=${join(tmpdir(), "makeinu-gamen")}`,
  "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const 待つ = (ms) => new Promise((r) => setTimeout(r, ms));
let 頁 = null;
for (let i = 0; i < 50 && !頁; i++) {
  await 待つ(200);
  try { 頁 = (await (await fetch(`http://127.0.0.1:${港}/json/list`)).json()).find((t) => t.type === "page"); } catch {}
}
const ws = new WebSocket(頁.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let 番 = 0;
const 待ち = new Map();
const 聞き手 = new Set();
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && 待ち.has(m.id)) { const { 済, 失 } = 待ち.get(m.id); 待ち.delete(m.id); m.error ? 失(new Error(JSON.stringify(m.error))) : 済(m.result); }
  else if (m.method) for (const l of 聞き手) l(m);
});
const 送る = (method, params = {}) => new Promise((済, 失) => { const i = ++番; 待ち.set(i, { 済, 失 }); ws.send(JSON.stringify({ id: i, method, params })); });
const 起きるまで = (名前, ms = 15000) => new Promise((済, 失) => {
  const t = setTimeout(() => { 聞き手.delete(l); 失(new Error("待ちきれない " + 名前)); }, ms);
  const l = (m) => { if (m.method === 名前) { clearTimeout(t); 聞き手.delete(l); 済(m.params); } };
  聞き手.add(l);
});
const 式 = async (js) => {
  const r = await 送る("Runtime.evaluate", { expression: js, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + " " + (r.exceptionDetails.exception?.description ?? ""));
  return r.result.value;
};
const 幅を決める = (幅, 高さ) => 送る("Emulation.setDeviceMetricsOverride", { width: 幅, height: 高さ, deviceScaleFactor: 2, mobile: 幅 < 800 });
const 合うか = (期待, 測った) =>
  typeof 期待 === "object" && 期待 !== null
    ? Object.entries(期待).every(([k, v]) => JSON.stringify(測った?.[k]) === JSON.stringify(v))
    : JSON.stringify(期待) === JSON.stringify(測った);
await 送る("Page.enable");
await 送る("Runtime.enable");

const 結果 = [];
for (const 段 of 手順) {
  const 幅 = 段.幅 ?? 390, 高さ = 段.高さ ?? 844;
  await 幅を決める(幅, 高さ);
  await 送る("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: 段.暗い ? "dark" : "light" }] });
  if (段.開く) { const 読めた = 起きるまで("Page.loadEventFired"); await 送る("Page.navigate", { url: 段.開く.replace("{場}", 場) }); await 読めた; }
  if (段.する) { const 読めた = 段.読み込む ? 起きるまで("Page.loadEventFired") : null; await 式(段.する); if (読めた) await 読めた; }
  await 待つ(300);
  const 測った = 段.測る ? await 式(段.測る) : null;
  if (段.名前) {
    if (段.全部) { await 幅を決める(幅, await 式("document.documentElement.scrollHeight")); await 待つ(200); }
    const 絵 = await 送る("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(写す先, 段.名前 + ".png"), Buffer.from(絵.data, "base64"));
  }
  const 行 = { 段: 段.名前 ?? 段.開く ?? 段.する, url: await 式("location.href"), 測った };
  if ("期待" in 段) 行.合否 = 合うか(段.期待, 測った) ? "合格" : "不合格";
  結果.push(行);
}
writeFileSync(join(写す先, "測った結果.json"), JSON.stringify(結果, null, 1));
console.log(JSON.stringify(結果, null, 1));
const 落ちた = 結果.filter((行) => 行.合否 === "不合格").length;
console.log(落ちた ? `不合格 ${落ちた} 段` : "期待のある段はすべて合格");
ws.close();
立てた.kill();
process.exit(落ちた ? 1 : 0);
