# Uponor Bridge – local Home Assistant app (add-on)

## Install (HA Green / HAOS)
1. Stop the manually started instance first (SSH / Terminal add-on):
   `pkill -f uponor_bridge`
2. Copy this whole `uponor_bridge` folder into the local apps directory on the HA host.
   Since the 2026 "add-ons → apps" rename the docs call it `local_apps` (Samba share
   `local_apps`, SSH path `/local_apps`); on older setups it is the `addons` share / `/addons`.
   Use whichever of the two exists:
   - **Samba share** app: open the `local_apps` (or `addons`) share and copy the folder in, or
   - **Terminal & SSH** app: `tar xzf uponor_bridge_addon.tar.gz -C /local_apps`
     (or `-C /addons`).
   Result: `/local_apps/uponor_bridge/config.yaml` etc.
3. Settings → **Apps** (formerly Add-ons) → **App store** (bottom right) → ⋮ (top right) →
   **Check for updates**, then refresh the browser page.
4. A **Local apps** section appears at the top of the store. Open **Uponor Bridge** → **Install**
   (the image is built on the device; takes a minute or two).
5. Optional: Configuration tab → check `serial_port`.
6. Info tab: enable **Start on boot** and **Watchdog**, then **Start**. Check the **Log** tab
   for `mqtt connected`.
7. The four Uponor devices keep the same MQTT unique IDs, so existing entities, names, areas
   and the dashboard stay unchanged.

Updating: copy new files over, bump `version` in `config.yaml`, Check for updates, then Update/Rebuild.

Not showing up? Settings → System → Logs → select **Supervisor** and look for a config.yaml validation error.
