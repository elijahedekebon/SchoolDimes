/// Where tapping a notification goes (docs/PARENT_APP_READINESS.md,
/// "Deep links from notifications"). Pure function: unit-tested.
enum Destination { topUp, depositStatus, childHistory, recurring, savings, card, p2p, dispute, pooledFund, privacy, inbox }

class DeepLink {
  const DeepLink(this.destination, {this.studentId, this.id, this.walletId, this.suggestedAmount});
  final Destination destination;
  final int? studentId;
  final int? id;
  final int? walletId;
  final String? suggestedAmount;

  @override
  bool operator ==(Object other) =>
      other is DeepLink &&
      other.destination == destination &&
      other.studentId == studentId &&
      other.id == id &&
      other.walletId == walletId &&
      other.suggestedAmount == suggestedAmount;
  @override
  int get hashCode => Object.hash(destination, studentId, id, walletId, suggestedAmount);
  @override
  String toString() => 'DeepLink($destination, student=$studentId, id=$id, wallet=$walletId, amount=$suggestedAmount)';
}

int? _int(Object? v) => v is int ? v : (v is String ? int.tryParse(v) : null);

DeepLink deepLinkFor(String eventType, Map<String, dynamic> payload) {
  final student = _int(payload['student_id']);
  switch (eventType) {
    case 'low_balance':
      final action = (payload['action'] as Map?)?.cast<String, dynamic>() ?? const {};
      return DeepLink(Destination.topUp,
          studentId: _int(action['student_id']) ?? student,
          walletId: _int(action['wallet_id']) ?? _int(payload['wallet_id']),
          suggestedAmount: action['suggested_amount']?.toString());
    case 'deposit_confirmed':
    case 'deposit_failed':
      return DeepLink(Destination.depositStatus, id: _int(payload['deposit_id']), studentId: student);
    case 'contributor_topup_received':
    case 'gift_received':
    case 'attendance_tap_in':
      return DeepLink(Destination.childHistory, studentId: student);
    case 'recurring_topup_executed':
    case 'recurring_topup_failed':
    case 'recurring_topup_paused':
      return DeepLink(Destination.recurring, id: _int(payload['recurring_topup_id']), studentId: student);
    case 'savings_goal_reached':
    case 'savings_withdrawal_completed':
    case 'savings_withdrawal_failed':
      return DeepLink(Destination.savings, studentId: student);
    case 'card_frozen':
    case 'card_unfrozen':
    case 'card_reported_lost':
    case 'card_locked_pin_failures':
      return DeepLink(Destination.card, studentId: student, id: _int(payload['card_id']));
    case 'p2p_transfer_received':
      return DeepLink(Destination.p2p, studentId: student);
    case 'dispute_status_changed':
      return DeepLink(Destination.dispute, id: _int(payload['dispute_id']), studentId: student);
    case 'pooled_fund_contribution_confirmed':
      return DeepLink(Destination.pooledFund, id: _int(payload['fund_id']));
    case 'data_request_updated':
      return DeepLink(Destination.privacy, id: _int(payload['request_id']));
    default:
      return const DeepLink(Destination.inbox);
  }
}
