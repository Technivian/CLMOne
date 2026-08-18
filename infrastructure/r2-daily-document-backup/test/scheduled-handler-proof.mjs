import { spawn } from "node:child_process";
import { once } from "node:events";

const port = 8791;
const child = spawn(process.execPath, ["node_modules/wrangler/wrangler-dist/cli.js", "dev", "--local", "--test-scheduled", "--port", String(port)], {
  cwd: new URL("..", import.meta.url),
  stdio: ["ignore", "pipe", "pipe"],
});

let output = "";
child.stdout.on("data", (chunk) => { output += chunk; });
child.stderr.on("data", (chunk) => { output += chunk; });

async function waitForServer() {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/__scheduled?cron=15+2+*+*+*`);
      if (response.ok) return;
    } catch {
      // Wrangler has not opened the local listener yet.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Wrangler scheduled-handler proof did not become ready:\n${output}`);
}

try {
  await waitForServer();
  process.stdout.write("Local Wrangler scheduled-handler proof passed.\n");
} finally {
  if (!child.killed) {
    child.kill("SIGTERM");
    await once(child, "exit");
  }
}
