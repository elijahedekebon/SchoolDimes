# Testing the POS app on a real Android device

What you need: an Android phone or tablet **with NFC**, a few blank NFC cards
or stickers (NTAG213/215 work well), and the phone and PC on the **same
Wi-Fi**.

## 1. Backend and dashboard on the PC

```bash
docker compose up -d
docker compose exec web python manage.py seed_demo
# the dashboard is served by Django: http://localhost:8000/school
```

Find the PC's LAN address (macOS: `ipconfig getifaddr en0`, e.g.
`192.168.1.20`). Check the phone can reach `http://192.168.1.20:8000/admin/`
in its browser.

## 2. Install the dev build

Enable **Developer options → USB debugging** on the phone and connect it.

```bash
cd pos-app
flutter devices                                   # note the device id
flutter run --flavor dev -d <id> --dart-define=API_BASE_URL=http://192.168.1.20:8000
```

## 3. Register the device

Dashboard (admin@kampaladps.schooldimes.test / pw123456) → **Devices →
Register device** → role *Canteen till*. In the token dialog set "Backend
address the device will use" to `http://192.168.1.20:8000`, then on the
phone tap **Scan QR code** and scan it. Choose a staff PIN, e.g. 9999.

## 4. Issue test cards with real UIDs

1. On the phone: **Staff → (PIN) → Settings → Show card UID**, then hold a
   blank card to the phone. The UID appears (e.g. `04a22b7c913e80`); copy it.
2. Dashboard → **Students → Amina Nakato → Cards → Issue card** (or
   **Replace card**), paste the UID, set a PIN (e.g. 2468).
3. Repeat for a second student (for the double-spend and P2P tests).
4. On the phone: **Staff → Settings → Refresh card data** (or wait for
   the next sync).

## 5. Test script

Tick each line; check the dashboard where noted.

| # | Do | Expect |
|---|---|---|
| 1 | **Online sale**: add Rice & beans → Charge → tap card → PIN → Confirm | receipt with the new balance, no "offline" badge. Dashboard → Sales: the sale with its line item |
| 2 | **Offline sale**: turn Wi-Fi off; sell a Mandazi | receipt says "Offline — will sync", balance "estimated"; status bar "1 to sync" |
| 3 | Turn Wi-Fi on | within seconds the status bar shows "All synced"; Dashboard → Sales shows the sale (channel offline sync) |
| 4 | **Pull the network mid-sale**: Wi-Fi off right after pressing Confirm | the sale is queued, not lost; after reconnecting it syncs once (Dashboard shows one sale, not two) |
| 5 | **Double spend**: register a second device; put both offline; on each, spend most of the same card's balance; reconnect both | the second device's sale syncs as a **shortfall**; Dashboard → Review queue shows it; the phone's Staff → Needs review lists it |
| 6 | **Frozen card**: Dashboard → Cards → Freeze; on the phone refresh card data; tap the card | "This card is frozen", no PIN prompt |
| 7 | **Blocked item**: Amina's override blocks Soda; try to sell her a Soda | refused "This item is blocked for this student" |
| 8 | **Wrong PIN lockout**: enter wrong PINs until the limit (school default 5) | "Too many wrong PINs…"; after the next sync the dashboard shows the card frozen and parents are notified |
| 9 | **Unlock**: Dashboard → Cards → Reset PIN, then Unfreeze; on the phone refresh | the card works with the new PIN |
| 10 | **Attendance offline**: register an *Attendance reader*, set up a second phone (or re-provision); Wi-Fi off; tap several cards in/out | each shows "Welcome/Goodbye, name" within a second; tapping again shows "Already recorded" |
| 11 | Reconnect | taps sync; Dashboard → Attendance → daily register shows them |
| 12 | **Revoked device**: Dashboard → Devices → Revoke | the phone shows "Device disabled" at its next request; unsynced records stay; set it up again with a new device's token only after syncing |
| 13 | **P2P** (canteen): Transfer → sender taps + PIN → receiver taps → amount | "UGX … sent"; Dashboard → student → P2P shows it (online only) |

## 6. Emulator instead of a phone

No NFC on emulators. The dev build shows a **Simulate tap** field on the
tap screens: type the card UID from the dashboard. The automated version of
the main flows:

```bash
pos-app/tool/run_integration.sh emulator-5554
```
