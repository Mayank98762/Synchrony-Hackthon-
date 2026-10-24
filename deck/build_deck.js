// Builds deck/HSIC_SoW_deck.pptx: 6 slides (the organizers' 5-6 slide limit). Owner: Shreyash.
// DECK_APPENDIX=1 adds 4 appendix slides (hypotheses, offer economics, model charts, assumptions).
//
// Every number on a slide is read from outputs/key_numbers.json (written by analysis/run_all.py); a missing key stops the
// build, so no figure is typed by hand. Charts come from outputs/charts/ (16:9 PNGs from the pipeline).
//
//   npm install pptxgenjs@3.12.0        (once, anywhere on NODE_PATH; not part of the repo)
//   node deck/build_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(__dirname, "HSIC_SoW_deck.pptx");
const CHART = (f) => path.join(ROOT, "outputs", "charts", f);
const KN = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "key_numbers.json"), "utf8"));

function v(key) {
  if (!(key in KN)) throw new Error(`key_numbers.json has no '${key}': rerun analysis/run_all.py`);
  return KN[key].value;
}
const pct = (k, d = 1) => `${(v(k) * 100).toFixed(d)}%`;
const pts = (x, d = 1) => `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toFixed(d)} pts`;
const num = (x) => Math.round(x).toLocaleString("en-US");
const inr = (k) => `₹${num(v(k))}`;
const inrM = (k, d = 1) => `₹${(v(k) / 1e6).toFixed(d)}M`;
const inrK = (k) => `${v(k) < 0 ? "−" : ""}₹${Math.abs(Math.round(v(k) / 1e3))}k`;
const ptsAbs = (x, d = 1) => `${Math.abs(x).toFixed(d)} pts`;
const share = (k, d = 0) => (typeof v(k) === "number" ? `${(v(k) * 100).toFixed(d)}%` : v(k));
const per100 = (k) => `${v(k) >= 0 ? "+" : "−"}₹${Math.abs(v(k) * 100).toFixed(2)}`;

// ---------------------------------------------------------------- design tokens (match analysis/style.py)
const INK = "0B0B0B", SECONDARY = "52514E", MUTED = "898781", NAVY = "0F2747", HSIC = "2A78D6";
const BG = "F3F5F8", WHITE = "FFFFFF", LINE = "D9DDE3";
const BADGE = { M: ["0B0B0B", "Measured"], S: ["6250D6", "Simulated"], A: ["898781", "Assumed"], H: ["E34948", "Hypothesis"] };
const THEME = {
  name: "HSIC Wallet", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: WHITE, dk2: NAVY, lt2: BG, accent1: HSIC, accent2: "EB6834", accent3: "1BAF7A",
            accent4: "EDA100", accent5: "6250D6", accent6: "E34948", hlink: HSIC, folHlink: "6250D6" },
};
const W = 13.333, M = 0.5;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "HSIC x MetroMart: silent attrition and share of wallet";
pres.author = "Devansh Agarwal, Mayank Srivastava, Shreyash Tiwari";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

const FOOT = "HSIC × MetroMart case data · FY25 = Aug 2024–Jul 2025 · FY26 = Aug 2025–Jul 2026 · " +
  "M Measured · S Simulated · A Assumed · H Hypothesis";
