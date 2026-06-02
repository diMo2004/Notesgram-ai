import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

function startProcess(command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: { ...process.env, ...options.env },
    shell: process.platform === "win32",
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout.on("data", (chunk) => process.stdout.write(chunk));
  child.stderr.on("data", (chunk) => process.stderr.write(chunk));

  return child;
}

function runProcess(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = startProcess(command, args, options);

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }

      reject(new Error(`${command} ${args.join(" ")} exited with code ${code}`));
    });
  });
}

async function waitForUrl(url, timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (response.ok) {
        return response;
      }
    } catch {
      // Keep retrying until the server is ready.
    }

    await delay(1000);
  }

  throw new Error(`Timed out waiting for ${url}`);
}

async function main() {
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

  await runProcess(npmCommand, ["run", "build"], { cwd: process.cwd() });

  const startServer = startProcess(npmCommand, ["run", "start"], { cwd: process.cwd() });

  try {
    await waitForUrl("http://127.0.0.1:3000");
    const response = await fetch("http://127.0.0.1:3000", { cache: "no-store" });
    const html = await response.text();

    if (!html.includes("Notesgram MVP")) {
      throw new Error("Frontend page did not contain the expected Notesgram MVP heading");
    }

    console.log("Frontend smoke test passed.");
  } finally {
    startServer.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});