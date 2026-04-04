import { startServer } from "./server/app";

void (async () => {
  const started = await startServer();
  console.log(`Omada Site Creator listening at ${started.url}`);
})();