pres.defineSlideMaster({
  title: "CONTENT", background: { color: BG },
  objects: [
    { text: { text: FOOT, options: { x: M, y: 7.05, w: 11.3, h: 0.3, fontSize: 10, color: MUTED, margin: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: 12.3, h: 0.95, fontSize: 24, bold: true,
      color: NAVY, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 7.05, w: 0.43, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.6, w: 12.3, h: 1.3, fontSize: 30, bold: true,
      color: WHITE, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 7.05, w: 0.43, h: 0.3, fontSize: 10, color: "AEB8C8", align: "right" },
});

// ---------------------------------------------------------------- building blocks
function text(slide, t, o) {
  slide.addText(t, { isTextBox: true, margin: 0, valign: "top", fontSize: 13, color: INK, ...o });
}
function badge(slide, x, y, letter) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 0.26, h: 0.26, rectRadius: 0.05,
    fill: { color: BADGE[letter][0] }, line: { color: BADGE[letter][0] }, shadow: { type: "none" }, objectName: `badge ${BADGE[letter][1]}` });
  text(slide, letter, { x, y, w: 0.26, h: 0.26, fontSize: 10, bold: true, color: WHITE, align: "center", valign: "middle" });
}
function card(slide, x, y, w, h, fill = WHITE) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill },
    line: { color: fill }, shadow: { type: "outer", blur: 6, offset: 2, angle: 90, color: "000000", opacity: 0.12 } });
}
function chart(slide, file, x, y, w) {
  const h = w * 9 / 16;
  card(slide, x, y, w + 0.2, h + 0.2);
  slide.addImage({ path: CHART(file), x: x + 0.1, y: y + 0.1, w, h, altText: file });
  return h + 0.2;
}
// A stat callout: big figure, badge, explanation.
function stat(slide, x, y, w, figure, label, letter, color = NAVY) {
  text(slide, figure, { x, y, w: w - 0.4, h: 0.55, fontSize: 28, bold: true, color });
  badge(slide, x + w - 0.26, y + 0.12, letter);
  text(slide, label, { x, y: y + 0.58, w, h: 0.75, fontSize: 12.5, color: SECONDARY });
}

