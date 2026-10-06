// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Swahili (`sw`).
class AppLocalizationsSw extends AppLocalizations {
  AppLocalizationsSw([String locale = 'sw']) : super(locale);

  @override
  String get appTitle => 'SchoolDimes';

  @override
  String get signIn => 'Sign in';

  @override
  String get signInTitle => 'Welcome back';

  @override
  String get register => 'Create account';

  @override
  String get registerTitle => 'Create your parent account';

  @override
  String get haveAccount => 'Already have an account? Sign in';

  @override
  String get noAccount => 'New here? Create an account';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get passwordHelp => 'At least 8 characters, not too common.';

  @override
  String get fullName => 'Full name';

  @override
  String get phone => 'Phone number';

  @override
  String get language => 'Language';

  @override
  String get signOut => 'Sign out';

  @override
  String get sessionExpired => 'Your session ended. Please sign in again.';

  @override
  String get networkError =>
      'No connection. Check your data or Wi-Fi and try again.';

  @override
  String get retry => 'Retry';

  @override
  String get cancel => 'Cancel';

  @override
  String get confirm => 'Confirm';

  @override
  String get save => 'Save';

  @override
  String get done => 'Done';

  @override
  String get close => 'Close';

  @override
  String get next => 'Next';

  @override
  String get loading => 'Loading…';

  @override
  String get nothingYet => 'Nothing here yet.';

  @override
  String lastUpdated(String when) {
    return 'Offline — last updated $when';
  }

  @override
  String get appLock => 'App lock';

  @override
  String get appLockHelp =>
      'Ask for your fingerprint or phone PIN when the app opens.';

  @override
  String get unlock => 'Unlock';

  @override
  String get kycTitle => 'Verify your identity';

  @override
  String get kycIntro =>
      'Schools check a parent\'s ID before linking children. Enter it as it appears on your document.';

  @override
  String get kycNameOnId => 'Name on ID';

  @override
  String get kycDocType => 'Document';

  @override
  String get kycNationalId => 'National ID';

  @override
  String get kycPassport => 'Passport';

  @override
  String get kycNumber => 'ID number';

  @override
  String get kycSubmit => 'Submit for checking';

  @override
  String get kycSkip => 'Later';

  @override
  String get kycStatus_pending => 'Being checked by the school';

  @override
  String get kycStatus_verified => 'Verified';

  @override
  String get kycStatus_rejected =>
      'Not accepted — see the note and submit again';

  @override
  String get kycStatus_none => 'Not submitted';

  @override
  String get kycLimits =>
      'Your school decides what changes once you\'re verified; nothing is blocked by the app.';

  @override
  String kycNotes(String notes) {
    return 'Note from the school: $notes';
  }

  @override
  String get homeTitle => 'My children';

  @override
  String noChildren(String email) {
    return 'No children are linked to your account yet. Ask the school office to link them to $email.';
  }

  @override
  String get mainBalance => 'Spending';

  @override
  String get savingsBalance => 'Savings';

  @override
  String get lowBalance => 'Low balance';

  @override
  String get card_active => 'Card active';

  @override
  String get card_frozen => 'Card frozen';

  @override
  String get card_lost => 'Card lost';

  @override
  String get card_none => 'No card yet';

  @override
  String get recentPurchases => 'Recent activity';

  @override
  String get seeAll => 'See all';

  @override
  String get topUp => 'Top up';

  @override
  String get freeze => 'Freeze card';

  @override
  String get unfreeze => 'Unfreeze card';

  @override
  String freezeConfirm(String name) {
    return 'Freeze $name\'s card? Every purchase, transfer and fee payment is refused at once; canteen tills refuse it after their next refresh.';
  }

  @override
  String unfreezeConfirm(String name) {
    return 'Unfreeze $name\'s card so it can be used again?';
  }

  @override
  String get reportLost => 'Report card lost';

  @override
  String reportLostConfirm(String name) {
    return 'Report $name\'s card lost? This is permanent; the school issues a new card.';
  }

  @override
  String get tipOfTheDay => 'Money tip';

  @override
  String get history => 'History';

  @override
  String get controls => 'Limits';

  @override
  String get savings => 'Savings';

  @override
  String get cardAndP2p => 'Card & transfers';

  @override
  String get filterAll => 'All';

  @override
  String get filterPurchases => 'Purchases';

  @override
  String get filterTopUps => 'Top-ups';

  @override
  String get filterOther => 'Other';

  @override
  String get from => 'From';

  @override
  String get to => 'To';

  @override
  String get items => 'Items';

  @override
  String get reportProblem => 'Report a problem';

  @override
  String get disputeOpen => 'Problem reported';

