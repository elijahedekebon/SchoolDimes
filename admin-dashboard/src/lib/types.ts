/** Response shapes from docs/API_CONTRACTS.md (only the fields the dashboard uses). */
export type Money = string;

export type PosItem = {
  id: number;
  product: number | null;
  description: string;
  category: number | null;
  quantity: number;
  unit_price: Money;
  line_total: Money;
};

export type PosTransaction = {
  id: number;
  device: number;
  device_name: string;
  school: number;
  merchant: number | null;
  card: number | null;
  card_uid: string;
  student: number | null;
  student_name: string;
  wallet: number | null;
  channel: string;
  amount: Money;
  applied_amount: Money;
  shortfall_amount: Money;
  recovered_amount: Money;
  outstanding_amount: Money;
  idempotency_key: string;
  device_local_timestamp: string;
  received_at: string;
  sync_status: string;
  reject_reason: string;
  flags: string[];
  pin_verified: boolean;
  ledger_reference: string;
  review_status: string;
  resolution: string;
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_notes: string;
  items: PosItem[];
};

export type SalesBucket = { transactions: number; gross_amount: Money; collected_amount: Money; shortfall_amount?: Money };

export type SalesSummary = {
  from: string;
  to: string;
  totals: SalesBucket & { shortfall_amount: Money };
  by_day: Array<SalesBucket & { date: string }>;
  by_device: Array<SalesBucket & { device_id: number; device_name: string }>;
  by_merchant: Array<SalesBucket & { merchant_id: number | null; merchant_name: string }>;
  by_school?: Array<SalesBucket & { school_id: number; school_name: string }>;
};

export type Reconciliation = {
  school: number;
  date: string;
  timezone: string;
  devices: Array<{
    device_id: number;
    device_name: string;
    device_role: string;
    status: string;
    last_sync_at: string | null;
    transactions: number;
    rejected: number;
    collected_amount: Money;
    ledger_amount: Money;
    matches: boolean;
  }>;
  stale_devices: Array<{ device_id: number; device_name: string; last_sync_at: string | null }>;
  unresolved_reviews: { count: number; outstanding_shortfall: Money };
  deposits: {
    confirmed_count: number;
    confirmed_amount: Money;
    ledger_amount: Money;
    matches: boolean;
    pending_count: number;
    pending_amount: Money;
  };
  fee_payments: { count: number; amount: Money; ledger_amount: Money; matches: boolean };
  pooled_funds: Array<{ fund_id: number; title: string; status: string; balance: Money }>;
  system_wallets: Record<string, Money>;
  books_total: Money;
  books_balanced: boolean;
};

export type Student = {
  id: number;
  school: number;
  name: string;
  class_name: string;
  date_of_birth: string | null;
  photo: string | null;
  created_at: string;
};

export type Card = {
  id: number;
  school: number;
  student: number;
  card_uid: string;
  status: "active" | "frozen" | "lost";
  biometric_enrolled: boolean;
  issued_at: string;
  updated_at: string;
};

export type Wallet = { id: number; school: number; student: number | null; wallet_type: string; balance: Money };

export type LedgerEntry = {
  id: number;
  wallet: number;
  amount: Money;
  direction: "credit" | "debit";
  entry_type: string;
  reference_id: string;
  description: string;
  created_at: string;
};

export type Device = {
  id: number;
  school: number;
  merchant: number | null;
  device_name: string;
  device_role: "canteen" | "merchant" | "attendance";
  token_prefix: string;
  status: "active" | "revoked";
  last_seen_at: string | null;
  last_sync_at: string | null;
  app_version: string;
  created_at: string;
  revoked_at: string | null;
  device_token?: string;
};