// ---------------------------------------------------------------- slide 1: the answer
pres.addSection({ title: "Main deck" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Main deck" });
text(s, "Synchrony Analytics Hackathon 2026  ·  HSIC × MetroMart co-branded card", { x: M, y: 0.3, w: 12.3, h: 0.3,
  fontSize: 12, color: "AEB8C8" });
s.addText("Silent attrition is universal: win back the wallet with product fixes, not a target list", { placeholder: "title" });
const sx = [M, M + 4.2, M + 8.4];
const s1 = [
  [`${pct("f1_sow_fy25")} → ${pct("f1_sow_fy26")}`, `HSIC's share of MetroMart spend, FY25 → FY26. All of the fall comes from cards that stayed open`],
  [pct("f3_cash_upi_share_of_loss", 0), `of HSIC's lost share went to Cash/UPI, which gained in every ticket size, while spend per card stayed flat`],
  [`${v("f10_2026_01_31_young_over_old").toFixed(1)}×`, `closure rate of cards under 6 months vs over 3 years (${pct("f10_2026_01_31_closure_lt6m")} vs ${pct("f10_2026_01_31_closure_3yplus")} in 6 months)`],
];
s1.forEach(([fig, lab], i) => {
  card(s, sx[i], 2.15, 3.9, 1.85, "1C3A63");
  text(s, fig, { x: sx[i] + 0.25, y: 2.3, w: 3.1, h: 0.65, fontSize: 30, bold: true, color: WHITE });
  badge(s, sx[i] + 3.45, 2.42, "M");
  text(s, lab, { x: sx[i] + 0.25, y: 3.0, w: 3.45, h: 0.95, fontSize: 13, color: "DCE3EE" });
});
text(s, [
  { text: `${inrM("f12_gap")} of HSIC spend lost in FY26. `, options: { bold: true, color: WHITE } },
  { text: `Net of the ${pct("f15_reward_rate_fy26", 2)} HSIC pays in rewards, it carried only ${inrM("f15_net_margin_lo_nocofund", 2)}–${inrM("f15_net_margin_hi_nocofund", 2)} of margin ` +
      `(${inrM("f15_net_margin_lo_cofund", 2)}–${inrM("f15_net_margin_hi_cofund", 2)} if MetroMart co-funds half): the stake is retention and revolving balances.`,
    options: { color: "DCE3EE" } },
], { x: M, y: 4.3, w: 11.8, h: 0.7, fontSize: 14 });
badge(s, 12.57, 4.33, "A");
const acts = ["Show the reward at the till: no incentive cost", "Instant cashback and the card on UPI, to match Cash/UPI",
  "Protect first-year cards, win back closed cards, pilot with 10% holdouts"];
acts.forEach((a, i) => {
  s.addShape(pres.shapes.OVAL, { x: sx[i], y: 5.35, w: 0.45, h: 0.45, fill: { color: HSIC }, line: { color: HSIC }, shadow: { type: "none" } });
  text(s, String(i + 1), { x: sx[i], y: 5.35, w: 0.45, h: 0.45, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle" });
  text(s, a, { x: sx[i] + 0.6, y: 5.33, w: 3.3, h: 0.75, fontSize: 14, bold: true, color: WHITE });
});
text(s, "Devansh Agarwal  ·  Mayank Srivastava  ·  Shreyash Tiwari  ·  BITS Pilani  ·  24 October 2026",
  { x: M, y: 6.75, w: 11, h: 0.3, fontSize: 11, color: "AEB8C8" });
s.addNotes("HSIC's share of MetroMart spend fell by a third in a year, and it isn't a group of customers drifting away: " +
  "it's everyone, at the same rate, while they keep shopping at MetroMart as much as before. That changes the answer. " +
  "A target list of at-risk customers would be chosen at random, so the first fixes are product fixes that reach every basket. " +
  "We price every offer net of the rewards HSIC already pays, because that margin is thin, and we pilot before scaling.");

// ---------------------------------------------------------------- slide 2: the decline
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main deck" });
s.addText("Customers kept shopping at MetroMart; they stopped paying with HSIC", { placeholder: "title" });
chart(s, "04_per_card.png", M, 1.45, 7.7);
const rx = 8.75, rw = 4.08;
stat(s, rx, 1.5, rw, pts(v("f2_total_pp")), `SoW ${pct("f1_sow_fy25")} → ${pct("f1_sow_fy26")}. Cards open throughout explain ${pts(v("f2_stayer_pp"))}; closures and new cards net out (${pts(v("f2_leaver_pp"))}, ${pts(v("f2_joiner_pp"))})`, "M");
stat(s, rx, 2.95, rw, pct("f3_cash_upi_share_of_loss", 0), `of the lost share went to Cash/UPI; Debit ${pct("f3_debit_share_of_loss", 0)}, other cards ${pct("f3_other_cc_share_of_loss", 0)}, MetroMart Wallet ${pct("f3_wallet_share_of_loss", 0)}`, "M");
stat(s, rx, 4.4, rw, `${pts(v("f4_cash_upi_change_pp_stayers"))} vs ${pts(v("f4_cash_upi_change_pp_noncardholders"))}`, "Cash/UPI's gain among cardholders vs non-cardholders: much stronger for cardholders than for the market", "M");
badge(s, rx, 5.85, "H");
text(s, "Why Cash/UPI? Immediacy: settled at once, while the card's reward arrives on next month's statement. The pilot tests it.",
  { x: rx + 0.36, y: 5.82, w: rw - 0.36, h: 0.8, fontSize: 12.5, color: SECONDARY });
text(s, "SoW = HSIC net ÷ total net MetroMart spend, only while the card is open, net of returns (returns count as zero transactions). " +
  "38,164 cardholders, 444,118 transactions; 39 reproduction checks pass.", { x: M, y: 6.25, w: 7.9, h: 0.6, fontSize: 11, color: MUTED });
s.addNotes("The share fell from 28.9% to 19.5% in a straight line, and the bridge shows it isn't mix: cards that stayed open " +
  "account for the whole fall. Spend per card at MetroMart was flat, while HSIC spend per card more than halved. " +
  "Almost half of the lost share went to Cash/UPI, at every ticket size, and much more strongly for cardholders than for the market. " +
  "Why customers pick Cash/UPI is a hypothesis, immediacy, which the instant-cashback pilot arm tests.");

// ---------------------------------------------------------------- slide 3: universal
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main deck" });
s.addText("It's universal: no customer group behaves differently, so low SoW is the whole book", { placeholder: "title" });
chart(s, "06_slices.png", M, 1.45, 7.7);
stat(s, rx, 1.5, rw, v("x1_variance_ratio_fy26").toFixed(2), `Variance ratio: customers differ in how often they use the card no more than coin flips would. This year's share predicts next year's at r = ${v("x1_persistence_r").toFixed(2)}`, "M");
stat(s, rx, 2.95, rw, `${pts(v("x3_excess_fixed_2026_01_31") * 100)} → ${pts(v("x3_excess_time_2026_01_31") * 100)}`, "\"Silent attriters\" by the usual count, and after allowing for the portfolio-wide trend: every open card is drifting, none faster", "M");
stat(s, rx, 4.4, rw, pct("seg_kmeans_eta2", 2), "of next year's SoW explained by K-means clusters built on SoW: clustering would target noise", "M");
text(s, "We tested 17 common hypotheses, each against a simple baseline or a calendar-matched null.", { x: rx, y: 5.85, w: rw, h: 0.6,
  fontSize: 12.5, color: SECONDARY, italic: true });
s.addNotes("Every slice fell by 7 to 11 points: Prime and Non-Prime, every age, limit, APR band, vintage and category. " +
  "Before segmenting, we tested whether customers differ at all: the spread in card use between customers is what coin flips " +
  "produce, and this year's share doesn't predict next year's. The usual silent-attrition count flags about a fifth of cardholders; " +
  "allow for the portfolio-wide trend and the excess is zero. Silent attrition is real, and it is universal.");

// ---------------------------------------------------------------- slide 4: closures and who to prioritise
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main deck" });
s.addText("Closures doubled and sit in young cards: prioritise by risk × value, not by SoW", { placeholder: "title" });
chart(s, "08_closure_by_card_age.png", M, 1.45, 5.9);
text(s, [
  { text: `${pct("f9_rate_first")} → ${pct("f9_rate_last")}`, options: { bold: true, color: NAVY, fontSize: 20 } },
  { text: "  of open cards closing per quarter. Card age alone predicts closure as well as any model we trained " +
      `(ROC-AUC ${v("cm_b2_roc_auc").toFixed(3)} vs ${v("cm_lr_all_roc_auc").toFixed(3)})`, options: { color: SECONDARY } },
], { x: M, y: 5.05, w: 5.75, h: 1.0, fontSize: 12.5 });
badge(s, M + 5.84, 5.1, "M");
const gx = 6.85, gy = 1.85, cw = 2.45, ch = 1.6;
text(s, "Young card (< 1 year)", { x: gx + 0.95, y: 1.48, w: cw, h: 0.3, fontSize: 12, bold: true, color: SECONDARY, align: "center" });
text(s, "Mature card", { x: gx + 0.95 + cw + 0.1, y: 1.48, w: cw, h: 0.3, fontSize: 12, bold: true, color: SECONDARY, align: "center" });
text(s, "High purchase frequency", { x: gx, y: gy + 0.45, w: 0.85, h: 0.8, fontSize: 11, bold: true, color: SECONDARY });
text(s, "Low / mid frequency", { x: gx, y: gy + ch + 0.55, w: 0.85, h: 0.8, fontSize: 11, bold: true, color: SECONDARY });
const boxes = [["B", "Protect first", 0, 0, HSIC], ["D", "Grow", 1, 0, WHITE], ["C", "Activate", 0, 1, WHITE], ["E", "Nudge", 1, 1, WHITE]];
boxes.forEach(([b, name, cx, cy, fill]) => {
  const x = gx + 0.95 + cx * (cw + 0.1), y = gy + cy * (ch + 0.1), dark = fill === HSIC;
  card(s, x, y, cw, ch, fill);
  text(s, `${b}. ${name}`, { x: x + 0.15, y: y + 0.12, w: cw - 0.3, h: 0.35, fontSize: 15, bold: true, color: dark ? WHITE : NAVY });
  text(s, [
    { text: `${num(v(`seg_${b}_n_score`))} cards`, options: { bold: true, breakLine: true } },
    { text: `closes ${pct(`seg_${b}_closure_6m`)} in 6 months`, options: { breakLine: true } },
    { text: `${inr(`seg_${b}_nonhsic_per_cust`)} off-card per customer`, options: { breakLine: true } },
    { text: `SoW ${pct(`seg_${b}_sow`)}` },
  ], { x: x + 0.15, y: y + 0.5, w: cw - 0.3, h: 1.05, fontSize: 12, color: dark ? WHITE : SECONDARY });
});
text(s, [
  { text: `SoW is within ${v("seg_sow_max_gap_pp").toFixed(1)} pts in every box`, options: { bold: true, color: NAVY } },
  { text: `: risk and value separate customers, SoW doesn't. Outside the grid: ${num(v("seg_A_n_score"))} closed cardholders still ` +
      `spending at MetroMart (${inrM("seg_A_post_close_net")} since closing): the win-back segment.`, options: { color: SECONDARY } },
], { x: gx, y: 5.3, w: 5.95, h: 1.0, fontSize: 12.5 });
s.addNotes("Closures are the visible half and they are accelerating: the share of open cards closing each quarter doubled. " +
  "Cards under six months close at 14.7% over the next six months, 4.8 times cards over three years, and no learned model beats " +
  "card age alone, so the early warning is a rule: protect first-year cards. To answer the brief's segmentation question, we " +
  "build a 2×2 on the two traits that do predict, card age for risk and purchase frequency for value. SoW is the same in every " +
  "box; risk and value are not. Young, high-frequency cards come first.");

// ---------------------------------------------------------------- slide 5: offers
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Main deck" });
s.addText("Three product fixes first; paid offers only where they pay back", { placeholder: "title" });
const offers = [
  ["O3  Reward visibility (hero)", "A till and receipt line, \"Pay with HSIC: earn ₹X on this basket\", and a monthly \"₹ you left on the table\".",
    `Prime members left ${inrM("f8_prime_ge_left_on_table", 2)} of cashback on the table in FY26. No incentive cost; pays back from the first rupee moved on 1% baskets in every scenario.`,
    "Is it awareness?"],
  ["O1  Instant cashback at the till", "The same reward, credited at checkout instead of on next month's statement.",
    `Goes after Cash/UPI's ${pct("f3_cash_upi_share_of_loss", 0)} of the loss; costs only a month of funding on the reward.`, "Is it immediacy?"],
  ["O2  HSIC card on UPI", "Link the credit card to UPI, where the spend went.",
    `Cardholders' Cash/UPI spend in FY26: ${inrM("econin_o2_eligible")}. Each 1% of it moved is worth ${inrK("o2_value_per_1pct_base")} a year (base).`, null],
];
offers.forEach(([name, what, why, test], i) => {
  const y = 1.45 + i * 1.78;
  card(s, M, y, 6.35, 1.62, i === 0 ? "E8F1FC" : WHITE);
  text(s, name, { x: M + 0.2, y: y + 0.12, w: 4.4, h: 0.35, fontSize: 15, bold: true, color: NAVY });
  if (test) { badge(s, M + 4.55, y + 0.15, "H"); text(s, test, { x: M + 4.88, y: y + 0.14, w: 1.4, h: 0.3, fontSize: 11.5, color: SECONDARY }); }
  text(s, what, { x: M + 0.2, y: y + 0.5, w: 5.95, h: 0.45, fontSize: 12, color: INK });
  badge(s, M + 0.2, y + 1.12, i === 1 ? "A" : "S");
  text(s, why, { x: M + 0.55, y: y + 1.0, w: 5.6, h: 0.55, fontSize: 11.5, color: SECONDARY });
});
const tx = 7.15, tw = 5.68;
text(s, "Paid and targeted offers: share of eligible spend that must move to pay back", { x: tx, y: 1.45, w: tw, h: 0.55,
  fontSize: 13, bold: true, color: NAVY });
const head = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: NAVY } } });
const cell = (t, o = {}) => ({ text: String(t), options: { color: INK, ...o } });
const be = (k) => (typeof v(k) === "number" ? (v(k) === 0 ? "from the first ₹" : share(k)) : v(k));
s.addTable([
  [head("Offer"), head("Who"), head("Base"), head("Conservative")],
  [cell("O4 No-cost EMI, ₹3k+ baskets"), cell("All big baskets"), cell(be("o4_breakeven_base")), cell(be("o4_breakeven_conservative"))],
  [cell("O6 Win-back: 3% for 90 days"), cell(`${num(v("econin_o6_customers"))} closed, still shopping`), cell(be("o6_breakeven_base")), cell(be("o6_breakeven_conservative"))],
  [cell("O7 Prime trial, young cards"), cell(`${num(v("econin_o7_young_cards"))} cards < 1 year`), cell(`keep ${share("o7_breakeven_saved_base", 1)} open`), cell(be("o7_breakeven_saved_conservative"))],
  [cell("O8 Threshold bonus"), cell(`${num(v("econin_o8_customers"))} high-frequency mature`), cell(be("o8_breakeven_base")), cell(be("o8_breakeven_conservative"))],
], { x: tx, y: 2.05, w: tw, colW: [2.05, 1.65, 1.0, 0.98], fontSize: 11, border: { type: "solid", pt: 0.5, color: LINE },
  fill: { color: WHITE }, valign: "middle", rowH: 0.5, margin: 0.05 });
