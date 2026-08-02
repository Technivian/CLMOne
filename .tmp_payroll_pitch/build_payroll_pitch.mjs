import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "/Users/haroonwahed/Documents/Projects/CLMOne/CLMOne_Payroll_Admin_Pitch.pptx";
const TMP = "/Users/haroonwahed/Documents/Projects/CLMOne/.tmp_payroll_pitch";
const W = 1280;
const H = 720;
const C = {
  canvas: "#FFFFFF",
  ink: "#000000",
  muted: "#4B5563",
  panel: "#EDEDED",
  line: "#B8BCC4",
  blue: "#3D8DFF",
  paleBlue: "#EAF5FB",
};

async function saveBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function box(slide, name, x, y, w, h, fill = "none", line = "none") {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function text(slide, name, value, x, y, w, h, size, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontSize: size,
    typeface: "Helvetica Neue",
    color: options.color || C.ink,
    bold: Boolean(options.bold),
    alignment: options.alignment || "left",
    verticalAlignment: options.verticalAlignment || "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function rule(slide, x, y, w, color = C.line, thickness = 1) {
  slide.shapes.add({
    geometry: "line",
    name: `rule-${x}-${y}`,
    position: { left: x, top: y, width: w, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: thickness },
  });
}

function chrome(slide, number, section) {
  slide.background.fill = C.canvas;
  text(slide, `eyebrow-${number}`, section.toUpperCase(), 42, 36, 300, 24, 14, { bold: true, color: C.muted });
  text(slide, `page-${number}`, String(number), 1190, 656, 48, 22, 14, { color: C.muted, alignment: "right" });
  rule(slide, 42, 72, 1196, C.line, 1);
}

function notes(slide) {
  slide.speakerNotes.textFrame.setText("[Sources]\nNo external sources. Content is based on the CLM One product capabilities supplied in this conversation.");
  slide.speakerNotes.setVisible(true);
}

function addCover(presentation) {
  // Codex Grid cover composition, adapted from layout 01.
  const slide = presentation.slides.add();
  slide.background.fill = C.canvas;
  text(slide, "cover-kicker", "CLM ONE FOR PAYROLL ADMINS", 42, 42, 420, 24, 16, { bold: true, color: C.muted });
  rule(slide, 42, 82, 1196, C.line, 1);
  text(slide, "cover-title", "Payroll agreements\nshouldn’t live in inboxes.", 42, 190, 770, 220, 68, { bold: true, verticalAlignment: "bottom" });
  text(slide, "cover-subtitle", "CLM One gives payroll teams one controlled place to intake, confirm, and manage the agreements that affect operations.", 42, 472, 610, 105, 28, { color: C.muted });
  box(slide, "cover-field", 866, 160, 330, 330, C.paleBlue, C.line);
  text(slide, "cover-field-label", "ONE CONTROLLED RECORD", 900, 220, 245, 28, 18, { bold: true, color: C.blue });
  text(slide, "cover-field-copy", "Source document\n+ extracted metadata\n+ human confirmation\n+ audit trail", 900, 278, 250, 150, 28, { bold: true });
  text(slide, "cover-page", "01", 1188, 656, 50, 22, 14, { color: C.muted, alignment: "right" });
  notes(slide);
}

function addProblem(presentation) {
  // Codex Grid three-column composition, adapted from layout 07.
  const slide = presentation.slides.add();
  chrome(slide, 2, "The problem");
  text(slide, "problem-title", "The friction is operational, not legal.", 42, 116, 1040, 58, 42, { bold: true });
  text(slide, "problem-sub", "When agreements are scattered, payroll teams lose the context needed to act with confidence.", 42, 188, 850, 38, 23, { color: C.muted });
  const entries = [
    ["01", "Files arrive everywhere", "Email attachments, shared drives, and individual folders create an incomplete picture."],
    ["02", "Ownership is unclear", "Teams cannot quickly see who is accountable for a contract or its follow-up."],
    ["03", "Key obligations are easy to miss", "Dates, terms, and compliance actions remain trapped in documents instead of daily operations."],
  ];
  entries.forEach((entry, index) => {
    const x = 42 + index * 400;
    rule(slide, x, 290, 336, C.ink, 2);
    text(slide, `problem-number-${index}`, entry[0], x, 315, 80, 38, 20, { bold: true, color: C.blue });
    text(slide, `problem-head-${index}`, entry[1], x, 374, 336, 70, 28, { bold: true });
    text(slide, `problem-copy-${index}`, entry[2], x, 462, 336, 110, 20, { color: C.muted });
  });
  notes(slide);
}

function addWorkflow(presentation) {
  // Codex Grid timeline composition, adapted from layout 17.
  const slide = presentation.slides.add();
  chrome(slide, 3, "How it works");
  text(slide, "workflow-title", "CLM One turns contract intake into a controlled workflow.", 42, 116, 1110, 58, 40, { bold: true });
  text(slide, "workflow-sub", "Automation accelerates preparation; people remain responsible for confirmation and decisions.", 42, 188, 1000, 36, 23, { color: C.muted });
  const labels = [
    ["IMPORT OR FORWARD", "Bring in a folder of files or forward email attachments."],
    ["EXTRACT", "Capture readable metadata and preserve it as unverified review context."],
    ["CONFIRM", "A reviewer verifies ownership, dates, type, and other key details."],
    ["MANAGE", "Keep the source, audit trail, and follow-up work in one record."],
  ];
  // Directional arrows are laid down before the process cards so the flow is
  // unambiguous without crossing labels.
  [303, 605, 907].forEach((x, index) => {
    slide.shapes.add({
      geometry: "rightArrow",
      name: `workflow-arrow-${index}`,
      position: { left: x, top: 402, width: 42, height: 28 },
      fill: C.blue,
      line: { style: "solid", fill: C.blue, width: 0 },
    });
  });
  labels.forEach((entry, index) => {
    const x = 42 + index * 302;
    box(slide, `workflow-card-${index}`, x, 306, 250, 214, index === 1 ? C.paleBlue : C.panel, C.line);
  });
  labels.forEach((entry, index) => {
    const x = 62 + index * 302;
    text(slide, `workflow-number-${index}`, `0${index + 1}`, x, 332, 60, 26, 16, { bold: true, color: C.blue });
    text(slide, `workflow-head-${index}`, entry[0], x, 380, 210, 52, 21, { bold: true });
    text(slide, `workflow-copy-${index}`, entry[1], x, 448, 205, 58, 17, { color: C.muted });
  });
  text(slide, "workflow-bottom", "Every imported document retains its source version and an auditable path back to how it entered CLM One.", 42, 584, 980, 31, 21, { color: C.muted });
  notes(slide);
}

function addBenefits(presentation) {
  // Codex Grid three-callout composition, adapted from layout 19; qualitative, not invented KPI claims.
  const slide = presentation.slides.add();
  chrome(slide, 4, "Why payroll teams care");
  text(slide, "benefits-title", "What payroll admins gain immediately", 42, 116, 850, 58, 42, { bold: true });
  text(slide, "benefits-sub", "A clearer operating model for agreements that affect people, payments, and compliance.", 42, 188, 950, 36, 23, { color: C.muted });
  const items = [
    ["ONE RECORD", "A single place to find the source agreement, current context, and activity history."],
    ["CLEAR OWNERSHIP", "Each record can be routed to the person responsible for confirmation and follow-up."],
    ["AUDITABLE ACTIONS", "Imports, extracted metadata, and review activity are visible and traceable."],
  ];
  items.forEach((entry, index) => {
    const x = 42 + index * 400;
    box(slide, `benefit-panel-${index}`, x, 310, 350, 240, C.panel, "none");
    text(slide, `benefit-label-${index}`, entry[0], x + 28, 348, 285, 32, 19, { bold: true, color: C.blue });
    text(slide, `benefit-copy-${index}`, entry[1], x + 28, 410, 286, 88, 24, { bold: true });
  });
  notes(slide);
}

function addClose(presentation) {
  // Codex Grid closing composition, adapted from layout 26.
  const slide = presentation.slides.add();
  slide.background.fill = C.canvas;
  text(slide, "close-kicker", "THE OUTCOME", 42, 42, 300, 24, 16, { bold: true, color: C.muted });
  rule(slide, 42, 82, 1196, C.line, 1);
  text(slide, "close-title", "A reliable contract record\nfor payroll operations.", 42, 176, 900, 220, 64, { bold: true, verticalAlignment: "bottom" });
  text(slide, "close-copy", "Start with one existing folder or shared inbox.\nBring the agreements in, confirm what matters, and give payroll a dependable operational record.", 42, 506, 780, 92, 27, { color: C.muted });
  text(slide, "close-call", "CLM ONE", 1010, 550, 185, 34, 22, { bold: true, color: C.blue, alignment: "right" });
  text(slide, "close-page", "05", 1188, 656, 50, 22, 14, { color: C.muted, alignment: "right" });
  notes(slide);
}

async function main() {
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  addCover(presentation);
  addProblem(presentation);
  addWorkflow(presentation);
  addBenefits(presentation);
  addClose(presentation);

  for (let index = 0; index < presentation.slides.items.length; index += 1) {
    const slide = presentation.slides.items[index];
    await saveBlob(`${TMP}/slide-${index + 1}.png`, await presentation.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(`${TMP}/slide-${index + 1}.layout.json`, await (await slide.export({ format: "layout" })).text());
  }
  await saveBlob(`${TMP}/deck-montage.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const output = await PresentationFile.exportPptx(presentation);
  await output.save(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
