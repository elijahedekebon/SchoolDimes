// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'SchoolDimes POS';

  @override
  String get setupTitle => 'Set up this device';

  @override
  String get setupIntro =>
      'Register the device in the SchoolDimes dashboard (Devices → Register device), then scan the QR code it shows once.';

  @override
  String get scanQr => 'Scan QR code';

  @override
  String get enterManually => 'Or enter it by hand';

  @override
  String get apiBaseUrl => 'Backend address';

  @override
  String get apiBaseUrlHelp =>
      'Emulator: http://10.0.2.2:8000 · phone on Wi-Fi: http://<PC LAN IP>:8000';

  @override
  String get deviceToken => 'Device token';

  @override
  String get adminPin => 'Staff PIN for this device';

  @override
  String get adminPinHelp =>
      '4–8 digits. Protects settings so students can\'t change or wipe the device.';

  @override
  String get adminPinRepeat => 'Repeat staff PIN';

  @override
  String get adminPinMismatch => 'The PINs don\'t match';

  @override
  String get provision => 'Set up device';

  @override
  String get provisioning => 'Checking the token…';

  @override
  String get downloadingCache => 'Downloading cards and products…';

  @override
  String get errInvalidToken =>
      'The server doesn\'t recognise this token. It may have been revoked or rotated: get a new one from the dashboard.';

  @override
  String get errUnreachable =>
      'Can\'t reach the backend. Check the address and that this device is on the same network.';

  @override
  String get errUnsyncedOtherDevice =>
      'This device still has unsynced sales or taps from its previous registration. Sync them first (re-provision with the same device\'s rotated token), or ask an admin.';

  @override
  String get errHttpsRequired =>
      'The production app only talks to an https:// backend.';

  @override
  String get errQrInvalid => 'That isn\'t a SchoolDimes device code.';

  @override
  String get revokedTitle => 'Device disabled';

  @override
  String get revokedBody =>
      'The school revoked or rotated this device\'s token. Selling is stopped. Unsynced records are kept safely on the device and will sync after you set it up again with a new token.';

  @override
  String get reprovision => 'Set up again';

  @override
  String get online => 'Online';

  @override
  String get offline => 'Offline';

  @override
  String pendingCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count to sync',
      one: '1 to sync',
      zero: 'All synced',
    );
    return '$_temp0';
  }

  @override
  String lastSync(String time) {
    return 'Last sync $time';
  }

  @override
  String get never => 'never';

  @override
  String cacheAge(String age) {
    return 'Cards $age';
  }

  @override
  String get cacheStale => 'Card data is old — connect to refresh';

  @override
  String minutesAgo(int n) {
    String _temp0 = intl.Intl.pluralLogic(
      n,
      locale: localeName,
      other: '$n min ago',
      one: '1 min ago',
      zero: 'just now',
    );
    return '$_temp0';
  }

  @override
  String hoursAgo(int n) {
    String _temp0 = intl.Intl.pluralLogic(
      n,
      locale: localeName,
      other: '$n h ago',
      one: '1 h ago',
    );
    return '$_temp0';
  }

  @override
  String get syncNow => 'Sync now';

  @override
  String get syncing => 'Syncing…';

  @override
  String get syncDone => 'Sync finished';

  @override
  String get syncFailed => 'Sync failed — will retry automatically';

  @override
  String get saleTitle => 'Sale';

  @override
  String get search => 'Search';

  @override
  String get allCategories => 'All';

  @override
  String get customAmount => 'Custom amount';

  @override
  String get customAmountDescription => 'Item description';

  @override
  String get amountUgx => 'Amount (UGX)';

  @override
  String get add => 'Add';

  @override
  String get cart => 'Cart';

  @override
  String get emptyCart => 'Tap products to add them';

  @override
  String get total => 'Total';

  @override
  String charge(String amount) {
    return 'Charge $amount';
  }

  @override
  String get clear => 'Clear';

  @override
  String get chargeButton => 'Charge';

  @override
  String get tapCard => 'Tap the student\'s card';

  @override
  String get tapCardHint => 'Hold the card against the back of the device';

  @override
  String get simulateTap => 'Simulate tap (dev)';

  @override
  String get simulateTapHint => 'Card UID, e.g. 04:A2:2B:7C';

  @override
  String get nfcDisabled =>
      'NFC is turned off. Turn it on in the device settings.';

  @override
  String get openNfcSettings => 'Open settings';

  @override
  String get nfcUnsupported => 'This device has no NFC reader.';

  @override
  String get unsupportedTag =>
      'That tag can\'t be read. Use a SchoolDimes card.';

  @override
  String get cancel => 'Cancel';

  @override
  String get confirm => 'Confirm';

  @override
  String get back => 'Back';

  @override
  String get enterPin => 'Student: enter your PIN';

  @override
  String pinWrong(int left) {
    String _temp0 = intl.Intl.pluralLogic(
      left,
      locale: localeName,
      other: 'Wrong PIN. $left tries left.',
      one: 'Wrong PIN. 1 try left.',
    );
    return '$_temp0';
  }

  @override
  String get pinLocked =>
      'Too many wrong PINs. This card is locked on this device; the school has been told.';

  @override
  String get checkingPin => 'Checking PIN…';

  @override
  String get cardUnknown =>
      'Unknown card — refresh the card data or contact the school office.';

  @override
  String get cardFrozen => 'This card is frozen.';

  @override
  String get cardLost => 'This card was reported lost.';

  @override
  String get cardLockedOnDevice =>
      'This card is locked on this device after wrong PINs. Ask an admin.';

  @override
  String get cardOnlineOnly =>
      'This card can\'t be checked offline. Connect to the internet and try again.';

  @override
  String get confirmSale => 'Confirm sale';

  @override
  String get student => 'Student';

  @override
  String get balanceAfter => 'Balance after';

  @override
  String get estimated => 'estimated';

  @override
  String get receiptTitle => 'Sale complete';

  @override
  String get offlineWillSync => 'Offline — will sync';

  @override
  String get newBalance => 'New balance';

  @override
  String get done => 'Done';

  @override
  String get refusedTitle => 'Sale refused';

  @override
  String get voidHint =>
      'Only cancel before confirming. After a sale is confirmed, corrections go through a dispute in the parent app or school office — not this device.';

  @override
  String get printReceipt => 'Print receipt';

  @override
  String get flaggedForReview => 'Sent to the school for review';

  @override
  String get reason_insufficient_funds => 'Not enough money on the card.';

  @override
  String get reason_card_frozen => 'This card is frozen.';

  @override
  String get reason_card_lost => 'This card was reported lost.';

  @override
  String get reason_per_transaction_cap_exceeded =>
      'This purchase is above the single-purchase limit.';

  @override
  String get reason_daily_cap_exceeded => 'Daily spending limit reached.';

  @override
  String get reason_weekly_cap_exceeded => 'Weekly spending limit reached.';

  @override
  String get reason_category_blocked =>
      'This category of item is blocked for this student.';

  @override
  String get reason_category_not_allowed =>
      'This category isn\'t on the student\'s allowed list.';

  @override
  String get reason_item_blocked => 'This item is blocked for this student.';

  @override
  String get reason_merchant_blocked =>
      'This shop is blocked for this student.';

  @override
  String get reason_p2p_disabled =>
      'Transfers are turned off for this student.';

  @override
  String get reason_p2p_cap_exceeded => 'Daily transfer limit reached.';

  @override
  String get reason_wallet_not_spendable =>
      'Payments can\'t be made from this wallet.';

  @override
  String get reason_pin_invalid => 'Wrong PIN.';

  @override
  String get reason_unknown_card => 'Unknown card.';

  @override
  String get reason_card_locked_on_device =>
      'Card locked on this device after wrong PINs.';

  @override
  String get reason_recipient_card_inactive =>
      'The other student\'s card isn\'t active.';

  @override
  String get reason_recipient_not_found =>
      'The other student isn\'t at this school.';

  @override
  String reason_other(String code) {
    return 'Refused ($code).';
  }

  @override
  String get p2pTitle => 'Send to a friend';

  @override
  String get p2pSenderTap => 'Sender: tap your card';

  @override
  String get p2pReceiverTap => 'Now tap the receiver\'s card';

  @override
  String get p2pAmount => 'How much to send?';

  @override
  String get p2pNote => 'Note (optional)';

  @override
  String p2pSend(String amount) {
    return 'Send $amount';
  }

  @override
  String p2pDone(String amount, String name) {
    return '$amount sent to $name';
  }

  @override
  String get p2pOnlineOnly => 'Transfers need an internet connection.';

  @override
  String get p2pSameCard => 'Tap a different student\'s card.';

  @override
  String get attendanceTitle => 'Attendance';

  @override
  String get directionIn => 'Arriving';

  @override
  String get directionOut => 'Leaving';

  @override
  String get tapToRecord => 'Tap your card';

  @override
  String welcome(String name) {
    return 'Welcome, $name!';
  }

  @override
  String goodbye(String name) {
    return 'Goodbye, $name!';
  }

  @override
  String alreadyRecorded(String name) {
    return 'Already recorded, $name';
  }

  @override
  String get tapUnknown => 'Card not recognised — see the office';

  @override
  String get tapLost => 'This card was reported lost — see the office';

  @override
  String get staffTitle => 'Staff';

  @override
  String get enterAdminPin => 'Staff PIN';

  @override
  String get adminPinWrong => 'Wrong staff PIN';

  @override
  String get useBiometrics => 'Use fingerprint';

  @override
  String get todaySummary => 'Today';

  @override
  String salesCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count sales',
      one: '1 sale',
      zero: 'No sales',
    );
    return '$_temp0';
  }

  @override
  String tapsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count taps',
      one: '1 tap',
      zero: 'No taps',
    );
    return '$_temp0';
  }

  @override
  String salesTotal(String amount) {
    return 'Total $amount';
  }

  @override
  String syncedVsPending(int synced, int pending) {
    return '$synced synced · $pending pending';
  }

  @override
  String get needsReview => 'Needs review';

  @override
  String get needsReviewHelp =>
      'Offline sales the server recorded with a shortfall or broken rule. The school resolves these in the dashboard.';

  @override
  String get rejectedList => 'Rejected';

  @override
  String get rejectedHelp =>
      'Records the server could not accept. Kept here for the school to follow up in the dashboard.';

  @override
  String get nothingHere => 'Nothing here.';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get refreshCache => 'Refresh card data';

  @override
  String get cacheRefreshed => 'Card data refreshed';

  @override
  String get deviceInfo => 'Device';

  @override
  String get role => 'Role';

  @override
  String get school => 'School';

  @override
  String get merchant => 'Merchant';

  @override
  String get appVersion => 'App version';

  @override
  String get flavor => 'Build';

  @override
  String get printer => 'Receipt printer';

  @override
  String get printerHelp =>
      'Print on built-in printers (Sunmi-style) when available.';

  @override
  String get reprovisionConfirm =>
      'Set this device up again? Unsynced records stay on the device.';

  @override
  String get showUid => 'Show card UID (dev)';

  @override
  String get showUidHint =>
      'Tap any card to read its UID, then issue that UID to a student in the dashboard.';

  @override
  String get uidCopied => 'UID copied';

  @override
  String get unlockCard => 'Unlock';

  @override
  String get lockedCards => 'Cards locked on this device';

  @override
  String get roleCanteen => 'Canteen till';

  @override
  String get roleMerchant => 'Merchant till';

  @override
  String get roleAttendance => 'Attendance reader';

  @override
  String get menuSale => 'Sell';

  @override
  String get menuP2p => 'Transfer';

  @override
  String get menuAttendance => 'Attendance';

  @override
  String get menuStaff => 'Staff';

  @override
  String error(String message) {
    return 'Something went wrong: $message';
  }
}