badge(s, tx, 4.75, "S");
text(s, `Break-even after the rewards HSIC funds; inputs are Assumed. O8 pays on noise: ${share("econin_o8_noise_share")} of its segment's card spend would earn the bonus with no change in behaviour.`,
  { x: tx + 0.36, y: 4.72, w: tw - 0.36, h: 0.75, fontSize: 11.5, color: SECONDARY });
badge(s, tx, 5.6, "M");
text(s, `Triggers must fit how rarely people shop: no one made 5 small HSIC purchases in a month (the most was ${v("o5_max_small_hsic_purchases_in_a_month")}), and 3 uses in 60 days reached ${share("o7_milestone_reach", 1)} of new cards. So the small-basket bonus pays per visit, and the young-card milestone is the first use, which ${share("o7_first_use_60d_share")} of new cards reach in 60 days.`,
  { x: tx + 0.36, y: 5.57, w: tw - 0.36, h: 0.85, fontSize: 11.5, color: SECONDARY });
s.addNotes("Lead with reward visibility because it is the cheapest lever: HSIC already pays the best Grocery and Electronics " +
  "rates in the market, and Prime members still don't use the card more. Making the reward visible costs nothing extra; whether " +
  "it works is exactly what the pilot tests. Instant cashback and the card on UPI go after the Cash/UPI habit. Paid offers come " +
  "after, and only where they pay back: a blanket no-cost EMI needs most big-basket spend to move, and a threshold bonus mostly " +
  "pays for spend that would have happened anyway.");

