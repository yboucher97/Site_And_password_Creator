import { Command } from "commander";

import { loadPlanFromPath, summarizePlan } from "./config/load-plan";
import { launchLoginBrowser } from "./omada/session";
import { runPlanFromFile } from "./runtime/run-plan";

const program = new Command();
const defaultBrowserChannel = process.platform === "win32" ? "msedge" : "chromium";

program
  .name("omada-site-creator")
  .description("File-driven Omada Essentials UI automation helper.");

program
  .command("login")
  .description("Open a persistent login browser and wait until it is closed.")
  .option("-p, --plan <path>", "Use controller settings from a plan file.")
  .action(async (options: { plan?: string }) => {
    const plan = options.plan ? await loadPlanFromPath(options.plan) : undefined;
    const controller = plan?.controller ?? {
      organizationName: "Change Me",
      baseUrl: "https://use1-omada-cloud.tplinkcloud.com/",
      browserChannel: defaultBrowserChannel,
      headless: false,
    };

    const session = await launchLoginBrowser(controller);
    console.log(session.message);
    await session.closePromise;
  });

program
  .command("dry-run <planPath>")
  .description("Validate a plan file and print a summary without opening the browser.")
  .action(async (planPath: string) => {
    const plan = await loadPlanFromPath(planPath);
    console.log(JSON.stringify(summarizePlan(plan), null, 2));
    const result = await runPlanFromFile(planPath, true);
    console.log(JSON.stringify(result.report, null, 2));
  });

program
  .command("apply <planPath>")
  .description("Run the Playwright automation for a plan file.")
  .action(async (planPath: string) => {
    const result = await runPlanFromFile(planPath, false);
    console.log(JSON.stringify(result.report, null, 2));
    process.exitCode = result.report.overallStatus === "failed" ? 1 : 0;
  });

program.parseAsync(process.argv);