  @override
  String get entry_pos_purchase => 'Purchase';

  @override
  String get entry_deposit => 'Top-up';

  @override
  String get entry_gift_voucher => 'Gift';

  @override
  String get entry_refund => 'Refund';

  @override
  String get entry_fee_payment => 'School fee';

  @override
  String get entry_p2p_transfer_in => 'Received from a friend';

  @override
  String get entry_p2p_transfer_out => 'Sent to a friend';

  @override
  String get entry_savings_move_in => 'Moved to savings';

  @override
  String get entry_savings_move_out => 'Moved from savings';

  @override
  String get entry_savings_withdrawal => 'Savings withdrawal';

  @override
  String get entry_shortfall_recovery => 'Shortfall repayment';

  @override
  String get entry_reversal => 'Reversal';

  @override
  String get entry_other => 'Other';

  @override
  String get topUpTitle => 'Top up';

  @override
  String get child => 'Child';

  @override
  String get amount => 'Amount (UGX)';

  @override
  String get amountInvalid => 'Enter a positive amount, e.g. 5000';

  @override
  String get channel => 'Pay with';

  @override
  String get channel_momo => 'Mobile money';

  @override
  String get channel_ussd => 'USSD';

  @override
  String get channel_bank => 'Bank';

  @override
  String get payerPhone => 'Phone that pays';

  @override
  String payNow(String amount) {
    return 'Pay $amount';
  }

  @override
  String get howToPay => 'How to pay';

  @override
  String get waitingConfirmation => 'Waiting for the payment to be confirmed…';

  @override
  String get stillWaiting =>
      'Still waiting. You can leave this screen: the money is added only when the payment provider confirms it.';

  @override
  String get depositStatus_pending => 'Waiting';

  @override
  String get depositStatus_confirmed => 'Paid — the money is on the card';

  @override
  String get depositStatus_failed => 'Failed — no money was taken';

  @override
  String get depositStatus_expired => 'Expired — not paid in time';

  @override
  String reference(String ref) {
    return 'Reference $ref';
  }

  @override
  String get tryAgain => 'Try again';

  @override
  String get depositHistory => 'Top-up history';

  @override
  String get payments => 'Payments';

  @override
  String get recurringTitle => 'Automatic top-ups';

  @override
  String get recurringAdd => 'New automatic top-up';

  @override
  String get frequency => 'How often';

  @override
  String get weekly => 'Weekly';

  @override
  String get monthly => 'Monthly';

  @override
  String get dayOfWeek => 'Day';

  @override
  String get dayOfMonth => 'Day of the month (1–28)';

  @override
  String nextRun(String when) {
    return 'Next: $when';
  }

  @override
  String get paused => 'Paused';

  @override
  String autoPaused(int count) {
    return 'Paused after $count failed payments';
  }

  @override
  String get resume => 'Resume';

  @override
  String get pause => 'Pause';

  @override
  String get delete => 'Delete';

  @override
  String lastStatus(String status) {
    return 'Last: $status';
  }

  @override
  String get weekday0 => 'Monday';

  @override
  String get weekday1 => 'Tuesday';

  @override
  String get weekday2 => 'Wednesday';

  @override
  String get weekday3 => 'Thursday';

  @override
  String get weekday4 => 'Friday';

  @override
  String get weekday5 => 'Saturday';

  @override
  String get weekday6 => 'Sunday';

  @override
  String get giftsTitle => 'Gifts & family links';

  @override
  String get sendGift => 'Send a gift';

  @override
  String get giftMessage => 'Message (shown to your family)';

  @override
  String get familyLinks => 'Links for relatives';

  @override
  String get familyLinksHelp =>
      'Relatives anywhere can top up using a link — no app or account. They only see your child\'s first name and school.';

  @override
  String createLink(String name) {
    return 'Create link for $name';
  }

  @override
  String get share => 'Share';

  @override
  String shareText(String name, String url) {
    return 'Send pocket money to $name at school: $url';
  }

  @override
  String get revoke => 'Turn off';

  @override
  String get revokeConfirm =>
      'Turn this link off? Anyone who has it can no longer use it.';

  @override
  String get linkOff => 'Off';

  @override
  String get contributionsReceived => 'Received from relatives';

  @override
  String get fundsTitle => 'Class funds';

  @override
  String fundRaised(String raised, String target) {
    return '$raised of $target';
  }

  @override
  String get contribute => 'Contribute';

  @override
  String get contributions => 'Contributions';

  @override
  String get createFund => 'Start a class fund';

  @override
  String get fundTitle => 'Title';

  @override
  String get fundPurpose => 'What it\'s for';

  @override
  String get fundTarget => 'Target (optional)';

  @override
  String get controlsTitle => 'Spending limits';

