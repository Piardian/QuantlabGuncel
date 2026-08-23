# Windows Sleep/Wake Scheduler Setup

This setup supports Windows Task Scheduler waking a plugged-in PC from Sleep
Mode. It does not implement BIOS wake, Wake-on-LAN, or any network-based wake
behavior.

## Recommended Schedule

Use `23:30` local time for the paper-trading task. This gives Windows time to
wake, restore networking, and run the daily market-data workflow after the
regular market session.

## Task Scheduler Configuration

1. Open Task Scheduler.
2. Create or edit the `Leadership Paper Trading` task.
3. On `Triggers`, create a weekly trigger at `23:30` and select Monday through
   Friday. This deliberately suppresses weekend notifications.
4. On `Actions`, use:

```text
Program/script:
C:\Users\piard\Desktop\backterster\run_paper_trading.bat

Start in:
C:\Users\piard\Desktop\backterster
```

5. On `Conditions`, enable:

```text
Wake the computer to run this task
```

6. On `Settings`, enable:

```text
Run task as soon as possible after a scheduled start is missed
If the task fails, restart every: 5 minutes
Attempt to restart up to: 3 times
```

## Power Settings Required

1. Open `Control Panel > Power Options`.
2. Select the active power plan.
3. Open `Change plan settings > Change advanced power settings`.
4. Under `Sleep`, set `Allow wake timers` to `Enable`.
5. Keep the PC plugged into power.
6. Avoid hibernation for this workflow unless you have separately verified that
   your Windows installation wakes reliably from hibernate.

## How To Test Wake-Up Behavior

1. Edit the scheduled task trigger to run 5 to 10 minutes from now.
2. Confirm `Wake the computer to run this task` is enabled.
3. Put Windows into Sleep Mode.
4. Leave the PC plugged in.
5. Wait for the scheduled time.
6. After the machine wakes, verify a new launcher log appears in:

```text
C:\Users\piard\Desktop\backterster\daily_logs
```

7. Confirm `latest_run_summary.txt` was updated.