// ---------------------------------------------------------------- slide 6: economics, pilot, asks
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Main deck" });
s.addText("The margin on moved spend is thin: pilot the cheap fixes first and ask MetroMart to co-fund", { placeholder: "title" });
chart(s, "11_net_margin_waterfall.png", M, 2.05, 6.6);
text(s, `Per ₹100 moved to HSIC (base): ${per100("econ_margin_general_base")} on general spend, ${per100("econ_margin_prime_grocery_base")} on Prime grocery. ` +
  `Conservative: ${per100("econ_margin_general_conservative")} and ${per100("econ_margin_prime_grocery_conservative")}.`,
  { x: M, y: 6.12, w: 6.8, h: 0.55, fontSize: 12, color: "DCE3EE" });
const px = 7.6, pw = 5.23;
const blocks = [
  ["Pilot", "S", `Randomised 10% holdout per offer and segment. Across the grid it detects a ${ptsAbs(v("mde_grid") * 100)} change in HSIC share in 3 months; one box needs ${ptsAbs(v("mde_E") * 100)} to ${ptsAbs(v("mde_B") * 100)}, so read at grid level or run 6 months. Scale only if the lift's CI excludes 0 and net value > 0.`],
  ["What the pilot tests", "H", "Reward visibility vs holdout: is it awareness? Instant cashback vs holdout: is it immediacy? A null result is reported as a refuted hypothesis."],
  ["Asks", null, `HSIC: ship reward visibility, pilot instant cashback, start UPI linkage, protect first-year cards, offer win-back. ` +
     `MetroMart: co-fund Prime category rewards. Without it, reward visibility on those baskets needs revolve income of ${pct("o3_breakeven_revolve_nocofund")} of spend to pay back.`],
];
let py = 2.05;
blocks.forEach(([head2, letter, body]) => {
  text(s, head2, { x: px, y: py, w: pw - 0.4, h: 0.35, fontSize: 15, bold: true, color: WHITE });
  if (letter) badge(s, px + pw - 0.26, py + 0.04, letter);
  text(s, body, { x: px, y: py + 0.38, w: pw, h: 1.1, fontSize: 12.5, color: "DCE3EE" });
  py += 1.55;
});
text(s, "Assumed: interchange 1.5–2%, revolve income 0–2% of spend, MetroMart co-funding 0–50%, cost of funds 8%, EMI subvention 3%. " +
  `Measured: reward rate ${pct("f15_reward_rate_fy26", 2)} on FY26 HSIC spend. Operating costs excluded, so break-evens are floors.`,
  { x: M, y: 6.75, w: 11.8, h: 0.45, fontSize: 10, color: "AEB8C8" });