  @override
  String get controlsHelp =>
      'You can only make limits stricter than the school\'s. Blank = use the school\'s limit.';

  @override
  String schoolLimit(String value) {
    return 'School: $value';
  }

  @override
  String get noLimit => 'no limit';

  @override
  String get dailyCap => 'Daily limit';

  @override
  String get weeklyCap => 'Weekly limit';

  @override
  String get perTxnCap => 'Per purchase';

  @override
  String get p2pCap => 'Transfers per day';

  @override
  String get p2pEnabled => 'Allow transfers to friends';

  @override
  String get blockedCategories => 'Blocked categories';

  @override
  String get blockedItems => 'Blocked items';

  @override
  String get blockedMerchants => 'Blocked shops';

  @override
  String get lowBalanceAlert => 'Tell me when the balance drops below';

  @override
  String get saved => 'Saved';

  @override
  String get savingsTitle => 'Savings';

  @override
  String get moveIn => 'Move to savings';

  @override
  String get moveOut => 'Move to spending';

  @override
  String get goals => 'Goals';

  @override
  String get newGoal => 'New goal';

  @override
  String get goalName => 'Goal';

  @override
  String get goalTarget => 'Target';

  @override
  String get goalReached => 'Goal reached! 🎉';

  @override
  String get withdrawWindow => 'Withdrawal window';

  @override
  String get withdrawWindowHelp =>
      'Savings can be sent to your phone only between these dates (e.g. the holidays).';

  @override
  String get windowClosed => 'Closed';

  @override
  String windowOpen(String end) {
    return 'Open until $end';
  }

  @override
  String get setWindow => 'Set dates';

  @override
  String get withdraw => 'Withdraw to my phone';

  @override
  String get payoutStatus => 'Withdrawals';

  @override
  String get payout_pending => 'Sending';

  @override
  String get payout_succeeded => 'Sent';

  @override
  String get payout_failed => 'Failed — returned to savings';

  @override
  String get p2pHistory => 'Transfers between students';

  @override
  String p2pSent(String name) {
    return 'Sent to $name';
  }

  @override
  String p2pReceived(String name) {
    return 'Received from $name';
  }

  @override
  String get disputesTitle => 'Reported problems';

  @override
  String get disputeReason => 'What went wrong?';

  @override
  String get reason_wrong_amount => 'Wrong amount';

  @override
  String get reason_not_received => 'Didn\'t get the item';

  @override
  String get reason_unauthorized => 'My child didn\'t buy this';

  @override
  String get reason_duplicate => 'Charged twice';

  @override
  String get reason_other => 'Something else';

  @override
  String get disputeNote => 'Tell the school more (optional)';

  @override
  String get disputeSend => 'Send to the school';

  @override
  String get disputeSent =>
      'Sent. The school will look into it and you\'ll be notified.';

  @override
  String get dispute_open => 'Open';

  @override
  String get dispute_under_review => 'Being reviewed';

  @override
  String dispute_resolved_refunded(String amount) {
    return 'Refunded $amount';
  }

  @override
  String get dispute_resolved_denied => 'Not refunded';

  @override
  String get inbox => 'Inbox';

  @override
  String get markAllRead => 'Mark all read';

  @override
  String get notificationSettings => 'Notification settings';

  @override
  String get channelInApp => 'In the app';

  @override
  String get channelSms => 'SMS';

  @override
  String get channelPush => 'Push notifications';

  @override
  String get pushNotConfigured =>
      'Push isn\'t set up in this build yet; you\'ll still see everything here.';

  @override
  String get more => 'More';

  @override
  String get profile => 'Profile';

  @override
  String get privacyTitle => 'My data & privacy';

  @override
  String get myData => 'See my data';

  @override
  String get downloadCsv => 'Download / share as CSV';

  @override
  String get dataRequests => 'Data requests';

  @override
  String get newDataRequest => 'New request';

  @override
  String get request_export => 'Export my data';

  @override
  String get request_correction => 'Correct something';

  @override
  String get request_deletion => 'Delete personal data';

  @override
  String get aboutMe => 'About me';

  @override
  String aboutChild(String name) {
    return 'About $name';
  }

  @override
  String get requestDetails => 'Details';

  @override
  String get retentionNotice =>
      'Deleting removes names, contact details, photos and ID numbers. Financial records (payments, purchases, fees, disputes) are kept, because the law and the audit trail need them.';

  @override
  String get request_pending => 'Received';

  @override
  String get request_in_progress => 'In progress';

  @override
  String get request_completed => 'Done';

  @override
  String get request_rejected => 'Declined';

  @override
  String error(String message) {
    return 'Something went wrong: $message';
  }
}
