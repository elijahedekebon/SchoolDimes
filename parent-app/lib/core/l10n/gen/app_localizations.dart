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
  /// **'SchoolDimes'**
  String get appTitle;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @signInTitle.
  ///
  /// In en, this message translates to:
  /// **'Welcome back'**
  String get signInTitle;

  /// No description provided for @register.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get register;

  /// No description provided for @registerTitle.
  ///
  /// In en, this message translates to:
  /// **'Create your parent account'**
  String get registerTitle;

  /// No description provided for @haveAccount.
  ///
  /// In en, this message translates to:
  /// **'Already have an account? Sign in'**
  String get haveAccount;

  /// No description provided for @noAccount.
  ///
  /// In en, this message translates to:
  /// **'New here? Create an account'**
  String get noAccount;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @passwordHelp.
  ///
  /// In en, this message translates to:
  /// **'At least 8 characters, not too common.'**
  String get passwordHelp;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullName;

  /// No description provided for @phone.
  ///
  /// In en, this message translates to:
  /// **'Phone number'**
  String get phone;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;

  /// No description provided for @sessionExpired.
  ///
  /// In en, this message translates to:
  /// **'Your session ended. Please sign in again.'**
  String get sessionExpired;

  /// No description provided for @networkError.
  ///
  /// In en, this message translates to:
  /// **'No connection. Check your data or Wi-Fi and try again.'**
  String get networkError;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

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

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @done.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get done;

  /// No description provided for @close.
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get close;

  /// No description provided for @next.
  ///
  /// In en, this message translates to:
  /// **'Next'**
  String get next;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading…'**
  String get loading;

  /// No description provided for @nothingYet.
  ///
  /// In en, this message translates to:
  /// **'Nothing here yet.'**
  String get nothingYet;

  /// No description provided for @lastUpdated.
  ///
  /// In en, this message translates to:
  /// **'Offline — last updated {when}'**
  String lastUpdated(String when);

  /// No description provided for @appLock.
  ///
  /// In en, this message translates to:
  /// **'App lock'**
  String get appLock;

  /// No description provided for @appLockHelp.
  ///
  /// In en, this message translates to:
  /// **'Ask for your fingerprint or phone PIN when the app opens.'**
  String get appLockHelp;

  /// No description provided for @unlock.
  ///
  /// In en, this message translates to:
  /// **'Unlock'**
  String get unlock;

  /// No description provided for @kycTitle.
  ///
  /// In en, this message translates to:
  /// **'Verify your identity'**
  String get kycTitle;

  /// No description provided for @kycIntro.
  ///
  /// In en, this message translates to:
  /// **'Schools check a parent\'s ID before linking children. Enter it as it appears on your document.'**
  String get kycIntro;

  /// No description provided for @kycNameOnId.
  ///
  /// In en, this message translates to:
  /// **'Name on ID'**
  String get kycNameOnId;

  /// No description provided for @kycDocType.
  ///
  /// In en, this message translates to:
  /// **'Document'**
  String get kycDocType;

  /// No description provided for @kycNationalId.
  ///
  /// In en, this message translates to:
  /// **'National ID'**
  String get kycNationalId;

  /// No description provided for @kycPassport.
  ///
  /// In en, this message translates to:
  /// **'Passport'**
  String get kycPassport;

  /// No description provided for @kycNumber.
  ///
  /// In en, this message translates to:
  /// **'ID number'**
  String get kycNumber;

  /// No description provided for @kycSubmit.
  ///
  /// In en, this message translates to:
  /// **'Submit for checking'**
  String get kycSubmit;

  /// No description provided for @kycSkip.
  ///
  /// In en, this message translates to:
  /// **'Later'**
  String get kycSkip;

  /// No description provided for @kycStatus_pending.
  ///
  /// In en, this message translates to:
  /// **'Being checked by the school'**
  String get kycStatus_pending;

  /// No description provided for @kycStatus_verified.
  ///
  /// In en, this message translates to:
  /// **'Verified'**
  String get kycStatus_verified;

  /// No description provided for @kycStatus_rejected.
  ///
  /// In en, this message translates to:
  /// **'Not accepted — see the note and submit again'**
  String get kycStatus_rejected;

  /// No description provided for @kycStatus_none.
  ///
  /// In en, this message translates to:
  /// **'Not submitted'**
  String get kycStatus_none;

  /// No description provided for @kycLimits.
  ///
  /// In en, this message translates to:
  /// **'Your school decides what changes once you\'re verified; nothing is blocked by the app.'**
  String get kycLimits;

  /// No description provided for @kycNotes.
  ///
  /// In en, this message translates to:
  /// **'Note from the school: {notes}'**
  String kycNotes(String notes);

  /// No description provided for @homeTitle.
  ///
  /// In en, this message translates to:
  /// **'My children'**
  String get homeTitle;

  /// No description provided for @noChildren.
  ///
  /// In en, this message translates to:
  /// **'No children are linked to your account yet. Ask the school office to link them to {email}.'**
  String noChildren(String email);

  /// No description provided for @mainBalance.
  ///
  /// In en, this message translates to:
  /// **'Spending'**
  String get mainBalance;

  /// No description provided for @savingsBalance.
  ///
  /// In en, this message translates to:
  /// **'Savings'**
  String get savingsBalance;

  /// No description provided for @lowBalance.
  ///
  /// In en, this message translates to:
  /// **'Low balance'**
  String get lowBalance;

  /// No description provided for @card_active.
  ///
  /// In en, this message translates to:
  /// **'Card active'**
  String get card_active;

  /// No description provided for @card_frozen.
  ///
  /// In en, this message translates to:
  /// **'Card frozen'**
  String get card_frozen;

  /// No description provided for @card_lost.
  ///
  /// In en, this message translates to:
  /// **'Card lost'**
  String get card_lost;

  /// No description provided for @card_none.
  ///
  /// In en, this message translates to:
  /// **'No card yet'**
  String get card_none;

  /// No description provided for @recentPurchases.
  ///
  /// In en, this message translates to:
  /// **'Recent activity'**
  String get recentPurchases;

  /// No description provided for @seeAll.
  ///
  /// In en, this message translates to:
  /// **'See all'**
  String get seeAll;

  /// No description provided for @topUp.
  ///
  /// In en, this message translates to:
  /// **'Top up'**
  String get topUp;

  /// No description provided for @freeze.
  ///
  /// In en, this message translates to:
  /// **'Freeze card'**
  String get freeze;

  /// No description provided for @unfreeze.
  ///
  /// In en, this message translates to:
  /// **'Unfreeze card'**
  String get unfreeze;

  /// No description provided for @freezeConfirm.
  ///
  /// In en, this message translates to:
  /// **'Freeze {name}\'s card? Every purchase, transfer and fee payment is refused at once; canteen tills refuse it after their next refresh.'**
  String freezeConfirm(String name);

  /// No description provided for @unfreezeConfirm.
  ///
  /// In en, this message translates to:
  /// **'Unfreeze {name}\'s card so it can be used again?'**
  String unfreezeConfirm(String name);

  /// No description provided for @reportLost.
  ///
  /// In en, this message translates to:
  /// **'Report card lost'**
  String get reportLost;

  /// No description provided for @reportLostConfirm.
  ///
  /// In en, this message translates to:
  /// **'Report {name}\'s card lost? This is permanent; the school issues a new card.'**
  String reportLostConfirm(String name);

  /// No description provided for @tipOfTheDay.
  ///
  /// In en, this message translates to:
  /// **'Money tip'**
  String get tipOfTheDay;

  /// No description provided for @history.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get history;

  /// No description provided for @controls.
  ///
  /// In en, this message translates to:
  /// **'Limits'**
  String get controls;

  /// No description provided for @savings.
  ///
  /// In en, this message translates to:
  /// **'Savings'**
  String get savings;

  /// No description provided for @cardAndP2p.
  ///
  /// In en, this message translates to:
  /// **'Card & transfers'**
  String get cardAndP2p;

  /// No description provided for @filterAll.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get filterAll;

  /// No description provided for @filterPurchases.
  ///
  /// In en, this message translates to:
  /// **'Purchases'**
  String get filterPurchases;

  /// No description provided for @filterTopUps.
  ///
  /// In en, this message translates to:
  /// **'Top-ups'**
  String get filterTopUps;

  /// No description provided for @filterOther.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get filterOther;

  /// No description provided for @from.
  ///
  /// In en, this message translates to:
  /// **'From'**
  String get from;

  /// No description provided for @to.
  ///
  /// In en, this message translates to:
  /// **'To'**
  String get to;

  /// No description provided for @items.
  ///
  /// In en, this message translates to:
  /// **'Items'**
  String get items;

  /// No description provided for @reportProblem.
  ///
  /// In en, this message translates to:
  /// **'Report a problem'**
  String get reportProblem;

  /// No description provided for @disputeOpen.
  ///
  /// In en, this message translates to:
  /// **'Problem reported'**
  String get disputeOpen;

  /// No description provided for @entry_pos_purchase.
  ///
  /// In en, this message translates to:
  /// **'Purchase'**
  String get entry_pos_purchase;

  /// No description provided for @entry_deposit.
  ///
  /// In en, this message translates to:
  /// **'Top-up'**
  String get entry_deposit;

  /// No description provided for @entry_gift_voucher.
  ///
  /// In en, this message translates to:
  /// **'Gift'**
  String get entry_gift_voucher;

  /// No description provided for @entry_refund.
  ///
  /// In en, this message translates to:
  /// **'Refund'**
  String get entry_refund;

  /// No description provided for @entry_fee_payment.
  ///
  /// In en, this message translates to:
  /// **'School fee'**
  String get entry_fee_payment;

  /// No description provided for @entry_p2p_transfer_in.
  ///
  /// In en, this message translates to:
  /// **'Received from a friend'**
  String get entry_p2p_transfer_in;

  /// No description provided for @entry_p2p_transfer_out.
  ///
  /// In en, this message translates to:
  /// **'Sent to a friend'**
  String get entry_p2p_transfer_out;

  /// No description provided for @entry_savings_move_in.
  ///
  /// In en, this message translates to:
  /// **'Moved to savings'**
  String get entry_savings_move_in;

  /// No description provided for @entry_savings_move_out.
  ///
  /// In en, this message translates to:
  /// **'Moved from savings'**
  String get entry_savings_move_out;

  /// No description provided for @entry_savings_withdrawal.
  ///
  /// In en, this message translates to:
  /// **'Savings withdrawal'**
  String get entry_savings_withdrawal;

  /// No description provided for @entry_shortfall_recovery.
  ///
  /// In en, this message translates to:
  /// **'Shortfall repayment'**
  String get entry_shortfall_recovery;

  /// No description provided for @entry_reversal.
  ///
  /// In en, this message translates to:
  /// **'Reversal'**
  String get entry_reversal;

  /// No description provided for @entry_other.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get entry_other;

  /// No description provided for @topUpTitle.
  ///
  /// In en, this message translates to:
  /// **'Top up'**
  String get topUpTitle;

  /// No description provided for @child.
  ///
  /// In en, this message translates to:
  /// **'Child'**
  String get child;

  /// No description provided for @amount.
  ///
  /// In en, this message translates to:
  /// **'Amount (UGX)'**
  String get amount;

  /// No description provided for @amountInvalid.
  ///
  /// In en, this message translates to:
  /// **'Enter a positive amount, e.g. 5000'**
  String get amountInvalid;

  /// No description provided for @channel.
  ///
  /// In en, this message translates to:
  /// **'Pay with'**
  String get channel;

  /// No description provided for @channel_momo.
  ///
  /// In en, this message translates to:
  /// **'Mobile money'**
  String get channel_momo;

  /// No description provided for @channel_ussd.
  ///
  /// In en, this message translates to:
  /// **'USSD'**
  String get channel_ussd;

  /// No description provided for @channel_bank.
  ///
  /// In en, this message translates to:
  /// **'Bank'**
  String get channel_bank;

  /// No description provided for @payerPhone.
  ///
  /// In en, this message translates to:
  /// **'Phone that pays'**
  String get payerPhone;

  /// No description provided for @payNow.
  ///
  /// In en, this message translates to:
  /// **'Pay {amount}'**
  String payNow(String amount);

  /// No description provided for @howToPay.
  ///
  /// In en, this message translates to:
  /// **'How to pay'**
  String get howToPay;

  /// No description provided for @waitingConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Waiting for the payment to be confirmed…'**
  String get waitingConfirmation;

  /// No description provided for @stillWaiting.
  ///
  /// In en, this message translates to:
  /// **'Still waiting. You can leave this screen: the money is added only when the payment provider confirms it.'**
  String get stillWaiting;

  /// No description provided for @depositStatus_pending.
  ///
  /// In en, this message translates to:
  /// **'Waiting'**
  String get depositStatus_pending;

  /// No description provided for @depositStatus_confirmed.
  ///
  /// In en, this message translates to:
  /// **'Paid — the money is on the card'**
  String get depositStatus_confirmed;

  /// No description provided for @depositStatus_failed.
  ///
  /// In en, this message translates to:
  /// **'Failed — no money was taken'**
  String get depositStatus_failed;

  /// No description provided for @depositStatus_expired.
  ///
  /// In en, this message translates to:
  /// **'Expired — not paid in time'**
  String get depositStatus_expired;

  /// No description provided for @reference.
  ///
  /// In en, this message translates to:
  /// **'Reference {ref}'**
  String reference(String ref);

  /// No description provided for @tryAgain.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// No description provided for @depositHistory.
  ///
  /// In en, this message translates to:
  /// **'Top-up history'**
  String get depositHistory;

  /// No description provided for @payments.
  ///
  /// In en, this message translates to:
  /// **'Payments'**
  String get payments;

  /// No description provided for @recurringTitle.
  ///
  /// In en, this message translates to:
  /// **'Automatic top-ups'**
  String get recurringTitle;

  /// No description provided for @recurringAdd.
  ///
  /// In en, this message translates to:
  /// **'New automatic top-up'**
  String get recurringAdd;

  /// No description provided for @frequency.
  ///
  /// In en, this message translates to:
  /// **'How often'**
  String get frequency;

  /// No description provided for @weekly.
  ///
  /// In en, this message translates to:
  /// **'Weekly'**
  String get weekly;

  /// No description provided for @monthly.
  ///
  /// In en, this message translates to:
  /// **'Monthly'**
  String get monthly;

  /// No description provided for @dayOfWeek.
  ///
  /// In en, this message translates to:
  /// **'Day'**
  String get dayOfWeek;

  /// No description provided for @dayOfMonth.
  ///
  /// In en, this message translates to:
  /// **'Day of the month (1–28)'**
  String get dayOfMonth;

  /// No description provided for @nextRun.
  ///
  /// In en, this message translates to:
  /// **'Next: {when}'**
  String nextRun(String when);

  /// No description provided for @paused.
  ///
  /// In en, this message translates to:
  /// **'Paused'**
  String get paused;

  /// No description provided for @autoPaused.
  ///
  /// In en, this message translates to:
  /// **'Paused after {count} failed payments'**
  String autoPaused(int count);

  /// No description provided for @resume.
  ///
  /// In en, this message translates to:
  /// **'Resume'**
  String get resume;

  /// No description provided for @pause.
  ///
  /// In en, this message translates to:
  /// **'Pause'**
  String get pause;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @lastStatus.
  ///
  /// In en, this message translates to:
  /// **'Last: {status}'**
  String lastStatus(String status);

  /// No description provided for @weekday0.
  ///
  /// In en, this message translates to:
  /// **'Monday'**
  String get weekday0;

  /// No description provided for @weekday1.
  ///
  /// In en, this message translates to:
  /// **'Tuesday'**
  String get weekday1;

  /// No description provided for @weekday2.
  ///
  /// In en, this message translates to:
  /// **'Wednesday'**
  String get weekday2;

  /// No description provided for @weekday3.
  ///
  /// In en, this message translates to:
  /// **'Thursday'**
  String get weekday3;

  /// No description provided for @weekday4.
  ///
  /// In en, this message translates to:
  /// **'Friday'**
  String get weekday4;

  /// No description provided for @weekday5.
  ///
  /// In en, this message translates to:
  /// **'Saturday'**
  String get weekday5;

  /// No description provided for @weekday6.
  ///
  /// In en, this message translates to:
  /// **'Sunday'**
  String get weekday6;

  /// No description provided for @giftsTitle.
  ///
  /// In en, this message translates to:
  /// **'Gifts & family links'**
  String get giftsTitle;

  /// No description provided for @sendGift.
  ///
  /// In en, this message translates to:
  /// **'Send a gift'**
  String get sendGift;

  /// No description provided for @giftMessage.
  ///
  /// In en, this message translates to:
  /// **'Message (shown to your family)'**
  String get giftMessage;

  /// No description provided for @familyLinks.
  ///
  /// In en, this message translates to:
  /// **'Links for relatives'**
  String get familyLinks;

  /// No description provided for @familyLinksHelp.
  ///
  /// In en, this message translates to:
  /// **'Relatives anywhere can top up using a link — no app or account. They only see your child\'s first name and school.'**
  String get familyLinksHelp;

  /// No description provided for @createLink.
  ///
  /// In en, this message translates to:
  /// **'Create link for {name}'**
  String createLink(String name);

  /// No description provided for @share.
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get share;

  /// No description provided for @shareText.
  ///
  /// In en, this message translates to:
  /// **'Send pocket money to {name} at school: {url}'**
  String shareText(String name, String url);

  /// No description provided for @revoke.
  ///
  /// In en, this message translates to:
  /// **'Turn off'**
  String get revoke;

  /// No description provided for @revokeConfirm.
  ///
  /// In en, this message translates to:
  /// **'Turn this link off? Anyone who has it can no longer use it.'**
  String get revokeConfirm;

  /// No description provided for @linkOff.
  ///
  /// In en, this message translates to:
  /// **'Off'**
  String get linkOff;

  /// No description provided for @contributionsReceived.
  ///
  /// In en, this message translates to:
  /// **'Received from relatives'**
  String get contributionsReceived;

  /// No description provided for @fundsTitle.
  ///
  /// In en, this message translates to:
  /// **'Class funds'**
  String get fundsTitle;

  /// No description provided for @fundRaised.
  ///
  /// In en, this message translates to:
  /// **'{raised} of {target}'**
  String fundRaised(String raised, String target);

  /// No description provided for @contribute.
  ///
  /// In en, this message translates to:
  /// **'Contribute'**
  String get contribute;

  /// No description provided for @contributions.
  ///
  /// In en, this message translates to:
  /// **'Contributions'**
  String get contributions;

  /// No description provided for @createFund.
  ///
  /// In en, this message translates to:
  /// **'Start a class fund'**
  String get createFund;

  /// No description provided for @fundTitle.
  ///
  /// In en, this message translates to:
  /// **'Title'**
  String get fundTitle;

  /// No description provided for @fundPurpose.
  ///
  /// In en, this message translates to:
  /// **'What it\'s for'**
  String get fundPurpose;

  /// No description provided for @fundTarget.
  ///
  /// In en, this message translates to:
  /// **'Target (optional)'**
  String get fundTarget;

  /// No description provided for @controlsTitle.
  ///
  /// In en, this message translates to:
  /// **'Spending limits'**
  String get controlsTitle;

  /// No description provided for @controlsHelp.
  ///
  /// In en, this message translates to:
  /// **'You can only make limits stricter than the school\'s. Blank = use the school\'s limit.'**
  String get controlsHelp;

  /// No description provided for @schoolLimit.
  ///
  /// In en, this message translates to:
  /// **'School: {value}'**
  String schoolLimit(String value);

  /// No description provided for @noLimit.
  ///
  /// In en, this message translates to:
  /// **'no limit'**
  String get noLimit;

  /// No description provided for @dailyCap.
  ///
  /// In en, this message translates to:
  /// **'Daily limit'**
  String get dailyCap;

  /// No description provided for @weeklyCap.
  ///
  /// In en, this message translates to:
  /// **'Weekly limit'**
  String get weeklyCap;

  /// No description provided for @perTxnCap.
  ///
  /// In en, this message translates to:
  /// **'Per purchase'**
  String get perTxnCap;

  /// No description provided for @p2pCap.
  ///
  /// In en, this message translates to:
  /// **'Transfers per day'**
  String get p2pCap;

  /// No description provided for @p2pEnabled.
  ///
  /// In en, this message translates to:
  /// **'Allow transfers to friends'**
  String get p2pEnabled;

  /// No description provided for @blockedCategories.
  ///
  /// In en, this message translates to:
  /// **'Blocked categories'**
  String get blockedCategories;

  /// No description provided for @blockedItems.
  ///
  /// In en, this message translates to:
  /// **'Blocked items'**
  String get blockedItems;

  /// No description provided for @blockedMerchants.
  ///
  /// In en, this message translates to:
  /// **'Blocked shops'**
  String get blockedMerchants;

  /// No description provided for @lowBalanceAlert.
  ///
  /// In en, this message translates to:
  /// **'Tell me when the balance drops below'**
  String get lowBalanceAlert;

  /// No description provided for @saved.
  ///
  /// In en, this message translates to:
  /// **'Saved'**
  String get saved;

  /// No description provided for @savingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Savings'**
  String get savingsTitle;

  /// No description provided for @moveIn.
  ///
  /// In en, this message translates to:
  /// **'Move to savings'**
  String get moveIn;

  /// No description provided for @moveOut.
  ///
  /// In en, this message translates to:
  /// **'Move to spending'**
  String get moveOut;

  /// No description provided for @goals.
  ///
  /// In en, this message translates to:
  /// **'Goals'**
  String get goals;

  /// No description provided for @newGoal.
  ///
  /// In en, this message translates to:
  /// **'New goal'**
  String get newGoal;

  /// No description provided for @goalName.
  ///
  /// In en, this message translates to:
  /// **'Goal'**
  String get goalName;

  /// No description provided for @goalTarget.
  ///
  /// In en, this message translates to:
  /// **'Target'**
  String get goalTarget;

  /// No description provided for @goalReached.
  ///
  /// In en, this message translates to:
  /// **'Goal reached! 🎉'**
  String get goalReached;

  /// No description provided for @withdrawWindow.
  ///
  /// In en, this message translates to:
  /// **'Withdrawal window'**
  String get withdrawWindow;

  /// No description provided for @withdrawWindowHelp.
  ///
  /// In en, this message translates to:
  /// **'Savings can be sent to your phone only between these dates (e.g. the holidays).'**
  String get withdrawWindowHelp;

  /// No description provided for @windowClosed.
  ///
  /// In en, this message translates to:
  /// **'Closed'**
  String get windowClosed;

  /// No description provided for @windowOpen.
  ///
  /// In en, this message translates to:
  /// **'Open until {end}'**
  String windowOpen(String end);

  /// No description provided for @setWindow.
  ///
  /// In en, this message translates to:
  /// **'Set dates'**
  String get setWindow;

  /// No description provided for @withdraw.
  ///
  /// In en, this message translates to:
  /// **'Withdraw to my phone'**
  String get withdraw;

  /// No description provided for @payoutStatus.
  ///
  /// In en, this message translates to:
  /// **'Withdrawals'**
  String get payoutStatus;

  /// No description provided for @payout_pending.
  ///
  /// In en, this message translates to:
  /// **'Sending'**
  String get payout_pending;

  /// No description provided for @payout_succeeded.
  ///
  /// In en, this message translates to:
  /// **'Sent'**
  String get payout_succeeded;

  /// No description provided for @payout_failed.
  ///
  /// In en, this message translates to:
  /// **'Failed — returned to savings'**
  String get payout_failed;

  /// No description provided for @p2pHistory.
  ///
  /// In en, this message translates to:
  /// **'Transfers between students'**
  String get p2pHistory;

  /// No description provided for @p2pSent.
  ///
  /// In en, this message translates to:
  /// **'Sent to {name}'**
  String p2pSent(String name);

  /// No description provided for @p2pReceived.
  ///
  /// In en, this message translates to:
  /// **'Received from {name}'**
  String p2pReceived(String name);

  /// No description provided for @disputesTitle.
  ///
  /// In en, this message translates to:
  /// **'Reported problems'**
  String get disputesTitle;

  /// No description provided for @disputeReason.
  ///
  /// In en, this message translates to:
  /// **'What went wrong?'**
  String get disputeReason;

  /// No description provided for @reason_wrong_amount.
  ///
  /// In en, this message translates to:
  /// **'Wrong amount'**
  String get reason_wrong_amount;

  /// No description provided for @reason_not_received.
  ///
  /// In en, this message translates to:
  /// **'Didn\'t get the item'**
  String get reason_not_received;

  /// No description provided for @reason_unauthorized.
  ///
  /// In en, this message translates to:
  /// **'My child didn\'t buy this'**
  String get reason_unauthorized;

  /// No description provided for @reason_duplicate.
  ///
  /// In en, this message translates to:
  /// **'Charged twice'**
  String get reason_duplicate;

  /// No description provided for @reason_other.
  ///
  /// In en, this message translates to:
  /// **'Something else'**
  String get reason_other;

  /// No description provided for @disputeNote.
  ///
  /// In en, this message translates to:
  /// **'Tell the school more (optional)'**
  String get disputeNote;

  /// No description provided for @disputeSend.
  ///
  /// In en, this message translates to:
  /// **'Send to the school'**
  String get disputeSend;

  /// No description provided for @disputeSent.
  ///
  /// In en, this message translates to:
  /// **'Sent. The school will look into it and you\'ll be notified.'**
  String get disputeSent;

  /// No description provided for @dispute_open.
  ///
  /// In en, this message translates to:
  /// **'Open'**
  String get dispute_open;

  /// No description provided for @dispute_under_review.
  ///
  /// In en, this message translates to:
  /// **'Being reviewed'**
  String get dispute_under_review;

  /// No description provided for @dispute_resolved_refunded.
  ///
  /// In en, this message translates to:
  /// **'Refunded {amount}'**
  String dispute_resolved_refunded(String amount);

  /// No description provided for @dispute_resolved_denied.
  ///
  /// In en, this message translates to:
  /// **'Not refunded'**
  String get dispute_resolved_denied;

  /// No description provided for @inbox.
  ///
  /// In en, this message translates to:
  /// **'Inbox'**
  String get inbox;

  /// No description provided for @markAllRead.
  ///
  /// In en, this message translates to:
  /// **'Mark all read'**
  String get markAllRead;

  /// No description provided for @notificationSettings.
  ///
  /// In en, this message translates to:
  /// **'Notification settings'**
  String get notificationSettings;

  /// No description provided for @channelInApp.
  ///
  /// In en, this message translates to:
  /// **'In the app'**
  String get channelInApp;

  /// No description provided for @channelSms.
  ///
  /// In en, this message translates to:
  /// **'SMS'**
  String get channelSms;

  /// No description provided for @channelPush.
  ///
  /// In en, this message translates to:
  /// **'Push notifications'**
  String get channelPush;

  /// No description provided for @pushNotConfigured.
  ///
  /// In en, this message translates to:
  /// **'Push isn\'t set up in this build yet; you\'ll still see everything here.'**
  String get pushNotConfigured;

  /// No description provided for @more.
  ///
  /// In en, this message translates to:
  /// **'More'**
  String get more;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @privacyTitle.
  ///
  /// In en, this message translates to:
  /// **'My data & privacy'**
  String get privacyTitle;

  /// No description provided for @myData.
  ///
  /// In en, this message translates to:
  /// **'See my data'**
  String get myData;

  /// No description provided for @downloadCsv.
  ///
  /// In en, this message translates to:
  /// **'Download / share as CSV'**
  String get downloadCsv;

  /// No description provided for @dataRequests.
  ///
  /// In en, this message translates to:
  /// **'Data requests'**
  String get dataRequests;

  /// No description provided for @newDataRequest.
  ///
  /// In en, this message translates to:
  /// **'New request'**
  String get newDataRequest;

  /// No description provided for @request_export.
  ///
  /// In en, this message translates to:
  /// **'Export my data'**
  String get request_export;

  /// No description provided for @request_correction.
  ///
  /// In en, this message translates to:
  /// **'Correct something'**
  String get request_correction;

  /// No description provided for @request_deletion.
  ///
  /// In en, this message translates to:
  /// **'Delete personal data'**
  String get request_deletion;

  /// No description provided for @aboutMe.
  ///
  /// In en, this message translates to:
  /// **'About me'**
  String get aboutMe;

  /// No description provided for @aboutChild.
  ///
  /// In en, this message translates to:
  /// **'About {name}'**
  String aboutChild(String name);

  /// No description provided for @requestDetails.
  ///
  /// In en, this message translates to:
  /// **'Details'**
  String get requestDetails;

  /// No description provided for @retentionNotice.
  ///
  /// In en, this message translates to:
  /// **'Deleting removes names, contact details, photos and ID numbers. Financial records (payments, purchases, fees, disputes) are kept, because the law and the audit trail need them.'**
  String get retentionNotice;

  /// No description provided for @request_pending.
  ///
  /// In en, this message translates to:
  /// **'Received'**
  String get request_pending;

  /// No description provided for @request_in_progress.
  ///
  /// In en, this message translates to:
  /// **'In progress'**
  String get request_in_progress;

  /// No description provided for @request_completed.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get request_completed;

  /// No description provided for @request_rejected.
  ///
  /// In en, this message translates to:
  /// **'Declined'**
  String get request_rejected;

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
