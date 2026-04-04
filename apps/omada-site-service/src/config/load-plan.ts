import { readFile } from "node:fs/promises";
import { basename, extname } from "node:path";
import { parse as parseYaml } from "yaml";

import { formatValidationError, planSchema, type OmadaPlan } from "./schema";

function readEnvBoolean(name: string): boolean | undefined {
  const rawValue = process.env[name];
  if (rawValue === undefined) {
    return undefined;
  }

  const normalized = rawValue.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }

  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }

  return undefined;
}

function applyEnvironmentDefaults(plan: OmadaPlan): OmadaPlan {
  const envBrowserChannel = process.env.OMADA_SITE_CREATOR_BROWSER_CHANNEL;
  const browserChannel = envBrowserChannel === "msedge" || envBrowserChannel === "chrome" || envBrowserChannel === "chromium"
    ? envBrowserChannel
    : plan.controller.browserChannel;

  const envHeadless = readEnvBoolean("OMADA_SITE_CREATOR_HEADLESS");
  const envCloudEmail = process.env.OMADA_SITE_CREATOR_CLOUD_EMAIL?.trim();
  const envCloudPassword = process.env.OMADA_SITE_CREATOR_CLOUD_PASSWORD;
  const envDeviceUsername = process.env.OMADA_SITE_CREATOR_DEVICE_USERNAME?.trim();
  const envDevicePassword = process.env.OMADA_SITE_CREATOR_DEVICE_PASSWORD;

  return {
    ...plan,
    controller: {
      ...plan.controller,
      browserChannel,
      headless: envHeadless ?? plan.controller.headless,
      cloudAccount: plan.controller.cloudAccount ?? (
        envCloudEmail && envCloudPassword
          ? {
              email: envCloudEmail,
              password: envCloudPassword,
            }
          : undefined
      ),
      deviceAccount: plan.controller.deviceAccount ?? (
        envDeviceUsername && envDevicePassword
          ? {
              username: envDeviceUsername,
              password: envDevicePassword,
            }
          : undefined
      ),
    },
  };
}

function parseText(content: string, sourceName: string): unknown {
  const extension = extname(sourceName).toLowerCase();

  if (extension === ".yaml" || extension === ".yml") {
    return parseYaml(content);
  }

  if (extension === ".json") {
    return JSON.parse(content);
  }

  throw new Error(`Unsupported plan file type for ${sourceName}. Use .yaml, .yml, or .json.`);
}

export function validatePlanData(data: unknown): OmadaPlan {
  const result = planSchema.safeParse(data);

  if (!result.success) {
    throw new Error(formatValidationError(result.error));
  }

  if (result.data.sites.some((site) => site.wlanGroups.some((group) => group.ssids.some((ssid) => ssid.security !== "open" && !ssid.password)))) {
    throw new Error("Every non-open SSID must include a password.");
  }

  return applyEnvironmentDefaults(result.data);
}

export function parsePlan(content: string, sourceName: string): OmadaPlan {
  const parsed = parseText(content, sourceName);
  return validatePlanData(parsed);
}

export async function loadPlanFromPath(planPath: string): Promise<OmadaPlan> {
  const content = await readFile(planPath, "utf8");
  return parsePlan(content, basename(planPath));
}

export function summarizePlan(plan: OmadaPlan): Record<string, number | string | boolean> {
  const siteCount = plan.sites.length;
  const lanCount = plan.sites.reduce((sum, site) => sum + site.lans.length, 0);
  const wlanGroupCount = plan.sites.reduce((sum, site) => sum + site.wlanGroups.length, 0);
  const ssidCount = plan.sites.reduce(
    (sum, site) => sum + site.wlanGroups.reduce((groupSum, group) => groupSum + group.ssids.length, 0),
    0,
  );

  return {
    version: plan.version,
    organizationName: plan.controller.organizationName,
    siteCount,
    lanCount,
    wlanGroupCount,
    ssidCount,
    headless: plan.controller.headless,
    stopOnError: plan.execution.stopOnError,
    dryRun: plan.execution.dryRun,
  };
}
