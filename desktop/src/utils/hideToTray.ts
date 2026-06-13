/** Hide the main window to the system tray after a successful project launch. */
import { invoke } from "@tauri-apps/api/core";

export async function hideToTray(): Promise<void> {
  await invoke("hide_main_window");
}
