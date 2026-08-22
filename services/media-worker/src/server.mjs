import { execFileSync } from "node:child_process";
import { createServer } from "node:http";

const port = Number(process.env.PORT ?? 3001);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PORT must be a valid TCP port");
}

function readToolVersion(binary) {
  const output = execFileSync(binary, ["-version"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  return output.split("\n")[0].trim();
}

const ffmpegVersion = readToolVersion("ffmpeg");
const ffprobeVersion = readToolVersion("ffprobe");

const server = createServer((request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(
      JSON.stringify({
        status: "ok",
        ffmpeg: ffmpegVersion,
        ffprobe: ffprobeVersion,
      }),
    );
    return;
  }

  response.writeHead(404, { "Content-Type": "application/json" });
  response.end(JSON.stringify({ error: "not_found" }));
});

server.listen(port, "0.0.0.0", () => {
  console.log(`media-worker listening on port ${port}`);
});