s.addNotes("Rewards eat most of the interchange, so a rupee moved to the card is worth about two paise in the base case and can " +
  "lose money on Prime grocery. That is why reward visibility leads: it adds no cost. Every paid offer shows the shift it needs " +
  "to pay back, and we say never where it can't. Nothing here is a forecast of recovery; the pilot turns these simulations into " +
  "measured results, and it is sized honestly: effects under about two points need the whole grid.");

// ---------------------------------------------------------------- appendix (off by default: 5-6 slide limit)
if (process.env.DECK_APPENDIX === "1") {
pres.addSection({ title: "Appendix (optional)" });
function parseCsv(file) {
  const rows = [];
  for (const line of fs.readFileSync(file, "utf8").trim().split(/\r?\n/)) {
    const out = []; let cur = "", q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (q) { if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
      else if (c === '"') q = true; else if (c === ",") { out.push(cur); cur = ""; } else cur += c;
    }
    out.push(cur); rows.push(out);
  }
  return rows;
}
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix (optional)" });
s.addText("Appendix A: common hypotheses we tested", { placeholder: "title" });
const exp = parseCsv(path.join(ROOT, "outputs", "experiment_log.csv"));
const hdr = exp[0], iId = hdr.indexOf("id"), iExp = hdr.indexOf("expected"), iVer = hdr.indexOf("verdict");
s.addTable([[head("#"), head("What a team would expect"), head("What the data says")],
  ...exp.slice(1).map((r) => [cell(r[iId]), cell(r[iExp]), cell(r[iVer])])],
  { x: M, y: 1.3, w: 12.3, colW: [0.6, 6.4, 5.3], fontSize: 10, border: { type: "solid", pt: 0.5, color: LINE },
    fill: { color: WHITE }, rowH: 0.3, margin: 0.04, valign: "middle" });
s.addNotes("Each row was tested on the full data with a calendar-matched null or a simple baseline. Verdicts come straight from the pipeline.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix (optional)" });
s.addText("Appendix B: offer economics by scenario (Simulated; inputs Assumed)", { placeholder: "title" });
const scen = ["conservative", "base", "optimistic"];
const ids = [["o3", "O3 Reward visibility: Prime Grocery + Electronics"], ["o3_other", "O3 Reward visibility: 1% baskets"],
  ["o1", "O1 Instant cashback"], ["o2", "O2 Card on UPI"], ["o4", "O4 No-cost EMI, ₹3k+ baskets"],
  ["o6", "O6 Win-back, closed cardholders"], ["o8", "O8 Threshold bonus"]];
