# A Grid Power Monitor for Raspberry Pi

A small Python application that runs on a Raspberry Pi and monitors the state of grid power for an external system. It is one half of a two-part project; the other half is the custom UPS the Pi runs on. Schematics and drawings for the UPS will live alongside this documentation.

The Pi is powered through the UPS. Under normal conditions the UPS passes grid power through; when grid power drops, the UPS switches to battery and the Pi keeps running. That is what makes the rest of this system possible: the Pi is still alive after grid power is gone, so it can detect the loss, notify, and shut itself down cleanly.

The Notecard is powered by the Pi through the Blues Notecarrier Pi, so it has no independent power path. When the Pi halts, the Notecard loses power with it. The UPS hardware then cuts battery power to stop the UPS from draining further.

Every 5 minutes a systemd timer invokes the app. It reads a GPIO pin driven by external hardware: a LOW voltage means the monitored system has power (ON); a HIGH voltage means it has lost power (OFF).

The app sends a notification when grid power is lost and again when it comes back. When the app sees OFF, it delivers a notification over the Blues Notecard and then shuts the Pi down. When the app sees ON after having previously seen OFF, it delivers a notification that power has been restored — and does not shut down. The Notecard is a Notecard Cell+WiFi (LTE Cat 1 bis), which supports WiFi-first with cellular fallback.

The delivery-before-shutdown ordering for the OFF case is the central design commitment. Because the Notecard is powered through the Pi, the Pi halting kills the Notecard — so the message has to be durably delivered before that happens. "Queued to the Notecard's flash" is not enough; the sync has to complete.

The app also emits a monthly heartbeat to confirm it is alive, and a FirstRunEvent on its first ever run.