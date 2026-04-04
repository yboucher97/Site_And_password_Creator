import type { BrowserContext, Page } from "playwright";
import { chromium } from "playwright";

import { browserProfileDir, ensureRuntimeDirs } from "../runtime/paths";
import type { OmadaPlan } from "../config/schema";
import { clickFirstVisible, fillFirstVisible, findFirstVisible } from "./locators";

let loginContext: BrowserContext | null = null;
let loginClosedPromise: Promise<void> | null = null;
type ControllerSettings = OmadaPlan["controller"];

export interface OmadaSessionHandle {
  context: BrowserContext;
  page: Page;
}

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
}

function hasInteractiveDisplay(): boolean {
  if (process.platform !== "linux") {
    return true;
  }

  return Boolean(process.env.DISPLAY || process.env.WAYLAND_DISPLAY);
}

function resolveCloudAccount(controller: ControllerSettings): ControllerSettings["cloudAccount"] | undefined {
  if (controller.cloudAccount) {
    return controller.cloudAccount;
  }

  const email = process.env.OMADA_SITE_CREATOR_CLOUD_EMAIL?.trim();
  const password = process.env.OMADA_SITE_CREATOR_CLOUD_PASSWORD;
  if (!email || !password) {
    return undefined;
  }

  return {
    email,
    password,
  };
}

function buildOptions(
  controller: ControllerSettings,
  forceHeaded: boolean,
): Parameters<typeof chromium.launchPersistentContext>[1] {
  const args = forceHeaded ? ["--start-maximized"] : [];
  if (process.platform === "linux") {
    args.push(
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--disable-background-networking",
      "--disable-renderer-backgrounding",
      "--disable-software-rasterizer",
    );
  }

  const options: Parameters<typeof chromium.launchPersistentContext>[1] = {
    headless: forceHeaded ? false : controller.headless,
    viewport: forceHeaded ? null : { width: 1366, height: 900 },
    args,
  };

  if (controller.browserChannel !== "chromium") {
    options.channel = controller.browserChannel;
  }

  return options;
}

async function navigateToOrgManager(page: Page, controller: ControllerSettings): Promise<void> {
  await page.goto(`${normalizeBaseUrl(controller.baseUrl)}#orgManager`, { waitUntil: "domcontentloaded" });
}

async function readLoginError(page: Page): Promise<string | null> {
  const errorLocator = await findFirstVisible(page, [
    (root) => root.locator(".el-form-item__error"),
    (root) => root.locator(".el-message__content"),
    (root) => root.locator(".error-text,.error-msg,.tips-error"),
    (root) => root.getByText(/incorrect|invalid|failed|expired|required/i),
  ], 1500);

  if (!errorLocator) {
    return null;
  }

  const text = (await errorLocator.innerText().catch(() => "")).trim();
  return text.length > 0 ? text : null;
}

async function attemptAutomaticCloudLogin(page: Page, controller: ControllerSettings): Promise<boolean> {
  const cloudAccount = resolveCloudAccount(controller);
  if (!cloudAccount) {
    return false;
  }

  if (!page.url().includes("id.tplinkcloud.com")) {
    return true;
  }

  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);

  await fillFirstVisible(page, "TP-Link cloud email", cloudAccount.email, [
    (root) => root.locator("#form_item_email"),
    (root) => root.getByPlaceholder(/Email/i),
    (root) => root.locator("input[type='text']"),
  ], 5000);

  await fillFirstVisible(page, "TP-Link cloud password", cloudAccount.password, [
    (root) => root.locator("#form_item_password"),
    (root) => root.getByPlaceholder(/Password/i),
    (root) => root.locator("input[type='password']"),
  ], 5000);

  await clickFirstVisible(page, "TP-Link Sign In", [
    (root) => root.getByRole("button", { name: /^Sign In$/i }),
    (root) => root.getByText(/^Sign In$/i),
    (root) => root.locator("a").filter({ hasText: /^Sign In$/i }),
  ], 5000);

  const redirectSucceeded = await page.waitForURL((url) => !url.toString().includes("id.tplinkcloud.com"), { timeout: 30000 })
    .then(() => true)
    .catch(() => false);

  if (redirectSucceeded) {
    return true;
  }

  const errorText = await readLoginError(page);
  throw new Error(
    errorText
      ? `Automatic TP-Link cloud login failed: ${errorText}`
      : "Automatic TP-Link cloud login failed. The login page stayed open after submitting credentials.",
  );
}

export async function launchLoginBrowser(controller: ControllerSettings): Promise<{ message: string; alreadyOpen: boolean; closePromise: Promise<void>; }> {
  ensureRuntimeDirs();

  if (loginContext) {
    return {
      message: "Login browser is already open. Complete login there and close it before starting a run.",
      alreadyOpen: true,
      closePromise: loginClosedPromise ?? Promise.resolve(),
    };
  }

  if (!hasInteractiveDisplay()) {
    throw new Error("Interactive login requires a display on Linux. On a VPS, set OMADA_SITE_CREATOR_CLOUD_EMAIL and OMADA_SITE_CREATOR_CLOUD_PASSWORD and use the webhook/server flow instead.");
  }

  loginContext = await chromium.launchPersistentContext(browserProfileDir, buildOptions(controller, true));
  const page = loginContext.pages()[0] ?? await loginContext.newPage();
  await navigateToOrgManager(page, controller);

  loginClosedPromise = new Promise<void>((resolve) => {
    const done = () => {
      loginContext = null;
      loginClosedPromise = null;
      resolve();
    };

    loginContext?.once("close", done);
    loginContext?.browser()?.once("disconnected", done);
  });

  return {
    message: "Login browser opened. Log in to Omada, wait until the org list loads, then close that browser window.",
    alreadyOpen: false,
    closePromise: loginClosedPromise,
  };
}

export async function withAuthenticatedSession<T>(
  controller: ControllerSettings,
  work: (handle: OmadaSessionHandle) => Promise<T>,
): Promise<T> {
  ensureRuntimeDirs();

  if (loginContext) {
    throw new Error("Close the interactive login browser before starting a run.");
  }

  const context = await chromium.launchPersistentContext(browserProfileDir, buildOptions(controller, false));

  try {
    const page = context.pages()[0] ?? await context.newPage();
    await navigateToOrgManager(page, controller);

    if (page.url().includes("id.tplinkcloud.com")) {
      const loggedIn = await attemptAutomaticCloudLogin(page, controller);
      if (!loggedIn) {
        throw new Error("Stored session is not logged in. Open the login browser first, or set OMADA_SITE_CREATOR_CLOUD_EMAIL and OMADA_SITE_CREATOR_CLOUD_PASSWORD for automatic login.");
      }

      await navigateToOrgManager(page, controller);
    }

    return await work({ context, page });
  } finally {
    await context.close();
  }
}
