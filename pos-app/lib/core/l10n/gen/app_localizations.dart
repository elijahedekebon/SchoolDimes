import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_lg.dart';
import 'app_localizations_sw.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'gen/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('lg'),
    Locale('sw'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'SchoolDimes POS'**
  String get appTitle;

  /// No description provided for @setupTitle.
  ///
  /// In en, this message translates to:
  /// **'Set up this device'**
  String get setupTitle;

  /// No description provided for @setupIntro.
  ///
  /// In en, this message translates to:
  /// **'Register the device in the SchoolDimes dashboard (Devices → Register device), then scan the QR code it shows once.'**
  String get setupIntro;

  /// No description provided for @scanQr.
  ///
  /// In en, this message translates to:
  /// **'Scan QR code'**
  String get scanQr;

  /// No description provided for @enterManually.
  ///
  /// In en, this message translates to:
  /// **'Or enter it by hand'**
  String get enterManually;

  /// No description provided for @apiBaseUrl.
  ///
  /// In en, this message translates to:
  /// **'Backend address'**
  String get apiBaseUrl;

  /// No description provided for @apiBaseUrlHelp.
  ///
  /// In en, this message translates to:
  /// **'Emulator: http://10.0.2.2:8000 · phone on Wi-Fi: http://<PC LAN IP>:8000'**
  String get apiBaseUrlHelp;

  /// No description provided for @deviceToken.
  ///
  /// In en, this message translates to:
  /// **'Device token'**
  String get deviceToken;

  /// No description provided for @adminPin.
  ///
  /// In en, this message translates to:
  /// **'Staff PIN for this device'**
  String get adminPin;

  /// No description provided for @adminPinHelp.
  ///
  /// In en, this message translates to:
  /// **'4–8 digits. Protects settings so students can\'t change or wipe the device.'**
  String get adminPinHelp;

  /// No description provided for @adminPinRepeat.
  ///
  /// In en, this message translates to:
  /// **'Repeat staff PIN'**
  String get adminPinRepeat;

  /// No description provided for @adminPinMismatch.
  ///
  /// In en, this message translates to:
  /// **'The PINs don\'t match'**
  String get adminPinMismatch;

  /// No description provided for @provision.
  ///
  /// In en, this message translates to:
  /// **'Set up device'**
  String get provision;

  /// No description provided for @provisioning.
  ///
  /// In en, this message translates to:
  /// **'Checking the token…'**
  String get provisioning;

  /// No description provided for @downloadingCache.
  ///
  /// In en, this message translates to:
  /// **'Downloading cards and products…'**
  String get downloadingCache;

  /// No description provided for @errInvalidToken.
  ///
  /// In en, this message translates to:
  /// **'The server doesn\'t recognise this token. It may have been revoked or rotated: get a new one from the dashboard.'**
  String get errInvalidToken;

  /// No description provided for @errUnreachable.
  ///
  /// In en, this message translates to:
  /// **'Can\'t reach the backend. Check the address and that this device is on the same network.'**
  String get errUnreachable;

  /// No description provided for @errUnsyncedOtherDevice.
  ///
  /// In en, this message translates to:
  /// **'This device still has unsynced sales or taps from its previous registration. Sync them first (re-provision with the same device\'s rotated token), or ask an admin.'**
  String get errUnsyncedOtherDevice;

  /// No description provided for @errHttpsRequired.
  ///
  /// In en, this message translates to:
  /// **'The production app only talks to an https:// backend.'**
  String get errHttpsRequired;

  /// No description provided for @errQrInvalid.
  ///
  /// In en, this message translates to:
  /// **'That isn\'t a SchoolDimes device code.'**
  String get errQrInvalid;

  /// No description provided for @revokedTitle.
  ///
  /// In en, this message translates to:
  /// **'Device disabled'**
  String get revokedTitle;

  /// No description provided for @revokedBody.
  ///
  /// In en, this message translates to:
  /// **'The school revoked or rotated this device\'s token. Selling is stopped. Unsynced records are kept safely on the device and will sync after you set it up again with a new token.'**
  String get revokedBody;

  /// No description provided for @reprovision.
  ///
  /// In en, this message translates to:
  /// **'Set up again'**
  String get reprovision;

  /// No description provided for @online.
  ///
  /// In en, this message translates to:
  /// **'Online'**
  String get online;

  /// No description provided for @offline.
  ///
  /// In en, this message translates to:
  /// **'Offline'**
  String get offline;

  /// No description provided for @pendingCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{All synced} one{1 to sync} other{{count} to sync}}'**
  String pendingCount(int count);

  /// No description provided for @lastSync.
  ///
  /// In en, this message translates to:
  /// **'Last sync {time}'**
  String lastSync(String time);

  /// No description provided for @never.
  ///
  /// In en, this message translates to:
  /// **'never'**
  String get never;

  /// No description provided for @cacheAge.
  ///
  /// In en, this message translates to:
  /// **'Cards {age}'**
  String cacheAge(String age);

  /// No description provided for @cacheStale.
  ///
  /// In en, this message translates to:
  /// **'Card data is old — connect to refresh'**
  String get cacheStale;

  /// No description provided for @minutesAgo.
  ///
  /// In en, this message translates to:
  /// **'{n, plural, =0{just now} one{1 min ago} other{{n} min ago}}'**
  String minutesAgo(int n);

  /// No description provided for @hoursAgo.
  ///
  /// In en, this message translates to:
  /// **'{n, plural, one{1 h ago} other{{n} h ago}}'**
  String hoursAgo(int n);

  /// No description provided for @syncNow.
  ///
  /// In en, this message translates to:
  /// **'Sync now'**
  String get syncNow;

  /// No description provided for @syncing.
  ///
  /// In en, this message translates to:
  /// **'Syncing…'**
  String get syncing;

  /// No description provided for @syncDone.
  ///
  /// In en, this message translates to:
  /// **'Sync finished'**
  String get syncDone;

  /// No description provided for @syncFailed.
  ///
  /// In en, this message translates to:
  /// **'Sync failed — will retry automatically'**
  String get syncFailed;

  /// No description provided for @saleTitle.
  ///
  /// In en, this message translates to:
  /// **'Sale'**
  String get saleTitle;

  /// No description provided for @search.
  ///
  /// In en, this message translates to:
  /// **'Search'**
  String get search;

  /// No description provided for @allCategories.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get allCategories;

  /// No description provided for @customAmount.
  ///
  /// In en, this message translates to:
  /// **'Custom amount'**
  String get customAmount;

  /// No description provided for @customAmountDescription.
  ///
  /// In en, this message translates to:
  /// **'Item description'**
  String get customAmountDescription;

  /// No description provided for @amountUgx.
  ///
  /// In en, this message translates to:
  /// **'Amount (UGX)'**
  String get amountUgx;

  /// No description provided for @add.
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get add;

  /// No description provided for @cart.
  ///
  /// In en, this message translates to:
  /// **'Cart'**
  String get cart;

  /// No description provided for @emptyCart.
  ///
  /// In en, this message translates to:
  /// **'Tap products to add them'**
  String get emptyCart;

  /// No description provided for @total.
  ///
  /// In en, this message translates to:
  /// **'Total'**
  String get total;

  /// No description provided for @charge.
  ///
  /// In en, this message translates to:
  /// **'Charge {amount}'**
  String charge(String amount);

  /// No description provided for @clear.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get clear;

  /// No description provided for @chargeButton.
  ///
  /// In en, this message translates to:
  /// **'Charge'**
  String get chargeButton;

  /// No description provided for @tapCard.
  ///
  /// In en, this message translates to:
  /// **'Tap the student\'s card'**
  String get tapCard;

  /// No description provided for @tapCardHint.
  ///
  /// In en, this message translates to:
  /// **'Hold the card against the back of the device'**
  String get tapCardHint;

  /// No description provided for @simulateTap.
  ///
  /// In en, this message translates to:
  /// **'Simulate tap (dev)'**
  String get simulateTap;

  /// No description provided for @simulateTapHint.
  ///
  /// In en, this message translates to:
  /// **'Card UID, e.g. 04:A2:2B:7C'**
  String get simulateTapHint;

  /// No description provided for @nfcDisabled.
  ///
  /// In en, this message translates to:
  /// **'NFC is turned off. Turn it on in the device settings.'**
  String get nfcDisabled;

  /// No description provided for @openNfcSettings.
  ///
  /// In en, this message translates to:
  /// **'Open settings'**
  String get openNfcSettings;

  /// No description provided for @nfcUnsupported.
  ///
  /// In en, this message translates to:
  /// **'This device has no NFC reader.'**
  String get nfcUnsupported;

  /// No description provided for @unsupportedTag.
  ///
  /// In en, this message translates to:
  /// **'That tag can\'t be read. Use a SchoolDimes card.'**
  String get unsupportedTag;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @confirm.
  ///
  /// In en, this message translates to:
  /// **'Confirm'**
  String get confirm;

  /// No description provided for @back.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get back;

  /// No description provided for @enterPin.
  ///
  /// In en, this message translates to:
  /// **'Student: enter your PIN'**
  String get enterPin;

  /// No description provided for @pinWrong.
  ///
  /// In en, this message translates to:
  /// **'{left, plural, one{Wrong PIN. 1 try left.} other{Wrong PIN. {left} tries left.}}'**
  String pinWrong(int left);

  /// No description provided for @pinLocked.
  ///
  /// In en, this message translates to:
  /// **'Too many wrong PINs. This card is locked on this device; the school has been told.'**
  String get pinLocked;

  /// No description provided for @checkingPin.
  ///
  /// In en, this message translates to:
  /// **'Checking PIN…'**
  String get checkingPin;

  /// No description provided for @cardUnknown.
  ///
  /// In en, this message translates to:
  /// **'Unknown card — refresh the card data or contact the school office.'**
  String get cardUnknown;

  /// No description provided for @cardFrozen.
  ///
  /// In en, this message translates to:
  /// **'This card is frozen.'**
  String get cardFrozen;

  /// No description provided for @cardLost.
  ///
  /// In en, this message translates to:
  /// **'This card was reported lost.'**
  String get cardLost;

  /// No description provided for @cardLockedOnDevice.
  ///
  /// In en, this message translates to:
  /// **'This card is locked on this device after wrong PINs. Ask an admin.'**
  String get cardLockedOnDevice;

  /// No description provided for @cardOnlineOnly.
  ///
  /// In en, this message translates to:
  /// **'This card can\'t be checked offline. Connect to the internet and try again.'**
  String get cardOnlineOnly;

  /// No description provided for @confirmSale.
  ///
  /// In en, this message translates to:
  /// **'Confirm sale'**
  String get confirmSale;

  /// No description provided for @student.
  ///
  /// In en, this message translates to:
  /// **'Student'**
  String get student;

  /// No description provided for @balanceAfter.
  ///
  /// In en, this message translates to:
  /// **'Balance after'**
  String get balanceAfter;

  /// No description provided for @estimated.
  ///
  /// In en, this message translates to:
  /// **'estimated'**
  String get estimated;

  /// No description provided for @receiptTitle.
  ///
  /// In en, this message translates to:
  /// **'Sale complete'**
  String get receiptTitle;

  /// No description provided for @offlineWillSync.
  ///
  /// In en, this message translates to:
  /// **'Offline — will sync'**
  String get offlineWillSync;

  /// No description provided for @newBalance.
  ///
  /// In en, this message translates to:
  /// **'New balance'**
  String get newBalance;

  /// No description provided for @done.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get done;

  /// No description provided for @refusedTitle.
  ///
  /// In en, this message translates to:
  /// **'Sale refused'**
  String get refusedTitle;

  /// No description provided for @voidHint.
  ///
  /// In en, this message translates to:
  /// **'Only cancel before confirming. After a sale is confirmed, corrections go through a dispute in the parent app or school office — not this device.'**
  String get voidHint;

  /// No description provided for @printReceipt.
  ///
  /// In en, this message translates to:
  /// **'Print receipt'**
  String get printReceipt;

  /// No description provided for @flaggedForReview.
  ///
  /// In en, this message translates to:
  /// **'Sent to the school for review'**
  String get flaggedForReview;

  /// No description provided for @reason_insufficient_funds.
  ///
  /// In en, this message translates to:
  /// **'Not enough money on the card.'**
  String get reason_insufficient_funds;

  /// No description provided for @reason_card_frozen.
  ///
  /// In en, this message translates to:
  /// **'This card is frozen.'**
  String get reason_card_frozen;

  /// No description provided for @reason_card_lost.
  ///
  /// In en, this message translates to:
  /// **'This card was reported lost.'**
  String get reason_card_lost;

  /// No description provided for @reason_per_transaction_cap_exceeded.
  ///
  /// In en, this message translates to:
  /// **'This purchase is above the single-purchase limit.'**
  String get reason_per_transaction_cap_exceeded;

  /// No description provided for @reason_daily_cap_exceeded.
  ///
  /// In en, this message translates to:
  /// **'Daily spending limit reached.'**
  String get reason_daily_cap_exceeded;

  /// No description provided for @reason_weekly_cap_exceeded.
  ///
  /// In en, this message translates to:
  /// **'Weekly spending limit reached.'**
  String get reason_weekly_cap_exceeded;

  /// No description provided for @reason_category_blocked.
  ///
  /// In en, this message translates to:
  /// **'This category of item is blocked for this student.'**
  String get reason_category_blocked;

  /// No description provided for @reason_category_not_allowed.
  ///
  /// In en, this message translates to:
  /// **'This category isn\'t on the student\'s allowed list.'**
  String get reason_category_not_allowed;

  /// No description provided for @reason_item_blocked.
  ///
  /// In en, this message translates to:
  /// **'This item is blocked for this student.'**
  String get reason_item_blocked;

  /// No description provided for @reason_merchant_blocked.
  ///
  /// In en, this message translates to:
  /// **'This shop is blocked for this student.'**
  String get reason_merchant_blocked;

  /// No description provided for @reason_p2p_disabled.
  ///
  /// In en, this message translates to:
  /// **'Transfers are turned off for this student.'**
  String get reason_p2p_disabled;

  /// No description provided for @reason_p2p_cap_exceeded.
  ///
  /// In en, this message translates to:
  /// **'Daily transfer limit reached.'**
  String get reason_p2p_cap_exceeded;

  /// No description provided for @reason_wallet_not_spendable.
  ///
  /// In en, this message translates to:
  /// **'Payments can\'t be made from this wallet.'**
  String get reason_wallet_not_spendable;

  /// No description provided for @reason_pin_invalid.
  ///
  /// In en, this message translates to:
  /// **'Wrong PIN.'**
  String get reason_pin_invalid;

  /// No description provided for @reason_unknown_card.
  ///
  /// In en, this message translates to:
  /// **'Unknown card.'**
  String get reason_unknown_card;

  /// No description provided for @reason_card_locked_on_device.
  ///
  /// In en, this message translates to:
  /// **'Card locked on this device after wrong PINs.'**
  String get reason_card_locked_on_device;

  /// No description provided for @reason_recipient_card_inactive.
  ///
  /// In en, this message translates to:
  /// **'The other student\'s card isn\'t active.'**
  String get reason_recipient_card_inactive;

  /// No description provided for @reason_recipient_not_found.
  ///
  /// In en, this message translates to:
  /// **'The other student isn\'t at this school.'**
  String get reason_recipient_not_found;

  /// No description provided for @reason_other.
  ///
  /// In en, this message translates to:
  /// **'Refused ({code}).'**
  String reason_other(String code);

  /// No description provided for @p2pTitle.
  ///
  /// In en, this message translates to:
  /// **'Send to a friend'**
  String get p2pTitle;

  /// No description provided for @p2pSenderTap.
  ///
  /// In en, this message translates to:
  /// **'Sender: tap your card'**
  String get p2pSenderTap;

  /// No description provided for @p2pReceiverTap.
  ///
  /// In en, this message translates to:
  /// **'Now tap the receiver\'s card'**
  String get p2pReceiverTap;

  /// No description provided for @p2pAmount.
  ///
  /// In en, this message translates to:
  /// **'How much to send?'**
  String get p2pAmount;

  /// No description provided for @p2pNote.
  ///
  /// In en, this message translates to:
  /// **'Note (optional)'**
  String get p2pNote;

  /// No description provided for @p2pSend.
  ///
  /// In en, this message translates to:
  /// **'Send {amount}'**
  String p2pSend(String amount);

  /// No description provided for @p2pDone.
  ///
  /// In en, this message translates to:
  /// **'{amount} sent to {name}'**
  String p2pDone(String amount, String name);

  /// No description provided for @p2pOnlineOnly.
  ///
  /// In en, this message translates to:
  /// **'Transfers need an internet connection.'**
  String get p2pOnlineOnly;

  /// No description provided for @p2pSameCard.
  ///
  /// In en, this message translates to:
  /// **'Tap a different student\'s card.'**
  String get p2pSameCard;

  /// No description provided for @attendanceTitle.
  ///
  /// In en, this message translates to:
  /// **'Attendance'**
  String get attendanceTitle;

  /// No description provided for @directionIn.
  ///
  /// In en, this message translates to:
  /// **'Arriving'**
  String get directionIn;

  /// No description provided for @directionOut.
  ///
  /// In en, this message translates to:
  /// **'Leaving'**
  String get directionOut;

  /// No description provided for @tapToRecord.
  ///
  /// In en, this message translates to:
  /// **'Tap your card'**
  String get tapToRecord;

  /// No description provided for @welcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome, {name}!'**
  String welcome(String name);

  /// No description provided for @goodbye.
  ///
  /// In en, this message translates to:
  /// **'Goodbye, {name}!'**
  String goodbye(String name);

  /// No description provided for @alreadyRecorded.
  ///
  /// In en, this message translates to:
  /// **'Already recorded, {name}'**
  String alreadyRecorded(String name);

  /// No description provided for @tapUnknown.
  ///
  /// In en, this message translates to:
  /// **'Card not recognised — see the office'**
  String get tapUnknown;

  /// No description provided for @tapLost.
  ///
  /// In en, this message translates to:
  /// **'This card was reported lost — see the office'**
  String get tapLost;

  /// No description provided for @staffTitle.
  ///
  /// In en, this message translates to:
  /// **'Staff'**
  String get staffTitle;

  /// No description provided for @enterAdminPin.
  ///
  /// In en, this message translates to:
  /// **'Staff PIN'**
  String get enterAdminPin;

  /// No description provided for @adminPinWrong.
  ///
  /// In en, this message translates to:
  /// **'Wrong staff PIN'**
  String get adminPinWrong;

  /// No description provided for @useBiometrics.
  ///
  /// In en, this message translates to:
  /// **'Use fingerprint'**
  String get useBiometrics;

  /// No description provided for @todaySummary.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get todaySummary;

  /// No description provided for @salesCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No sales} one{1 sale} other{{count} sales}}'**
  String salesCount(int count);

  /// No description provided for @tapsCount.
  ///
  /// In en, this message translates to:
  /// **'{count, plural, =0{No taps} one{1 tap} other{{count} taps}}'**
  String tapsCount(int count);

  /// No description provided for @salesTotal.
  ///
  /// In en, this message translates to:
  /// **'Total {amount}'**
  String salesTotal(String amount);

  /// No description provided for @syncedVsPending.
  ///
  /// In en, this message translates to:
  /// **'{synced} synced · {pending} pending'**
  String syncedVsPending(int synced, int pending);

  /// No description provided for @needsReview.
  ///
  /// In en, this message translates to:
  /// **'Needs review'**
  String get needsReview;

  /// No description provided for @needsReviewHelp.
  ///
  /// In en, this message translates to:
  /// **'Offline sales the server recorded with a shortfall or broken rule. The school resolves these in the dashboard.'**
  String get needsReviewHelp;

  /// No description provided for @rejectedList.
  ///
  /// In en, this message translates to:
  /// **'Rejected'**
  String get rejectedList;

  /// No description provided for @rejectedHelp.
  ///
  /// In en, this message translates to:
  /// **'Records the server could not accept. Kept here for the school to follow up in the dashboard.'**
  String get rejectedHelp;

  /// No description provided for @nothingHere.
  ///
  /// In en, this message translates to:
  /// **'Nothing here.'**
  String get nothingHere;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @refreshCache.
  ///
  /// In en, this message translates to:
  /// **'Refresh card data'**
  String get refreshCache;

  /// No description provided for @cacheRefreshed.
  ///
  /// In en, this message translates to:
  /// **'Card data refreshed'**
  String get cacheRefreshed;

  /// No description provided for @deviceInfo.
  ///
  /// In en, this message translates to:
  /// **'Device'**
  String get deviceInfo;

  /// No description provided for @role.
  ///
  /// In en, this message translates to:
  /// **'Role'**
  String get role;

  /// No description provided for @school.
  ///
  /// In en, this message translates to:
  /// **'School'**
  String get school;

  /// No description provided for @merchant.
  ///
  /// In en, this message translates to:
  /// **'Merchant'**
  String get merchant;

  /// No description provided for @appVersion.
  ///
  /// In en, this message translates to:
  /// **'App version'**
  String get appVersion;

  /// No description provided for @flavor.
  ///
  /// In en, this message translates to:
  /// **'Build'**
  String get flavor;

  /// No description provided for @printer.
  ///
  /// In en, this message translates to:
  /// **'Receipt printer'**
  String get printer;

  /// No description provided for @printerHelp.
  ///
  /// In en, this message translates to:
  /// **'Print on built-in printers (Sunmi-style) when available.'**
  String get printerHelp;

  /// No description provided for @reprovisionConfirm.
  ///
  /// In en, this message translates to:
  /// **'Set this device up again? Unsynced records stay on the device.'**
  String get reprovisionConfirm;

  /// No description provided for @showUid.
  ///
  /// In en, this message translates to:
  /// **'Show card UID (dev)'**
  String get showUid;

  /// No description provided for @showUidHint.
  ///
  /// In en, this message translates to:
  /// **'Tap any card to read its UID, then issue that UID to a student in the dashboard.'**
  String get showUidHint;

  /// No description provided for @uidCopied.
  ///
  /// In en, this message translates to:
  /// **'UID copied'**
  String get uidCopied;

  /// No description provided for @unlockCard.
  ///
  /// In en, this message translates to:
  /// **'Unlock'**
  String get unlockCard;

  /// No description provided for @lockedCards.
  ///
  /// In en, this message translates to:
  /// **'Cards locked on this device'**
  String get lockedCards;

  /// No description provided for @roleCanteen.
  ///
  /// In en, this message translates to:
  /// **'Canteen till'**
  String get roleCanteen;

  /// No description provided for @roleMerchant.
  ///
  /// In en, this message translates to:
  /// **'Merchant till'**
  String get roleMerchant;

  /// No description provided for @roleAttendance.
  ///
  /// In en, this message translates to:
  /// **'Attendance reader'**
  String get roleAttendance;

  /// No description provided for @menuSale.
  ///
  /// In en, this message translates to:
  /// **'Sell'**
  String get menuSale;

  /// No description provided for @menuP2p.
  ///
  /// In en, this message translates to:
  /// **'Transfer'**
  String get menuP2p;

  /// No description provided for @menuAttendance.
  ///
  /// In en, this message translates to:
  /// **'Attendance'**
  String get menuAttendance;

  /// No description provided for @menuStaff.
  ///
  /// In en, this message translates to:
  /// **'Staff'**
  String get menuStaff;

  /// No description provided for @error.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong: {message}'**
  String error(String message);
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'lg', 'sw'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'lg':
      return AppLocalizationsLg();
    case 'sw':
      return AppLocalizationsSw();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