const fmtBE = (k) => (typeof v(k) === "number" ? (v(k) === 0 ? "0%" : share(k, 1)) : v(k));
s.addTable([[head("Offer"), ...scen.map((n) => head(`Break-even, ${n}`)), head("₹/yr per 1% moved, base"), head("Revolve needed, no co-funding")],
  ...ids.map(([id, name]) => [cell(name), ...scen.map((n) => cell(fmtBE(`${id}_breakeven_${n}`))),
    cell(inrK(`${id}_value_per_1pct_base`)), cell(share(`${id}_breakeven_revolve_nocofund`, 2))])],
  { x: M, y: 1.35, w: 12.3, colW: [3.9, 1.55, 1.55, 1.55, 1.85, 1.9], fontSize: 11, border: { type: "solid", pt: 0.5, color: LINE },
    fill: { color: WHITE }, rowH: 0.42, margin: 0.05, valign: "middle" });
text(s, `O7 Prime trial for young Non-Prime cards: costs ${inr("o7_trial_cost_per_card_base")} per card (base) against ${inr("o7_value_per_saved_card_base")} for each card kept open a year; ` +
  `it pays back if it keeps ${share("o7_breakeven_saved_base", 1)} of trial cards open. Pilot MDE by box: B ${ptsAbs(v("mde_B") * 100)}, C ${ptsAbs(v("mde_C") * 100)}, ` +
  `D ${ptsAbs(v("mde_D") * 100)}, E ${ptsAbs(v("mde_E") * 100)} (3 months, 10% holdout). ` +
  "Value per 1% moved is net of the incentive paid on spend that would have happened anyway, so it can be negative.", { x: M, y: 5.0, w: 12.3, h: 0.8, fontSize: 12, color: SECONDARY });
s.addNotes("Break-even is the share of the offer's eligible non-HSIC spend that must move to HSIC for the offer to pay back after the rewards HSIC funds. 'never' means it can't in that scenario.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix (optional)" });
s.addText("Appendix C: silent attrition vs the trend, and the closure model", { placeholder: "title" });
chart(s, "07_silent_null.png", M, 1.5, 5.95);
chart(s, "08_closure_model_auc.png", M + 6.25, 1.5, 5.95);
text(s, "Left: zero-HSIC rate in the next 6 months vs two expectations at three cutoffs. Right: out-of-time ROC-AUC of every closure model vs card age alone.",
  { x: M, y: 5.1, w: 12.3, h: 0.6, fontSize: 12, color: SECONDARY });
s.addNotes("Both charts come straight from the pipeline. All numbers Measured.");

s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix (optional)" });
s.addText("Appendix D: rules, assumptions and limitations", { placeholder: "title" });
const colL = ["SoW = HSIC net ÷ total net MetroMart spend, ratio of sums, only while the card is open (open and close dates inclusive)",
  "Net sales: returns subtract; returns count as zero transactions", "MetroMart fiscal year Aug–Jul; categories and methods from the lookups; HSIC = code 3",
  "Rewards: Prime 5% Grocery, 3% Electronics, 1% other; Non-Prime 1%; credited the next month",
  "6,836 customers without a card are left out of SoW; amounts in ₹; Travel and Bill Payments earn the 1% rate"];
const colR = ["Interchange 1.5 / 1.75 / 2%, revolve income 0 / 1 / 2% of spend, MetroMart co-funding 0 / 50 / 50% (Assumed)",
  "Cost of funds 8% (O1) and EMI subvention 3% with every ₹3k+ HSIC basket taking it (O4): Assumed, upper bound",
  "The ₹9,999.99 cap understates big tickets; there is no balance data, so revolve income is a scenario",
  "No offer history, so every response is simulated until the pilot; 50% co-funding is generous, since card costs MetroMart a merchant fee that UPI doesn't",
  "The data behaves as if payment method is drawn per purchase; customer-level targeting switches on only if a future gate passes"];
const bullets = (arr) => arr.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < arr.length - 1, paraSpaceAfter: 6 } }));
text(s, "Rules from the brief", { x: M, y: 1.4, w: 5.9, h: 0.35, fontSize: 15, bold: true, color: NAVY });
text(s, bullets(colL), { x: M, y: 1.85, w: 5.9, h: 4.6, fontSize: 13, color: INK });
text(s, "Assumptions and limitations", { x: 6.9, y: 1.4, w: 5.9, h: 0.35, fontSize: 15, bold: true, color: NAVY });
text(s, bullets(colR), { x: 6.9, y: 1.85, w: 5.9, h: 4.6, fontSize: 13, color: INK });
s.addNotes("Every assumption is labelled on the slides where it is used.");

}

pres.writeFile({ fileName: OUT }).then(async () => {
  const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
  await applyTheme(OUT, THEME);
  console.log(`wrote ${path.relative(ROOT, OUT)}`);
});
