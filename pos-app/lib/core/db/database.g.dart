// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $CachedCardsTable extends CachedCards
    with TableInfo<$CachedCardsTable, CachedCard> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedCardsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _cardUidMeta = const VerificationMeta(
    'cardUid',
  );
  @override
  late final GeneratedColumn<String> cardUid = GeneratedColumn<String>(
    'card_uid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _cardIdMeta = const VerificationMeta('cardId');
  @override
  late final GeneratedColumn<int> cardId = GeneratedColumn<int>(
    'card_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _pinHashMeta = const VerificationMeta(
    'pinHash',
  );
  @override
  late final GeneratedColumn<String> pinHash = GeneratedColumn<String>(
    'pin_hash',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _studentIdMeta = const VerificationMeta(
    'studentId',
  );
  @override
  late final GeneratedColumn<int> studentId = GeneratedColumn<int>(
    'student_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _displayNameMeta = const VerificationMeta(
    'displayName',
  );
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
    'display_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _photoUrlMeta = const VerificationMeta(
    'photoUrl',
  );
  @override
  late final GeneratedColumn<String> photoUrl = GeneratedColumn<String>(
    'photo_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _schoolIdMeta = const VerificationMeta(
    'schoolId',
  );
  @override
  late final GeneratedColumn<int> schoolId = GeneratedColumn<int>(
    'school_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _walletIdMeta = const VerificationMeta(
    'walletId',
  );
  @override
  late final GeneratedColumn<int> walletId = GeneratedColumn<int>(
    'wallet_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _balanceCentsMeta = const VerificationMeta(
    'balanceCents',
  );
  @override
  late final GeneratedColumn<int> balanceCents = GeneratedColumn<int>(
    'balance_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _todaySpendCentsMeta = const VerificationMeta(
    'todaySpendCents',
  );
  @override
  late final GeneratedColumn<int> todaySpendCents = GeneratedColumn<int>(
    'today_spend_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _weekSpendCentsMeta = const VerificationMeta(
    'weekSpendCents',
  );
  @override
  late final GeneratedColumn<int> weekSpendCents = GeneratedColumn<int>(
    'week_spend_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _spendDayMeta = const VerificationMeta(
    'spendDay',
  );
  @override
  late final GeneratedColumn<String> spendDay = GeneratedColumn<String>(
    'spend_day',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _weekStartMeta = const VerificationMeta(
    'weekStart',
  );
  @override
  late final GeneratedColumn<String> weekStart = GeneratedColumn<String>(
    'week_start',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _offlineCeilingCentsMeta =
      const VerificationMeta('offlineCeilingCents');
  @override
  late final GeneratedColumn<int> offlineCeilingCents = GeneratedColumn<int>(
    'offline_ceiling_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _policyJsonMeta = const VerificationMeta(
    'policyJson',
  );
  @override
  late final GeneratedColumn<String> policyJson = GeneratedColumn<String>(
    'policy_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _balanceAsOfMeta = const VerificationMeta(
    'balanceAsOf',
  );
  @override
  late final GeneratedColumn<DateTime> balanceAsOf = GeneratedColumn<DateTime>(
    'balance_as_of',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    cardUid,
    cardId,
    status,
    pinHash,
    studentId,
    displayName,
    photoUrl,
    schoolId,
    walletId,
    balanceCents,
    todaySpendCents,
    weekSpendCents,
    spendDay,
    weekStart,
    offlineCeilingCents,
    policyJson,
    balanceAsOf,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_cards';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedCard> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('card_uid')) {
      context.handle(
        _cardUidMeta,
        cardUid.isAcceptableOrUnknown(data['card_uid']!, _cardUidMeta),
      );
    } else if (isInserting) {
      context.missing(_cardUidMeta);
    }
    if (data.containsKey('card_id')) {
      context.handle(
        _cardIdMeta,
        cardId.isAcceptableOrUnknown(data['card_id']!, _cardIdMeta),
      );
    } else if (isInserting) {
      context.missing(_cardIdMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('pin_hash')) {
      context.handle(
        _pinHashMeta,
        pinHash.isAcceptableOrUnknown(data['pin_hash']!, _pinHashMeta),
      );
    } else if (isInserting) {
      context.missing(_pinHashMeta);
    }
    if (data.containsKey('student_id')) {
      context.handle(
        _studentIdMeta,
        studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta),
      );
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    if (data.containsKey('display_name')) {
      context.handle(
        _displayNameMeta,
        displayName.isAcceptableOrUnknown(
          data['display_name']!,
          _displayNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_displayNameMeta);
    }
    if (data.containsKey('photo_url')) {
      context.handle(
        _photoUrlMeta,
        photoUrl.isAcceptableOrUnknown(data['photo_url']!, _photoUrlMeta),
      );
    }
    if (data.containsKey('school_id')) {
      context.handle(
        _schoolIdMeta,
        schoolId.isAcceptableOrUnknown(data['school_id']!, _schoolIdMeta),
      );
    } else if (isInserting) {
      context.missing(_schoolIdMeta);
    }
    if (data.containsKey('wallet_id')) {
      context.handle(
        _walletIdMeta,
        walletId.isAcceptableOrUnknown(data['wallet_id']!, _walletIdMeta),
      );
    } else if (isInserting) {
      context.missing(_walletIdMeta);
    }
    if (data.containsKey('balance_cents')) {
      context.handle(
        _balanceCentsMeta,
        balanceCents.isAcceptableOrUnknown(
          data['balance_cents']!,
          _balanceCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_balanceCentsMeta);
    }
    if (data.containsKey('today_spend_cents')) {
      context.handle(
        _todaySpendCentsMeta,
        todaySpendCents.isAcceptableOrUnknown(
          data['today_spend_cents']!,
          _todaySpendCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_todaySpendCentsMeta);
    }
    if (data.containsKey('week_spend_cents')) {
      context.handle(
        _weekSpendCentsMeta,
        weekSpendCents.isAcceptableOrUnknown(
          data['week_spend_cents']!,
          _weekSpendCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_weekSpendCentsMeta);
    }
    if (data.containsKey('spend_day')) {
      context.handle(
        _spendDayMeta,
        spendDay.isAcceptableOrUnknown(data['spend_day']!, _spendDayMeta),
      );
    } else if (isInserting) {
      context.missing(_spendDayMeta);
    }
    if (data.containsKey('week_start')) {
      context.handle(
        _weekStartMeta,
        weekStart.isAcceptableOrUnknown(data['week_start']!, _weekStartMeta),
      );
    } else if (isInserting) {
      context.missing(_weekStartMeta);
    }
    if (data.containsKey('offline_ceiling_cents')) {
      context.handle(
        _offlineCeilingCentsMeta,
        offlineCeilingCents.isAcceptableOrUnknown(
          data['offline_ceiling_cents']!,
          _offlineCeilingCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_offlineCeilingCentsMeta);
    }
    if (data.containsKey('policy_json')) {
      context.handle(
        _policyJsonMeta,
        policyJson.isAcceptableOrUnknown(data['policy_json']!, _policyJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_policyJsonMeta);
    }
    if (data.containsKey('balance_as_of')) {
      context.handle(
        _balanceAsOfMeta,
        balanceAsOf.isAcceptableOrUnknown(
          data['balance_as_of']!,
          _balanceAsOfMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_balanceAsOfMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {cardUid};
  @override
  CachedCard map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedCard(
      cardUid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}card_uid'],
      )!,
      cardId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}card_id'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      pinHash: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}pin_hash'],
      )!,
      studentId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}student_id'],
      )!,
      displayName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}display_name'],
      )!,
      photoUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}photo_url'],
      ),
      schoolId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}school_id'],
      )!,
      walletId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}wallet_id'],
      )!,
      balanceCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}balance_cents'],
      )!,
      todaySpendCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}today_spend_cents'],
      )!,
      weekSpendCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}week_spend_cents'],
      )!,
      spendDay: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}spend_day'],
      )!,
      weekStart: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}week_start'],
      )!,
      offlineCeilingCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}offline_ceiling_cents'],
      )!,
      policyJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}policy_json'],
      )!,
      balanceAsOf: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}balance_as_of'],
      )!,
    );
  }

  @override
  $CachedCardsTable createAlias(String alias) {
    return $CachedCardsTable(attachedDatabase, alias);
  }
}

class CachedCard extends DataClass implements Insertable<CachedCard> {
  final String cardUid;
  final int cardId;
  final String status;
  final String pinHash;
  final int studentId;
  final String displayName;
  final String? photoUrl;
  final int schoolId;
  final int walletId;
  final int balanceCents;
  final int todaySpendCents;
  final int weekSpendCents;
  final String spendDay;
  final String weekStart;
  final int offlineCeilingCents;
  final String policyJson;
  final DateTime balanceAsOf;
  const CachedCard({
    required this.cardUid,
    required this.cardId,
    required this.status,
    required this.pinHash,
    required this.studentId,
    required this.displayName,
    this.photoUrl,
    required this.schoolId,
    required this.walletId,
    required this.balanceCents,
    required this.todaySpendCents,
    required this.weekSpendCents,
    required this.spendDay,
    required this.weekStart,
    required this.offlineCeilingCents,
    required this.policyJson,
    required this.balanceAsOf,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['card_uid'] = Variable<String>(cardUid);
    map['card_id'] = Variable<int>(cardId);
    map['status'] = Variable<String>(status);
    map['pin_hash'] = Variable<String>(pinHash);
    map['student_id'] = Variable<int>(studentId);
    map['display_name'] = Variable<String>(displayName);
    if (!nullToAbsent || photoUrl != null) {
      map['photo_url'] = Variable<String>(photoUrl);
    }
    map['school_id'] = Variable<int>(schoolId);
    map['wallet_id'] = Variable<int>(walletId);
    map['balance_cents'] = Variable<int>(balanceCents);
    map['today_spend_cents'] = Variable<int>(todaySpendCents);
    map['week_spend_cents'] = Variable<int>(weekSpendCents);
    map['spend_day'] = Variable<String>(spendDay);
    map['week_start'] = Variable<String>(weekStart);
    map['offline_ceiling_cents'] = Variable<int>(offlineCeilingCents);
    map['policy_json'] = Variable<String>(policyJson);
    map['balance_as_of'] = Variable<DateTime>(balanceAsOf);
    return map;
  }

  CachedCardsCompanion toCompanion(bool nullToAbsent) {
    return CachedCardsCompanion(
      cardUid: Value(cardUid),
      cardId: Value(cardId),
      status: Value(status),
      pinHash: Value(pinHash),
      studentId: Value(studentId),
      displayName: Value(displayName),
      photoUrl: photoUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(photoUrl),
      schoolId: Value(schoolId),
      walletId: Value(walletId),
      balanceCents: Value(balanceCents),
      todaySpendCents: Value(todaySpendCents),
      weekSpendCents: Value(weekSpendCents),
      spendDay: Value(spendDay),
      weekStart: Value(weekStart),
      offlineCeilingCents: Value(offlineCeilingCents),
      policyJson: Value(policyJson),
      balanceAsOf: Value(balanceAsOf),
    );
  }

  factory CachedCard.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedCard(
      cardUid: serializer.fromJson<String>(json['cardUid']),
      cardId: serializer.fromJson<int>(json['cardId']),
      status: serializer.fromJson<String>(json['status']),
      pinHash: serializer.fromJson<String>(json['pinHash']),
      studentId: serializer.fromJson<int>(json['studentId']),
      displayName: serializer.fromJson<String>(json['displayName']),
      photoUrl: serializer.fromJson<String?>(json['photoUrl']),
      schoolId: serializer.fromJson<int>(json['schoolId']),
      walletId: serializer.fromJson<int>(json['walletId']),
      balanceCents: serializer.fromJson<int>(json['balanceCents']),
      todaySpendCents: serializer.fromJson<int>(json['todaySpendCents']),
      weekSpendCents: serializer.fromJson<int>(json['weekSpendCents']),
      spendDay: serializer.fromJson<String>(json['spendDay']),
      weekStart: serializer.fromJson<String>(json['weekStart']),
      offlineCeilingCents: serializer.fromJson<int>(
        json['offlineCeilingCents'],
      ),
      policyJson: serializer.fromJson<String>(json['policyJson']),
      balanceAsOf: serializer.fromJson<DateTime>(json['balanceAsOf']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'cardUid': serializer.toJson<String>(cardUid),
      'cardId': serializer.toJson<int>(cardId),
      'status': serializer.toJson<String>(status),
      'pinHash': serializer.toJson<String>(pinHash),
      'studentId': serializer.toJson<int>(studentId),
      'displayName': serializer.toJson<String>(displayName),
      'photoUrl': serializer.toJson<String?>(photoUrl),
      'schoolId': serializer.toJson<int>(schoolId),
      'walletId': serializer.toJson<int>(walletId),
      'balanceCents': serializer.toJson<int>(balanceCents),
      'todaySpendCents': serializer.toJson<int>(todaySpendCents),
      'weekSpendCents': serializer.toJson<int>(weekSpendCents),
      'spendDay': serializer.toJson<String>(spendDay),
      'weekStart': serializer.toJson<String>(weekStart),
      'offlineCeilingCents': serializer.toJson<int>(offlineCeilingCents),
      'policyJson': serializer.toJson<String>(policyJson),
      'balanceAsOf': serializer.toJson<DateTime>(balanceAsOf),
    };
  }

  CachedCard copyWith({
    String? cardUid,
    int? cardId,
    String? status,
    String? pinHash,
    int? studentId,
    String? displayName,
    Value<String?> photoUrl = const Value.absent(),
    int? schoolId,
    int? walletId,
    int? balanceCents,
    int? todaySpendCents,
    int? weekSpendCents,
    String? spendDay,
    String? weekStart,
    int? offlineCeilingCents,
    String? policyJson,
    DateTime? balanceAsOf,
  }) => CachedCard(
    cardUid: cardUid ?? this.cardUid,
    cardId: cardId ?? this.cardId,
    status: status ?? this.status,
    pinHash: pinHash ?? this.pinHash,
    studentId: studentId ?? this.studentId,
    displayName: displayName ?? this.displayName,
    photoUrl: photoUrl.present ? photoUrl.value : this.photoUrl,
    schoolId: schoolId ?? this.schoolId,
    walletId: walletId ?? this.walletId,
    balanceCents: balanceCents ?? this.balanceCents,
    todaySpendCents: todaySpendCents ?? this.todaySpendCents,
    weekSpendCents: weekSpendCents ?? this.weekSpendCents,
    spendDay: spendDay ?? this.spendDay,
    weekStart: weekStart ?? this.weekStart,
    offlineCeilingCents: offlineCeilingCents ?? this.offlineCeilingCents,
    policyJson: policyJson ?? this.policyJson,
    balanceAsOf: balanceAsOf ?? this.balanceAsOf,
  );
  CachedCard copyWithCompanion(CachedCardsCompanion data) {
    return CachedCard(
      cardUid: data.cardUid.present ? data.cardUid.value : this.cardUid,
      cardId: data.cardId.present ? data.cardId.value : this.cardId,
      status: data.status.present ? data.status.value : this.status,
      pinHash: data.pinHash.present ? data.pinHash.value : this.pinHash,
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      displayName: data.displayName.present
          ? data.displayName.value
          : this.displayName,
      photoUrl: data.photoUrl.present ? data.photoUrl.value : this.photoUrl,
      schoolId: data.schoolId.present ? data.schoolId.value : this.schoolId,
      walletId: data.walletId.present ? data.walletId.value : this.walletId,
      balanceCents: data.balanceCents.present
          ? data.balanceCents.value
          : this.balanceCents,
      todaySpendCents: data.todaySpendCents.present
          ? data.todaySpendCents.value
          : this.todaySpendCents,
      weekSpendCents: data.weekSpendCents.present
          ? data.weekSpendCents.value
          : this.weekSpendCents,
      spendDay: data.spendDay.present ? data.spendDay.value : this.spendDay,
      weekStart: data.weekStart.present ? data.weekStart.value : this.weekStart,
      offlineCeilingCents: data.offlineCeilingCents.present
          ? data.offlineCeilingCents.value
          : this.offlineCeilingCents,
      policyJson: data.policyJson.present
          ? data.policyJson.value
          : this.policyJson,
      balanceAsOf: data.balanceAsOf.present
          ? data.balanceAsOf.value
          : this.balanceAsOf,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedCard(')
          ..write('cardUid: $cardUid, ')
          ..write('cardId: $cardId, ')
          ..write('status: $status, ')
          ..write('pinHash: $pinHash, ')
          ..write('studentId: $studentId, ')
          ..write('displayName: $displayName, ')
          ..write('photoUrl: $photoUrl, ')
          ..write('schoolId: $schoolId, ')
          ..write('walletId: $walletId, ')
          ..write('balanceCents: $balanceCents, ')
          ..write('todaySpendCents: $todaySpendCents, ')
          ..write('weekSpendCents: $weekSpendCents, ')
          ..write('spendDay: $spendDay, ')
          ..write('weekStart: $weekStart, ')
          ..write('offlineCeilingCents: $offlineCeilingCents, ')
          ..write('policyJson: $policyJson, ')
          ..write('balanceAsOf: $balanceAsOf')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    cardUid,
    cardId,
    status,
    pinHash,
    studentId,
    displayName,
    photoUrl,
    schoolId,
    walletId,
    balanceCents,
    todaySpendCents,
    weekSpendCents,
    spendDay,
    weekStart,
    offlineCeilingCents,
    policyJson,
    balanceAsOf,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedCard &&
          other.cardUid == this.cardUid &&
          other.cardId == this.cardId &&
          other.status == this.status &&
          other.pinHash == this.pinHash &&
          other.studentId == this.studentId &&
          other.displayName == this.displayName &&
          other.photoUrl == this.photoUrl &&
          other.schoolId == this.schoolId &&
          other.walletId == this.walletId &&
          other.balanceCents == this.balanceCents &&
          other.todaySpendCents == this.todaySpendCents &&
          other.weekSpendCents == this.weekSpendCents &&
          other.spendDay == this.spendDay &&
          other.weekStart == this.weekStart &&
          other.offlineCeilingCents == this.offlineCeilingCents &&
          other.policyJson == this.policyJson &&
          other.balanceAsOf == this.balanceAsOf);
}

class CachedCardsCompanion extends UpdateCompanion<CachedCard> {
  final Value<String> cardUid;
  final Value<int> cardId;
  final Value<String> status;
  final Value<String> pinHash;
  final Value<int> studentId;
  final Value<String> displayName;
  final Value<String?> photoUrl;
  final Value<int> schoolId;
  final Value<int> walletId;
  final Value<int> balanceCents;
  final Value<int> todaySpendCents;
  final Value<int> weekSpendCents;
  final Value<String> spendDay;
  final Value<String> weekStart;
  final Value<int> offlineCeilingCents;
  final Value<String> policyJson;
  final Value<DateTime> balanceAsOf;
  final Value<int> rowid;
  const CachedCardsCompanion({
    this.cardUid = const Value.absent(),
    this.cardId = const Value.absent(),
    this.status = const Value.absent(),
    this.pinHash = const Value.absent(),
    this.studentId = const Value.absent(),
    this.displayName = const Value.absent(),
    this.photoUrl = const Value.absent(),
    this.schoolId = const Value.absent(),
    this.walletId = const Value.absent(),
    this.balanceCents = const Value.absent(),
    this.todaySpendCents = const Value.absent(),
    this.weekSpendCents = const Value.absent(),
    this.spendDay = const Value.absent(),
    this.weekStart = const Value.absent(),
    this.offlineCeilingCents = const Value.absent(),
    this.policyJson = const Value.absent(),
    this.balanceAsOf = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedCardsCompanion.insert({
    required String cardUid,
    required int cardId,
    required String status,
    required String pinHash,
    required int studentId,
    required String displayName,
    this.photoUrl = const Value.absent(),
    required int schoolId,
    required int walletId,
    required int balanceCents,
    required int todaySpendCents,
    required int weekSpendCents,
    required String spendDay,
    required String weekStart,
    required int offlineCeilingCents,
    required String policyJson,
    required DateTime balanceAsOf,
    this.rowid = const Value.absent(),
  }) : cardUid = Value(cardUid),
       cardId = Value(cardId),
       status = Value(status),
       pinHash = Value(pinHash),
       studentId = Value(studentId),
       displayName = Value(displayName),
       schoolId = Value(schoolId),
       walletId = Value(walletId),
       balanceCents = Value(balanceCents),
       todaySpendCents = Value(todaySpendCents),
       weekSpendCents = Value(weekSpendCents),
       spendDay = Value(spendDay),
       weekStart = Value(weekStart),
       offlineCeilingCents = Value(offlineCeilingCents),
       policyJson = Value(policyJson),
       balanceAsOf = Value(balanceAsOf);
  static Insertable<CachedCard> custom({
    Expression<String>? cardUid,
    Expression<int>? cardId,
    Expression<String>? status,
    Expression<String>? pinHash,
    Expression<int>? studentId,
    Expression<String>? displayName,
    Expression<String>? photoUrl,
    Expression<int>? schoolId,
    Expression<int>? walletId,
    Expression<int>? balanceCents,
    Expression<int>? todaySpendCents,
    Expression<int>? weekSpendCents,
    Expression<String>? spendDay,
    Expression<String>? weekStart,
    Expression<int>? offlineCeilingCents,
    Expression<String>? policyJson,
    Expression<DateTime>? balanceAsOf,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (cardUid != null) 'card_uid': cardUid,
      if (cardId != null) 'card_id': cardId,
      if (status != null) 'status': status,
      if (pinHash != null) 'pin_hash': pinHash,
      if (studentId != null) 'student_id': studentId,
      if (displayName != null) 'display_name': displayName,
      if (photoUrl != null) 'photo_url': photoUrl,
      if (schoolId != null) 'school_id': schoolId,
      if (walletId != null) 'wallet_id': walletId,
      if (balanceCents != null) 'balance_cents': balanceCents,
      if (todaySpendCents != null) 'today_spend_cents': todaySpendCents,
      if (weekSpendCents != null) 'week_spend_cents': weekSpendCents,
      if (spendDay != null) 'spend_day': spendDay,
      if (weekStart != null) 'week_start': weekStart,
      if (offlineCeilingCents != null)
        'offline_ceiling_cents': offlineCeilingCents,
      if (policyJson != null) 'policy_json': policyJson,
      if (balanceAsOf != null) 'balance_as_of': balanceAsOf,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedCardsCompanion copyWith({
    Value<String>? cardUid,
    Value<int>? cardId,
    Value<String>? status,
    Value<String>? pinHash,
    Value<int>? studentId,
    Value<String>? displayName,
    Value<String?>? photoUrl,
    Value<int>? schoolId,
    Value<int>? walletId,
    Value<int>? balanceCents,
    Value<int>? todaySpendCents,
    Value<int>? weekSpendCents,
    Value<String>? spendDay,
    Value<String>? weekStart,
    Value<int>? offlineCeilingCents,
    Value<String>? policyJson,
    Value<DateTime>? balanceAsOf,
    Value<int>? rowid,
  }) {
    return CachedCardsCompanion(
      cardUid: cardUid ?? this.cardUid,
      cardId: cardId ?? this.cardId,
      status: status ?? this.status,
      pinHash: pinHash ?? this.pinHash,
      studentId: studentId ?? this.studentId,
      displayName: displayName ?? this.displayName,
      photoUrl: photoUrl ?? this.photoUrl,
      schoolId: schoolId ?? this.schoolId,
      walletId: walletId ?? this.walletId,
      balanceCents: balanceCents ?? this.balanceCents,
      todaySpendCents: todaySpendCents ?? this.todaySpendCents,
      weekSpendCents: weekSpendCents ?? this.weekSpendCents,
      spendDay: spendDay ?? this.spendDay,
      weekStart: weekStart ?? this.weekStart,
      offlineCeilingCents: offlineCeilingCents ?? this.offlineCeilingCents,
      policyJson: policyJson ?? this.policyJson,
      balanceAsOf: balanceAsOf ?? this.balanceAsOf,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (cardUid.present) {
      map['card_uid'] = Variable<String>(cardUid.value);
    }
    if (cardId.present) {
      map['card_id'] = Variable<int>(cardId.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (pinHash.present) {
      map['pin_hash'] = Variable<String>(pinHash.value);
    }
    if (studentId.present) {
      map['student_id'] = Variable<int>(studentId.value);
    }
    if (displayName.present) {
      map['display_name'] = Variable<String>(displayName.value);
    }
    if (photoUrl.present) {
      map['photo_url'] = Variable<String>(photoUrl.value);
    }
    if (schoolId.present) {
      map['school_id'] = Variable<int>(schoolId.value);
    }
    if (walletId.present) {
      map['wallet_id'] = Variable<int>(walletId.value);
    }
    if (balanceCents.present) {
      map['balance_cents'] = Variable<int>(balanceCents.value);
    }
    if (todaySpendCents.present) {
      map['today_spend_cents'] = Variable<int>(todaySpendCents.value);
    }
    if (weekSpendCents.present) {
      map['week_spend_cents'] = Variable<int>(weekSpendCents.value);
    }
    if (spendDay.present) {
      map['spend_day'] = Variable<String>(spendDay.value);
    }
    if (weekStart.present) {
      map['week_start'] = Variable<String>(weekStart.value);
    }
    if (offlineCeilingCents.present) {
      map['offline_ceiling_cents'] = Variable<int>(offlineCeilingCents.value);
    }
    if (policyJson.present) {
      map['policy_json'] = Variable<String>(policyJson.value);
    }
    if (balanceAsOf.present) {
      map['balance_as_of'] = Variable<DateTime>(balanceAsOf.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedCardsCompanion(')
          ..write('cardUid: $cardUid, ')
          ..write('cardId: $cardId, ')
          ..write('status: $status, ')
          ..write('pinHash: $pinHash, ')
          ..write('studentId: $studentId, ')
          ..write('displayName: $displayName, ')
          ..write('photoUrl: $photoUrl, ')
          ..write('schoolId: $schoolId, ')
          ..write('walletId: $walletId, ')
          ..write('balanceCents: $balanceCents, ')
          ..write('todaySpendCents: $todaySpendCents, ')
          ..write('weekSpendCents: $weekSpendCents, ')
          ..write('spendDay: $spendDay, ')
          ..write('weekStart: $weekStart, ')
          ..write('offlineCeilingCents: $offlineCeilingCents, ')
          ..write('policyJson: $policyJson, ')
          ..write('balanceAsOf: $balanceAsOf, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ProductsTable extends Products with TableInfo<$ProductsTable, Product> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ProductsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _categoryIdMeta = const VerificationMeta(
    'categoryId',
  );
  @override
  late final GeneratedColumn<int> categoryId = GeneratedColumn<int>(
    'category_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _categoryNameMeta = const VerificationMeta(
    'categoryName',
  );
  @override
  late final GeneratedColumn<String> categoryName = GeneratedColumn<String>(
    'category_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _priceCentsMeta = const VerificationMeta(
    'priceCents',
  );
  @override
  late final GeneratedColumn<int> priceCents = GeneratedColumn<int>(
    'price_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _activeMeta = const VerificationMeta('active');
  @override
  late final GeneratedColumn<bool> active = GeneratedColumn<bool>(
    'active',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("active" IN (0, 1))',
    ),
  );
  static const VerificationMeta _schoolIdMeta = const VerificationMeta(
    'schoolId',
  );
  @override
  late final GeneratedColumn<int> schoolId = GeneratedColumn<int>(
    'school_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _merchantIdMeta = const VerificationMeta(
    'merchantId',
  );
  @override
  late final GeneratedColumn<int> merchantId = GeneratedColumn<int>(
    'merchant_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    name,
    categoryId,
    categoryName,
    priceCents,
    active,
    schoolId,
    merchantId,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'products';
  @override
  VerificationContext validateIntegrity(
    Insertable<Product> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('category_id')) {
      context.handle(
        _categoryIdMeta,
        categoryId.isAcceptableOrUnknown(data['category_id']!, _categoryIdMeta),
      );
    } else if (isInserting) {
      context.missing(_categoryIdMeta);
    }
    if (data.containsKey('category_name')) {
      context.handle(
        _categoryNameMeta,
        categoryName.isAcceptableOrUnknown(
          data['category_name']!,
          _categoryNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_categoryNameMeta);
    }
    if (data.containsKey('price_cents')) {
      context.handle(
        _priceCentsMeta,
        priceCents.isAcceptableOrUnknown(data['price_cents']!, _priceCentsMeta),
      );
    } else if (isInserting) {
      context.missing(_priceCentsMeta);
    }
    if (data.containsKey('active')) {
      context.handle(
        _activeMeta,
        active.isAcceptableOrUnknown(data['active']!, _activeMeta),
      );
    } else if (isInserting) {
      context.missing(_activeMeta);
    }
    if (data.containsKey('school_id')) {
      context.handle(
        _schoolIdMeta,
        schoolId.isAcceptableOrUnknown(data['school_id']!, _schoolIdMeta),
      );
    } else if (isInserting) {
      context.missing(_schoolIdMeta);
    }
    if (data.containsKey('merchant_id')) {
      context.handle(
        _merchantIdMeta,
        merchantId.isAcceptableOrUnknown(data['merchant_id']!, _merchantIdMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Product map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Product(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      categoryId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}category_id'],
      )!,
      categoryName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}category_name'],
      )!,
      priceCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}price_cents'],
      )!,
      active: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}active'],
      )!,
      schoolId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}school_id'],
      )!,
      merchantId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}merchant_id'],
      ),
    );
  }

  @override
  $ProductsTable createAlias(String alias) {
    return $ProductsTable(attachedDatabase, alias);
  }
}

class Product extends DataClass implements Insertable<Product> {
  final int id;
  final String name;
  final int categoryId;
  final String categoryName;
  final int priceCents;
  final bool active;
  final int schoolId;
  final int? merchantId;
  const Product({
    required this.id,
    required this.name,
    required this.categoryId,
    required this.categoryName,
    required this.priceCents,
    required this.active,
    required this.schoolId,
    this.merchantId,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['name'] = Variable<String>(name);
    map['category_id'] = Variable<int>(categoryId);
    map['category_name'] = Variable<String>(categoryName);
    map['price_cents'] = Variable<int>(priceCents);
    map['active'] = Variable<bool>(active);
    map['school_id'] = Variable<int>(schoolId);
    if (!nullToAbsent || merchantId != null) {
      map['merchant_id'] = Variable<int>(merchantId);
    }
    return map;
  }

  ProductsCompanion toCompanion(bool nullToAbsent) {
    return ProductsCompanion(
      id: Value(id),
      name: Value(name),
      categoryId: Value(categoryId),
      categoryName: Value(categoryName),
      priceCents: Value(priceCents),
      active: Value(active),
      schoolId: Value(schoolId),
      merchantId: merchantId == null && nullToAbsent
          ? const Value.absent()
          : Value(merchantId),
    );
  }

  factory Product.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Product(
      id: serializer.fromJson<int>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      categoryId: serializer.fromJson<int>(json['categoryId']),
      categoryName: serializer.fromJson<String>(json['categoryName']),
      priceCents: serializer.fromJson<int>(json['priceCents']),
      active: serializer.fromJson<bool>(json['active']),
      schoolId: serializer.fromJson<int>(json['schoolId']),
      merchantId: serializer.fromJson<int?>(json['merchantId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'name': serializer.toJson<String>(name),
      'categoryId': serializer.toJson<int>(categoryId),
      'categoryName': serializer.toJson<String>(categoryName),
      'priceCents': serializer.toJson<int>(priceCents),
      'active': serializer.toJson<bool>(active),
      'schoolId': serializer.toJson<int>(schoolId),
      'merchantId': serializer.toJson<int?>(merchantId),
    };
  }

  Product copyWith({
    int? id,
    String? name,
    int? categoryId,
    String? categoryName,
    int? priceCents,
    bool? active,
    int? schoolId,
    Value<int?> merchantId = const Value.absent(),
  }) => Product(
    id: id ?? this.id,
    name: name ?? this.name,
    categoryId: categoryId ?? this.categoryId,
    categoryName: categoryName ?? this.categoryName,
    priceCents: priceCents ?? this.priceCents,
    active: active ?? this.active,
    schoolId: schoolId ?? this.schoolId,
    merchantId: merchantId.present ? merchantId.value : this.merchantId,
  );
  Product copyWithCompanion(ProductsCompanion data) {
    return Product(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      categoryId: data.categoryId.present
          ? data.categoryId.value
          : this.categoryId,
      categoryName: data.categoryName.present
          ? data.categoryName.value
          : this.categoryName,
      priceCents: data.priceCents.present
          ? data.priceCents.value
          : this.priceCents,
      active: data.active.present ? data.active.value : this.active,
      schoolId: data.schoolId.present ? data.schoolId.value : this.schoolId,
      merchantId: data.merchantId.present
          ? data.merchantId.value
          : this.merchantId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Product(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('categoryId: $categoryId, ')
          ..write('categoryName: $categoryName, ')
          ..write('priceCents: $priceCents, ')
          ..write('active: $active, ')
          ..write('schoolId: $schoolId, ')
          ..write('merchantId: $merchantId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    name,
    categoryId,
    categoryName,
    priceCents,
    active,
    schoolId,
    merchantId,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Product &&
          other.id == this.id &&
          other.name == this.name &&
          other.categoryId == this.categoryId &&
          other.categoryName == this.categoryName &&
          other.priceCents == this.priceCents &&
          other.active == this.active &&
          other.schoolId == this.schoolId &&
          other.merchantId == this.merchantId);
}

class ProductsCompanion extends UpdateCompanion<Product> {
  final Value<int> id;
  final Value<String> name;
  final Value<int> categoryId;
  final Value<String> categoryName;
  final Value<int> priceCents;
  final Value<bool> active;
  final Value<int> schoolId;
  final Value<int?> merchantId;
  const ProductsCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.categoryId = const Value.absent(),
    this.categoryName = const Value.absent(),
    this.priceCents = const Value.absent(),
    this.active = const Value.absent(),
    this.schoolId = const Value.absent(),
    this.merchantId = const Value.absent(),
  });
  ProductsCompanion.insert({
    this.id = const Value.absent(),
    required String name,
    required int categoryId,
    required String categoryName,
    required int priceCents,
    required bool active,
    required int schoolId,
    this.merchantId = const Value.absent(),
  }) : name = Value(name),
       categoryId = Value(categoryId),
       categoryName = Value(categoryName),
       priceCents = Value(priceCents),
       active = Value(active),
       schoolId = Value(schoolId);
  static Insertable<Product> custom({
    Expression<int>? id,
    Expression<String>? name,
    Expression<int>? categoryId,
    Expression<String>? categoryName,
    Expression<int>? priceCents,
    Expression<bool>? active,
    Expression<int>? schoolId,
    Expression<int>? merchantId,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (categoryId != null) 'category_id': categoryId,
      if (categoryName != null) 'category_name': categoryName,
      if (priceCents != null) 'price_cents': priceCents,
      if (active != null) 'active': active,
      if (schoolId != null) 'school_id': schoolId,
      if (merchantId != null) 'merchant_id': merchantId,
    });
  }

  ProductsCompanion copyWith({
    Value<int>? id,
    Value<String>? name,
    Value<int>? categoryId,
    Value<String>? categoryName,
    Value<int>? priceCents,
    Value<bool>? active,
    Value<int>? schoolId,
    Value<int?>? merchantId,
  }) {
    return ProductsCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      categoryId: categoryId ?? this.categoryId,
      categoryName: categoryName ?? this.categoryName,
      priceCents: priceCents ?? this.priceCents,
      active: active ?? this.active,
      schoolId: schoolId ?? this.schoolId,
      merchantId: merchantId ?? this.merchantId,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (categoryId.present) {
      map['category_id'] = Variable<int>(categoryId.value);
    }
    if (categoryName.present) {
      map['category_name'] = Variable<String>(categoryName.value);
    }
    if (priceCents.present) {
      map['price_cents'] = Variable<int>(priceCents.value);
    }
    if (active.present) {
      map['active'] = Variable<bool>(active.value);
    }
    if (schoolId.present) {
      map['school_id'] = Variable<int>(schoolId.value);
    }
    if (merchantId.present) {
      map['merchant_id'] = Variable<int>(merchantId.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ProductsCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('categoryId: $categoryId, ')
          ..write('categoryName: $categoryName, ')
          ..write('priceCents: $priceCents, ')
          ..write('active: $active, ')
          ..write('schoolId: $schoolId, ')
          ..write('merchantId: $merchantId')
          ..write(')'))
        .toString();
  }
}

class $CategoriesTable extends Categories
    with TableInfo<$CategoriesTable, Category> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CategoriesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isUnhealthyMeta = const VerificationMeta(
    'isUnhealthy',
  );
  @override
  late final GeneratedColumn<bool> isUnhealthy = GeneratedColumn<bool>(
    'is_unhealthy',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_unhealthy" IN (0, 1))',
    ),
  );
  static const VerificationMeta _activeMeta = const VerificationMeta('active');
  @override
  late final GeneratedColumn<bool> active = GeneratedColumn<bool>(
    'active',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("active" IN (0, 1))',
    ),
  );
  static const VerificationMeta _schoolIdMeta = const VerificationMeta(
    'schoolId',
  );
  @override
  late final GeneratedColumn<int> schoolId = GeneratedColumn<int>(
    'school_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    name,
    isUnhealthy,
    active,
    schoolId,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'categories';
  @override
  VerificationContext validateIntegrity(
    Insertable<Category> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('is_unhealthy')) {
      context.handle(
        _isUnhealthyMeta,
        isUnhealthy.isAcceptableOrUnknown(
          data['is_unhealthy']!,
          _isUnhealthyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_isUnhealthyMeta);
    }
    if (data.containsKey('active')) {
      context.handle(
        _activeMeta,
        active.isAcceptableOrUnknown(data['active']!, _activeMeta),
      );
    } else if (isInserting) {
      context.missing(_activeMeta);
    }
    if (data.containsKey('school_id')) {
      context.handle(
        _schoolIdMeta,
        schoolId.isAcceptableOrUnknown(data['school_id']!, _schoolIdMeta),
      );
    } else if (isInserting) {
      context.missing(_schoolIdMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Category map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Category(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      isUnhealthy: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_unhealthy'],
      )!,
      active: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}active'],
      )!,
      schoolId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}school_id'],
      )!,
    );
  }

  @override
  $CategoriesTable createAlias(String alias) {
    return $CategoriesTable(attachedDatabase, alias);
  }
}

class Category extends DataClass implements Insertable<Category> {
  final int id;
  final String name;
  final bool isUnhealthy;
  final bool active;
  final int schoolId;
  const Category({
    required this.id,
    required this.name,
    required this.isUnhealthy,
    required this.active,
    required this.schoolId,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['name'] = Variable<String>(name);
    map['is_unhealthy'] = Variable<bool>(isUnhealthy);
    map['active'] = Variable<bool>(active);
    map['school_id'] = Variable<int>(schoolId);
    return map;
  }

  CategoriesCompanion toCompanion(bool nullToAbsent) {
    return CategoriesCompanion(
      id: Value(id),
      name: Value(name),
      isUnhealthy: Value(isUnhealthy),
      active: Value(active),
      schoolId: Value(schoolId),
    );
  }

  factory Category.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Category(
      id: serializer.fromJson<int>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      isUnhealthy: serializer.fromJson<bool>(json['isUnhealthy']),
      active: serializer.fromJson<bool>(json['active']),
      schoolId: serializer.fromJson<int>(json['schoolId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'name': serializer.toJson<String>(name),
      'isUnhealthy': serializer.toJson<bool>(isUnhealthy),
      'active': serializer.toJson<bool>(active),
      'schoolId': serializer.toJson<int>(schoolId),
    };
  }

  Category copyWith({
    int? id,
    String? name,
    bool? isUnhealthy,
    bool? active,
    int? schoolId,
  }) => Category(
    id: id ?? this.id,
    name: name ?? this.name,
    isUnhealthy: isUnhealthy ?? this.isUnhealthy,
    active: active ?? this.active,
    schoolId: schoolId ?? this.schoolId,
  );
  Category copyWithCompanion(CategoriesCompanion data) {
    return Category(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      isUnhealthy: data.isUnhealthy.present
          ? data.isUnhealthy.value
          : this.isUnhealthy,
      active: data.active.present ? data.active.value : this.active,
      schoolId: data.schoolId.present ? data.schoolId.value : this.schoolId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Category(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('isUnhealthy: $isUnhealthy, ')
          ..write('active: $active, ')
          ..write('schoolId: $schoolId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, name, isUnhealthy, active, schoolId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Category &&
          other.id == this.id &&
          other.name == this.name &&
          other.isUnhealthy == this.isUnhealthy &&
          other.active == this.active &&
          other.schoolId == this.schoolId);
}

class CategoriesCompanion extends UpdateCompanion<Category> {
  final Value<int> id;
  final Value<String> name;
  final Value<bool> isUnhealthy;
  final Value<bool> active;
  final Value<int> schoolId;
  const CategoriesCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.isUnhealthy = const Value.absent(),
    this.active = const Value.absent(),
    this.schoolId = const Value.absent(),
  });
  CategoriesCompanion.insert({
    this.id = const Value.absent(),
    required String name,
    required bool isUnhealthy,
    required bool active,
    required int schoolId,
  }) : name = Value(name),
       isUnhealthy = Value(isUnhealthy),
       active = Value(active),
       schoolId = Value(schoolId);
  static Insertable<Category> custom({
    Expression<int>? id,
    Expression<String>? name,
    Expression<bool>? isUnhealthy,
    Expression<bool>? active,
    Expression<int>? schoolId,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (isUnhealthy != null) 'is_unhealthy': isUnhealthy,
      if (active != null) 'active': active,
      if (schoolId != null) 'school_id': schoolId,
    });
  }

  CategoriesCompanion copyWith({
    Value<int>? id,
    Value<String>? name,
    Value<bool>? isUnhealthy,
    Value<bool>? active,
    Value<int>? schoolId,
  }) {
    return CategoriesCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      isUnhealthy: isUnhealthy ?? this.isUnhealthy,
      active: active ?? this.active,
      schoolId: schoolId ?? this.schoolId,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (isUnhealthy.present) {
      map['is_unhealthy'] = Variable<bool>(isUnhealthy.value);
    }
    if (active.present) {
      map['active'] = Variable<bool>(active.value);
    }
    if (schoolId.present) {
      map['school_id'] = Variable<int>(schoolId.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CategoriesCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('isUnhealthy: $isUnhealthy, ')
          ..write('active: $active, ')
          ..write('schoolId: $schoolId')
          ..write(')'))
        .toString();
  }
}

class $RosterCardsTable extends RosterCards
    with TableInfo<$RosterCardsTable, RosterCard> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RosterCardsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _cardUidMeta = const VerificationMeta(
    'cardUid',
  );
  @override
  late final GeneratedColumn<String> cardUid = GeneratedColumn<String>(
    'card_uid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _studentIdMeta = const VerificationMeta(
    'studentId',
  );
  @override
  late final GeneratedColumn<int> studentId = GeneratedColumn<int>(
    'student_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _displayNameMeta = const VerificationMeta(
    'displayName',
  );
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
    'display_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _classNameMeta = const VerificationMeta(
    'className',
  );
  @override
  late final GeneratedColumn<String> className = GeneratedColumn<String>(
    'class_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _photoUrlMeta = const VerificationMeta(
    'photoUrl',
  );
  @override
  late final GeneratedColumn<String> photoUrl = GeneratedColumn<String>(
    'photo_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    cardUid,
    status,
    studentId,
    displayName,
    className,
    photoUrl,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'roster_cards';
  @override
  VerificationContext validateIntegrity(
    Insertable<RosterCard> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('card_uid')) {
      context.handle(
        _cardUidMeta,
        cardUid.isAcceptableOrUnknown(data['card_uid']!, _cardUidMeta),
      );
    } else if (isInserting) {
      context.missing(_cardUidMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('student_id')) {
      context.handle(
        _studentIdMeta,
        studentId.isAcceptableOrUnknown(data['student_id']!, _studentIdMeta),
      );
    } else if (isInserting) {
      context.missing(_studentIdMeta);
    }
    if (data.containsKey('display_name')) {
      context.handle(
        _displayNameMeta,
        displayName.isAcceptableOrUnknown(
          data['display_name']!,
          _displayNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_displayNameMeta);
    }
    if (data.containsKey('class_name')) {
      context.handle(
        _classNameMeta,
        className.isAcceptableOrUnknown(data['class_name']!, _classNameMeta),
      );
    } else if (isInserting) {
      context.missing(_classNameMeta);
    }
    if (data.containsKey('photo_url')) {
      context.handle(
        _photoUrlMeta,
        photoUrl.isAcceptableOrUnknown(data['photo_url']!, _photoUrlMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {cardUid};
  @override
  RosterCard map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return RosterCard(
      cardUid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}card_uid'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      studentId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}student_id'],
      )!,
      displayName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}display_name'],
      )!,
      className: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}class_name'],
      )!,
      photoUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}photo_url'],
      ),
    );
  }

  @override
  $RosterCardsTable createAlias(String alias) {
    return $RosterCardsTable(attachedDatabase, alias);
  }
}

class RosterCard extends DataClass implements Insertable<RosterCard> {
  final String cardUid;
  final String status;
  final int studentId;
  final String displayName;
  final String className;
  final String? photoUrl;
  const RosterCard({
    required this.cardUid,
    required this.status,
    required this.studentId,
    required this.displayName,
    required this.className,
    this.photoUrl,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['card_uid'] = Variable<String>(cardUid);
    map['status'] = Variable<String>(status);
    map['student_id'] = Variable<int>(studentId);
    map['display_name'] = Variable<String>(displayName);
    map['class_name'] = Variable<String>(className);
    if (!nullToAbsent || photoUrl != null) {
      map['photo_url'] = Variable<String>(photoUrl);
    }
    return map;
  }

  RosterCardsCompanion toCompanion(bool nullToAbsent) {
    return RosterCardsCompanion(
      cardUid: Value(cardUid),
      status: Value(status),
      studentId: Value(studentId),
      displayName: Value(displayName),
      className: Value(className),
      photoUrl: photoUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(photoUrl),
    );
  }

  factory RosterCard.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return RosterCard(
      cardUid: serializer.fromJson<String>(json['cardUid']),
      status: serializer.fromJson<String>(json['status']),
      studentId: serializer.fromJson<int>(json['studentId']),
      displayName: serializer.fromJson<String>(json['displayName']),
      className: serializer.fromJson<String>(json['className']),
      photoUrl: serializer.fromJson<String?>(json['photoUrl']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'cardUid': serializer.toJson<String>(cardUid),
      'status': serializer.toJson<String>(status),
      'studentId': serializer.toJson<int>(studentId),
      'displayName': serializer.toJson<String>(displayName),
      'className': serializer.toJson<String>(className),
      'photoUrl': serializer.toJson<String?>(photoUrl),
    };
  }

  RosterCard copyWith({
    String? cardUid,
    String? status,
    int? studentId,
    String? displayName,
    String? className,
    Value<String?> photoUrl = const Value.absent(),
  }) => RosterCard(
    cardUid: cardUid ?? this.cardUid,
    status: status ?? this.status,
    studentId: studentId ?? this.studentId,
    displayName: displayName ?? this.displayName,
    className: className ?? this.className,
    photoUrl: photoUrl.present ? photoUrl.value : this.photoUrl,
  );
  RosterCard copyWithCompanion(RosterCardsCompanion data) {
    return RosterCard(
      cardUid: data.cardUid.present ? data.cardUid.value : this.cardUid,
      status: data.status.present ? data.status.value : this.status,
      studentId: data.studentId.present ? data.studentId.value : this.studentId,
      displayName: data.displayName.present
          ? data.displayName.value
          : this.displayName,
      className: data.className.present ? data.className.value : this.className,
      photoUrl: data.photoUrl.present ? data.photoUrl.value : this.photoUrl,
    );
  }

  @override
  String toString() {
    return (StringBuffer('RosterCard(')
          ..write('cardUid: $cardUid, ')
          ..write('status: $status, ')
          ..write('studentId: $studentId, ')
          ..write('displayName: $displayName, ')
          ..write('className: $className, ')
          ..write('photoUrl: $photoUrl')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(cardUid, status, studentId, displayName, className, photoUrl);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is RosterCard &&
          other.cardUid == this.cardUid &&
          other.status == this.status &&
          other.studentId == this.studentId &&
          other.displayName == this.displayName &&
          other.className == this.className &&
          other.photoUrl == this.photoUrl);
}

class RosterCardsCompanion extends UpdateCompanion<RosterCard> {
  final Value<String> cardUid;
  final Value<String> status;
  final Value<int> studentId;
  final Value<String> displayName;
  final Value<String> className;
  final Value<String?> photoUrl;
  final Value<int> rowid;
  const RosterCardsCompanion({
    this.cardUid = const Value.absent(),
    this.status = const Value.absent(),
    this.studentId = const Value.absent(),
    this.displayName = const Value.absent(),
    this.className = const Value.absent(),
    this.photoUrl = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  RosterCardsCompanion.insert({
    required String cardUid,
    required String status,
    required int studentId,
    required String displayName,
    required String className,
    this.photoUrl = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : cardUid = Value(cardUid),
       status = Value(status),
       studentId = Value(studentId),
       displayName = Value(displayName),
       className = Value(className);
  static Insertable<RosterCard> custom({
    Expression<String>? cardUid,
    Expression<String>? status,
    Expression<int>? studentId,
    Expression<String>? displayName,
    Expression<String>? className,
    Expression<String>? photoUrl,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (cardUid != null) 'card_uid': cardUid,
      if (status != null) 'status': status,
      if (studentId != null) 'student_id': studentId,
      if (displayName != null) 'display_name': displayName,
      if (className != null) 'class_name': className,
      if (photoUrl != null) 'photo_url': photoUrl,
      if (rowid != null) 'rowid': rowid,
    });
  }

  RosterCardsCompanion copyWith({
    Value<String>? cardUid,
    Value<String>? status,
    Value<int>? studentId,
    Value<String>? displayName,
    Value<String>? className,
    Value<String?>? photoUrl,
    Value<int>? rowid,
  }) {
    return RosterCardsCompanion(
      cardUid: cardUid ?? this.cardUid,
      status: status ?? this.status,
      studentId: studentId ?? this.studentId,
      displayName: displayName ?? this.displayName,
      className: className ?? this.className,
      photoUrl: photoUrl ?? this.photoUrl,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (cardUid.present) {
      map['card_uid'] = Variable<String>(cardUid.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (studentId.present) {
      map['student_id'] = Variable<int>(studentId.value);
    }
    if (displayName.present) {
      map['display_name'] = Variable<String>(displayName.value);
    }
    if (className.present) {
      map['class_name'] = Variable<String>(className.value);
    }
    if (photoUrl.present) {
      map['photo_url'] = Variable<String>(photoUrl.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RosterCardsCompanion(')
          ..write('cardUid: $cardUid, ')
          ..write('status: $status, ')
          ..write('studentId: $studentId, ')
          ..write('displayName: $displayName, ')
          ..write('className: $className, ')
          ..write('photoUrl: $photoUrl, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SaleQueueTable extends SaleQueue
    with TableInfo<$SaleQueueTable, SaleQueueData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SaleQueueTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _idempotencyKeyMeta = const VerificationMeta(
    'idempotencyKey',
  );
  @override
  late final GeneratedColumn<String> idempotencyKey = GeneratedColumn<String>(
    'idempotency_key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'),
  );
  static const VerificationMeta _cardUidMeta = const VerificationMeta(
    'cardUid',
  );
  @override
  late final GeneratedColumn<String> cardUid = GeneratedColumn<String>(
    'card_uid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _studentNameMeta = const VerificationMeta(
    'studentName',
  );
  @override
  late final GeneratedColumn<String> studentName = GeneratedColumn<String>(
    'student_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _amountCentsMeta = const VerificationMeta(
    'amountCents',
  );
  @override
  late final GeneratedColumn<int> amountCents = GeneratedColumn<int>(
    'amount_cents',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _itemsJsonMeta = const VerificationMeta(
    'itemsJson',
  );
  @override
  late final GeneratedColumn<String> itemsJson = GeneratedColumn<String>(
    'items_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _deviceLocalTimestampMeta =
      const VerificationMeta('deviceLocalTimestamp');
  @override
  late final GeneratedColumn<String> deviceLocalTimestamp =
      GeneratedColumn<String>(
        'device_local_timestamp',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _kampalaDayMeta = const VerificationMeta(
    'kampalaDay',
  );
  @override
  late final GeneratedColumn<String> kampalaDay = GeneratedColumn<String>(
    'kampala_day',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _kampalaWeekMeta = const VerificationMeta(
    'kampalaWeek',
  );
  @override
  late final GeneratedColumn<String> kampalaWeek = GeneratedColumn<String>(
    'kampala_week',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _channelMeta = const VerificationMeta(
    'channel',
  );
  @override
  late final GeneratedColumn<String> channel = GeneratedColumn<String>(
    'channel',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _appliedCentsMeta = const VerificationMeta(
    'appliedCents',
  );
  @override
  late final GeneratedColumn<int> appliedCents = GeneratedColumn<int>(
    'applied_cents',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _shortfallCentsMeta = const VerificationMeta(
    'shortfallCents',
  );
  @override
  late final GeneratedColumn<int> shortfallCents = GeneratedColumn<int>(
    'shortfall_cents',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _flagsMeta = const VerificationMeta('flags');
  @override
  late final GeneratedColumn<String> flags = GeneratedColumn<String>(
    'flags',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _reasonMeta = const VerificationMeta('reason');
  @override
  late final GeneratedColumn<String> reason = GeneratedColumn<String>(
    'reason',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _serverTransactionIdMeta =
      const VerificationMeta('serverTransactionId');
  @override
  late final GeneratedColumn<int> serverTransactionId = GeneratedColumn<int>(
    'server_transaction_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _attemptsMeta = const VerificationMeta(
    'attempts',
  );
  @override
  late final GeneratedColumn<int> attempts = GeneratedColumn<int>(
    'attempts',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _syncedAtMeta = const VerificationMeta(
    'syncedAt',
  );
  @override
  late final GeneratedColumn<DateTime> syncedAt = GeneratedColumn<DateTime>(
    'synced_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    idempotencyKey,
    cardUid,
    studentName,
    amountCents,
    itemsJson,
    deviceLocalTimestamp,
    kampalaDay,
    kampalaWeek,
    createdAt,
    channel,
    status,
    appliedCents,
    shortfallCents,
    flags,
    reason,
    serverTransactionId,
    attempts,
    lastError,
    syncedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sale_queue';
  @override
  VerificationContext validateIntegrity(
    Insertable<SaleQueueData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('idempotency_key')) {
      context.handle(
        _idempotencyKeyMeta,
        idempotencyKey.isAcceptableOrUnknown(
          data['idempotency_key']!,
          _idempotencyKeyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_idempotencyKeyMeta);
    }
    if (data.containsKey('card_uid')) {
      context.handle(
        _cardUidMeta,
        cardUid.isAcceptableOrUnknown(data['card_uid']!, _cardUidMeta),
      );
    } else if (isInserting) {
      context.missing(_cardUidMeta);
    }
    if (data.containsKey('student_name')) {
      context.handle(
        _studentNameMeta,
        studentName.isAcceptableOrUnknown(
          data['student_name']!,
          _studentNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_studentNameMeta);
    }
    if (data.containsKey('amount_cents')) {
      context.handle(
        _amountCentsMeta,
        amountCents.isAcceptableOrUnknown(
          data['amount_cents']!,
          _amountCentsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_amountCentsMeta);
    }
    if (data.containsKey('items_json')) {
      context.handle(
        _itemsJsonMeta,
        itemsJson.isAcceptableOrUnknown(data['items_json']!, _itemsJsonMeta),
      );
    } else if (isInserting) {
      context.missing(_itemsJsonMeta);
    }
    if (data.containsKey('device_local_timestamp')) {
      context.handle(
        _deviceLocalTimestampMeta,
        deviceLocalTimestamp.isAcceptableOrUnknown(
          data['device_local_timestamp']!,
          _deviceLocalTimestampMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_deviceLocalTimestampMeta);
    }
    if (data.containsKey('kampala_day')) {
      context.handle(
        _kampalaDayMeta,
        kampalaDay.isAcceptableOrUnknown(data['kampala_day']!, _kampalaDayMeta),
      );
    } else if (isInserting) {
      context.missing(_kampalaDayMeta);
    }
    if (data.containsKey('kampala_week')) {
      context.handle(
        _kampalaWeekMeta,
        kampalaWeek.isAcceptableOrUnknown(
          data['kampala_week']!,
          _kampalaWeekMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_kampalaWeekMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('channel')) {
      context.handle(
        _channelMeta,
        channel.isAcceptableOrUnknown(data['channel']!, _channelMeta),
      );
    } else if (isInserting) {
      context.missing(_channelMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('applied_cents')) {
      context.handle(
        _appliedCentsMeta,
        appliedCents.isAcceptableOrUnknown(
          data['applied_cents']!,
          _appliedCentsMeta,
        ),
      );
    }
    if (data.containsKey('shortfall_cents')) {
      context.handle(
        _shortfallCentsMeta,
        shortfallCents.isAcceptableOrUnknown(
          data['shortfall_cents']!,
          _shortfallCentsMeta,
        ),
      );
    }
    if (data.containsKey('flags')) {
      context.handle(
        _flagsMeta,
        flags.isAcceptableOrUnknown(data['flags']!, _flagsMeta),
      );
    }
    if (data.containsKey('reason')) {
      context.handle(
        _reasonMeta,
        reason.isAcceptableOrUnknown(data['reason']!, _reasonMeta),
      );
    }
    if (data.containsKey('server_transaction_id')) {
      context.handle(
        _serverTransactionIdMeta,
        serverTransactionId.isAcceptableOrUnknown(
          data['server_transaction_id']!,
          _serverTransactionIdMeta,
        ),
      );
    }
    if (data.containsKey('attempts')) {
      context.handle(
        _attemptsMeta,
        attempts.isAcceptableOrUnknown(data['attempts']!, _attemptsMeta),
      );
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    if (data.containsKey('synced_at')) {
      context.handle(
        _syncedAtMeta,
        syncedAt.isAcceptableOrUnknown(data['synced_at']!, _syncedAtMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SaleQueueData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SaleQueueData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      idempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}idempotency_key'],
      )!,
      cardUid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}card_uid'],
      )!,
      studentName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}student_name'],
      )!,
      amountCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}amount_cents'],
      )!,
      itemsJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}items_json'],
      )!,
      deviceLocalTimestamp: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}device_local_timestamp'],
      )!,
      kampalaDay: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}kampala_day'],
      )!,
      kampalaWeek: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}kampala_week'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      channel: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}channel'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      appliedCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}applied_cents'],
      ),
      shortfallCents: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}shortfall_cents'],
      ),
      flags: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}flags'],
      )!,
      reason: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}reason'],
      ),
      serverTransactionId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}server_transaction_id'],
      ),
      attempts: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}attempts'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
      syncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}synced_at'],
      ),
    );
  }

  @override
  $SaleQueueTable createAlias(String alias) {
    return $SaleQueueTable(attachedDatabase, alias);
  }
}

class SaleQueueData extends DataClass implements Insertable<SaleQueueData> {
  final int id;
  final String idempotencyKey;
  final String cardUid;
  final String studentName;
  final int amountCents;
  final String itemsJson;
  final String deviceLocalTimestamp;
  final String kampalaDay;
  final String kampalaWeek;
  final DateTime createdAt;
  final String channel;
  final String status;
  final int? appliedCents;
  final int? shortfallCents;
  final String flags;
  final String? reason;
  final int? serverTransactionId;
  final int attempts;
  final String? lastError;
  final DateTime? syncedAt;
  const SaleQueueData({
    required this.id,
    required this.idempotencyKey,
    required this.cardUid,
    required this.studentName,
    required this.amountCents,
    required this.itemsJson,
    required this.deviceLocalTimestamp,
    required this.kampalaDay,
    required this.kampalaWeek,
    required this.createdAt,
    required this.channel,
    required this.status,
    this.appliedCents,
    this.shortfallCents,
    required this.flags,
    this.reason,
    this.serverTransactionId,
    required this.attempts,
    this.lastError,
    this.syncedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['idempotency_key'] = Variable<String>(idempotencyKey);
    map['card_uid'] = Variable<String>(cardUid);
    map['student_name'] = Variable<String>(studentName);
    map['amount_cents'] = Variable<int>(amountCents);
    map['items_json'] = Variable<String>(itemsJson);
    map['device_local_timestamp'] = Variable<String>(deviceLocalTimestamp);
    map['kampala_day'] = Variable<String>(kampalaDay);
    map['kampala_week'] = Variable<String>(kampalaWeek);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['channel'] = Variable<String>(channel);
    map['status'] = Variable<String>(status);
    if (!nullToAbsent || appliedCents != null) {
      map['applied_cents'] = Variable<int>(appliedCents);
    }
    if (!nullToAbsent || shortfallCents != null) {
      map['shortfall_cents'] = Variable<int>(shortfallCents);
    }
    map['flags'] = Variable<String>(flags);
    if (!nullToAbsent || reason != null) {
      map['reason'] = Variable<String>(reason);
    }
    if (!nullToAbsent || serverTransactionId != null) {
      map['server_transaction_id'] = Variable<int>(serverTransactionId);
    }
    map['attempts'] = Variable<int>(attempts);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    if (!nullToAbsent || syncedAt != null) {
      map['synced_at'] = Variable<DateTime>(syncedAt);
    }
    return map;
  }

  SaleQueueCompanion toCompanion(bool nullToAbsent) {
    return SaleQueueCompanion(
      id: Value(id),
      idempotencyKey: Value(idempotencyKey),
      cardUid: Value(cardUid),
      studentName: Value(studentName),
      amountCents: Value(amountCents),
      itemsJson: Value(itemsJson),
      deviceLocalTimestamp: Value(deviceLocalTimestamp),
      kampalaDay: Value(kampalaDay),
      kampalaWeek: Value(kampalaWeek),
      createdAt: Value(createdAt),
      channel: Value(channel),
      status: Value(status),
      appliedCents: appliedCents == null && nullToAbsent
          ? const Value.absent()
          : Value(appliedCents),
      shortfallCents: shortfallCents == null && nullToAbsent
          ? const Value.absent()
          : Value(shortfallCents),
      flags: Value(flags),
      reason: reason == null && nullToAbsent
          ? const Value.absent()
          : Value(reason),
      serverTransactionId: serverTransactionId == null && nullToAbsent
          ? const Value.absent()
          : Value(serverTransactionId),
      attempts: Value(attempts),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
      syncedAt: syncedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(syncedAt),
    );
  }

  factory SaleQueueData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SaleQueueData(
      id: serializer.fromJson<int>(json['id']),
      idempotencyKey: serializer.fromJson<String>(json['idempotencyKey']),
      cardUid: serializer.fromJson<String>(json['cardUid']),
      studentName: serializer.fromJson<String>(json['studentName']),
      amountCents: serializer.fromJson<int>(json['amountCents']),
      itemsJson: serializer.fromJson<String>(json['itemsJson']),
      deviceLocalTimestamp: serializer.fromJson<String>(
        json['deviceLocalTimestamp'],
      ),
      kampalaDay: serializer.fromJson<String>(json['kampalaDay']),
      kampalaWeek: serializer.fromJson<String>(json['kampalaWeek']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      channel: serializer.fromJson<String>(json['channel']),
      status: serializer.fromJson<String>(json['status']),
      appliedCents: serializer.fromJson<int?>(json['appliedCents']),
      shortfallCents: serializer.fromJson<int?>(json['shortfallCents']),
      flags: serializer.fromJson<String>(json['flags']),
      reason: serializer.fromJson<String?>(json['reason']),
      serverTransactionId: serializer.fromJson<int?>(
        json['serverTransactionId'],
      ),
      attempts: serializer.fromJson<int>(json['attempts']),
      lastError: serializer.fromJson<String?>(json['lastError']),
      syncedAt: serializer.fromJson<DateTime?>(json['syncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'idempotencyKey': serializer.toJson<String>(idempotencyKey),
      'cardUid': serializer.toJson<String>(cardUid),
      'studentName': serializer.toJson<String>(studentName),
      'amountCents': serializer.toJson<int>(amountCents),
      'itemsJson': serializer.toJson<String>(itemsJson),
      'deviceLocalTimestamp': serializer.toJson<String>(deviceLocalTimestamp),
      'kampalaDay': serializer.toJson<String>(kampalaDay),
      'kampalaWeek': serializer.toJson<String>(kampalaWeek),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'channel': serializer.toJson<String>(channel),
      'status': serializer.toJson<String>(status),
      'appliedCents': serializer.toJson<int?>(appliedCents),
      'shortfallCents': serializer.toJson<int?>(shortfallCents),
      'flags': serializer.toJson<String>(flags),
      'reason': serializer.toJson<String?>(reason),
      'serverTransactionId': serializer.toJson<int?>(serverTransactionId),
      'attempts': serializer.toJson<int>(attempts),
      'lastError': serializer.toJson<String?>(lastError),
      'syncedAt': serializer.toJson<DateTime?>(syncedAt),
    };
  }

  SaleQueueData copyWith({
    int? id,
    String? idempotencyKey,
    String? cardUid,
    String? studentName,
    int? amountCents,
    String? itemsJson,
    String? deviceLocalTimestamp,
    String? kampalaDay,
    String? kampalaWeek,
    DateTime? createdAt,
    String? channel,
    String? status,
    Value<int?> appliedCents = const Value.absent(),
    Value<int?> shortfallCents = const Value.absent(),
    String? flags,
    Value<String?> reason = const Value.absent(),
    Value<int?> serverTransactionId = const Value.absent(),
    int? attempts,
    Value<String?> lastError = const Value.absent(),
    Value<DateTime?> syncedAt = const Value.absent(),
  }) => SaleQueueData(
    id: id ?? this.id,
    idempotencyKey: idempotencyKey ?? this.idempotencyKey,
    cardUid: cardUid ?? this.cardUid,
    studentName: studentName ?? this.studentName,
    amountCents: amountCents ?? this.amountCents,
    itemsJson: itemsJson ?? this.itemsJson,
    deviceLocalTimestamp: deviceLocalTimestamp ?? this.deviceLocalTimestamp,
    kampalaDay: kampalaDay ?? this.kampalaDay,
    kampalaWeek: kampalaWeek ?? this.kampalaWeek,
    createdAt: createdAt ?? this.createdAt,
    channel: channel ?? this.channel,
    status: status ?? this.status,
    appliedCents: appliedCents.present ? appliedCents.value : this.appliedCents,
    shortfallCents: shortfallCents.present
        ? shortfallCents.value
        : this.shortfallCents,
    flags: flags ?? this.flags,
    reason: reason.present ? reason.value : this.reason,
    serverTransactionId: serverTransactionId.present
        ? serverTransactionId.value
        : this.serverTransactionId,
    attempts: attempts ?? this.attempts,
    lastError: lastError.present ? lastError.value : this.lastError,
    syncedAt: syncedAt.present ? syncedAt.value : this.syncedAt,
  );
  SaleQueueData copyWithCompanion(SaleQueueCompanion data) {
    return SaleQueueData(
      id: data.id.present ? data.id.value : this.id,
      idempotencyKey: data.idempotencyKey.present
          ? data.idempotencyKey.value
          : this.idempotencyKey,
      cardUid: data.cardUid.present ? data.cardUid.value : this.cardUid,
      studentName: data.studentName.present
          ? data.studentName.value
          : this.studentName,
      amountCents: data.amountCents.present
          ? data.amountCents.value
          : this.amountCents,
      itemsJson: data.itemsJson.present ? data.itemsJson.value : this.itemsJson,
      deviceLocalTimestamp: data.deviceLocalTimestamp.present
          ? data.deviceLocalTimestamp.value
          : this.deviceLocalTimestamp,
      kampalaDay: data.kampalaDay.present
          ? data.kampalaDay.value
          : this.kampalaDay,
      kampalaWeek: data.kampalaWeek.present
          ? data.kampalaWeek.value
          : this.kampalaWeek,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      channel: data.channel.present ? data.channel.value : this.channel,
      status: data.status.present ? data.status.value : this.status,
      appliedCents: data.appliedCents.present
          ? data.appliedCents.value
          : this.appliedCents,
      shortfallCents: data.shortfallCents.present
          ? data.shortfallCents.value
          : this.shortfallCents,
      flags: data.flags.present ? data.flags.value : this.flags,
      reason: data.reason.present ? data.reason.value : this.reason,
      serverTransactionId: data.serverTransactionId.present
          ? data.serverTransactionId.value
          : this.serverTransactionId,
      attempts: data.attempts.present ? data.attempts.value : this.attempts,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
      syncedAt: data.syncedAt.present ? data.syncedAt.value : this.syncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SaleQueueData(')
          ..write('id: $id, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('cardUid: $cardUid, ')
          ..write('studentName: $studentName, ')
          ..write('amountCents: $amountCents, ')
          ..write('itemsJson: $itemsJson, ')
          ..write('deviceLocalTimestamp: $deviceLocalTimestamp, ')
          ..write('kampalaDay: $kampalaDay, ')
          ..write('kampalaWeek: $kampalaWeek, ')
          ..write('createdAt: $createdAt, ')
          ..write('channel: $channel, ')
          ..write('status: $status, ')
          ..write('appliedCents: $appliedCents, ')
          ..write('shortfallCents: $shortfallCents, ')
          ..write('flags: $flags, ')
          ..write('reason: $reason, ')
          ..write('serverTransactionId: $serverTransactionId, ')
          ..write('attempts: $attempts, ')
          ..write('lastError: $lastError, ')
          ..write('syncedAt: $syncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    idempotencyKey,
    cardUid,
    studentName,
    amountCents,
    itemsJson,
    deviceLocalTimestamp,
    kampalaDay,
    kampalaWeek,
    createdAt,
    channel,
    status,
    appliedCents,
    shortfallCents,
    flags,
    reason,
    serverTransactionId,
    attempts,
    lastError,
    syncedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SaleQueueData &&
          other.id == this.id &&
          other.idempotencyKey == this.idempotencyKey &&
          other.cardUid == this.cardUid &&
          other.studentName == this.studentName &&
          other.amountCents == this.amountCents &&
          other.itemsJson == this.itemsJson &&
          other.deviceLocalTimestamp == this.deviceLocalTimestamp &&
          other.kampalaDay == this.kampalaDay &&
          other.kampalaWeek == this.kampalaWeek &&
          other.createdAt == this.createdAt &&
          other.channel == this.channel &&
          other.status == this.status &&
          other.appliedCents == this.appliedCents &&
          other.shortfallCents == this.shortfallCents &&
          other.flags == this.flags &&
          other.reason == this.reason &&
          other.serverTransactionId == this.serverTransactionId &&
          other.attempts == this.attempts &&
          other.lastError == this.lastError &&
          other.syncedAt == this.syncedAt);
}

class SaleQueueCompanion extends UpdateCompanion<SaleQueueData> {
  final Value<int> id;
  final Value<String> idempotencyKey;
  final Value<String> cardUid;
  final Value<String> studentName;
  final Value<int> amountCents;
  final Value<String> itemsJson;
  final Value<String> deviceLocalTimestamp;
  final Value<String> kampalaDay;
  final Value<String> kampalaWeek;
  final Value<DateTime> createdAt;
  final Value<String> channel;
  final Value<String> status;
  final Value<int?> appliedCents;
  final Value<int?> shortfallCents;
  final Value<String> flags;
  final Value<String?> reason;
  final Value<int?> serverTransactionId;
  final Value<int> attempts;
  final Value<String?> lastError;
  final Value<DateTime?> syncedAt;
  const SaleQueueCompanion({
    this.id = const Value.absent(),
    this.idempotencyKey = const Value.absent(),
    this.cardUid = const Value.absent(),
    this.studentName = const Value.absent(),
    this.amountCents = const Value.absent(),
    this.itemsJson = const Value.absent(),
    this.deviceLocalTimestamp = const Value.absent(),
    this.kampalaDay = const Value.absent(),
    this.kampalaWeek = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.channel = const Value.absent(),
    this.status = const Value.absent(),
    this.appliedCents = const Value.absent(),
    this.shortfallCents = const Value.absent(),
    this.flags = const Value.absent(),
    this.reason = const Value.absent(),
    this.serverTransactionId = const Value.absent(),
    this.attempts = const Value.absent(),
    this.lastError = const Value.absent(),
    this.syncedAt = const Value.absent(),
  });
  SaleQueueCompanion.insert({
    this.id = const Value.absent(),
    required String idempotencyKey,
    required String cardUid,
    required String studentName,
    required int amountCents,
    required String itemsJson,
    required String deviceLocalTimestamp,
    required String kampalaDay,
    required String kampalaWeek,
    required DateTime createdAt,
    required String channel,
    required String status,
    this.appliedCents = const Value.absent(),
    this.shortfallCents = const Value.absent(),
    this.flags = const Value.absent(),
    this.reason = const Value.absent(),
    this.serverTransactionId = const Value.absent(),
    this.attempts = const Value.absent(),
    this.lastError = const Value.absent(),
    this.syncedAt = const Value.absent(),
  }) : idempotencyKey = Value(idempotencyKey),
       cardUid = Value(cardUid),
       studentName = Value(studentName),
       amountCents = Value(amountCents),
       itemsJson = Value(itemsJson),
       deviceLocalTimestamp = Value(deviceLocalTimestamp),
       kampalaDay = Value(kampalaDay),
       kampalaWeek = Value(kampalaWeek),
       createdAt = Value(createdAt),
       channel = Value(channel),
       status = Value(status);
  static Insertable<SaleQueueData> custom({
    Expression<int>? id,
    Expression<String>? idempotencyKey,
    Expression<String>? cardUid,
    Expression<String>? studentName,
    Expression<int>? amountCents,
    Expression<String>? itemsJson,
    Expression<String>? deviceLocalTimestamp,
    Expression<String>? kampalaDay,
    Expression<String>? kampalaWeek,
    Expression<DateTime>? createdAt,
    Expression<String>? channel,
    Expression<String>? status,
    Expression<int>? appliedCents,
    Expression<int>? shortfallCents,
    Expression<String>? flags,
    Expression<String>? reason,
    Expression<int>? serverTransactionId,
    Expression<int>? attempts,
    Expression<String>? lastError,
    Expression<DateTime>? syncedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
      if (cardUid != null) 'card_uid': cardUid,
      if (studentName != null) 'student_name': studentName,
      if (amountCents != null) 'amount_cents': amountCents,
      if (itemsJson != null) 'items_json': itemsJson,
      if (deviceLocalTimestamp != null)
        'device_local_timestamp': deviceLocalTimestamp,
      if (kampalaDay != null) 'kampala_day': kampalaDay,
      if (kampalaWeek != null) 'kampala_week': kampalaWeek,
      if (createdAt != null) 'created_at': createdAt,
      if (channel != null) 'channel': channel,
      if (status != null) 'status': status,
      if (appliedCents != null) 'applied_cents': appliedCents,
      if (shortfallCents != null) 'shortfall_cents': shortfallCents,
      if (flags != null) 'flags': flags,
      if (reason != null) 'reason': reason,
      if (serverTransactionId != null)
        'server_transaction_id': serverTransactionId,
      if (attempts != null) 'attempts': attempts,
      if (lastError != null) 'last_error': lastError,
      if (syncedAt != null) 'synced_at': syncedAt,
    });
  }

  SaleQueueCompanion copyWith({
    Value<int>? id,
    Value<String>? idempotencyKey,
    Value<String>? cardUid,
    Value<String>? studentName,
    Value<int>? amountCents,
    Value<String>? itemsJson,
    Value<String>? deviceLocalTimestamp,
    Value<String>? kampalaDay,
    Value<String>? kampalaWeek,
    Value<DateTime>? createdAt,
    Value<String>? channel,
    Value<String>? status,
    Value<int?>? appliedCents,
    Value<int?>? shortfallCents,
    Value<String>? flags,
    Value<String?>? reason,
    Value<int?>? serverTransactionId,
    Value<int>? attempts,
    Value<String?>? lastError,
    Value<DateTime?>? syncedAt,
  }) {
    return SaleQueueCompanion(
      id: id ?? this.id,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      cardUid: cardUid ?? this.cardUid,
      studentName: studentName ?? this.studentName,
      amountCents: amountCents ?? this.amountCents,
      itemsJson: itemsJson ?? this.itemsJson,
      deviceLocalTimestamp: deviceLocalTimestamp ?? this.deviceLocalTimestamp,
      kampalaDay: kampalaDay ?? this.kampalaDay,
      kampalaWeek: kampalaWeek ?? this.kampalaWeek,
      createdAt: createdAt ?? this.createdAt,
      channel: channel ?? this.channel,
      status: status ?? this.status,
      appliedCents: appliedCents ?? this.appliedCents,
      shortfallCents: shortfallCents ?? this.shortfallCents,
      flags: flags ?? this.flags,
      reason: reason ?? this.reason,
      serverTransactionId: serverTransactionId ?? this.serverTransactionId,
      attempts: attempts ?? this.attempts,
      lastError: lastError ?? this.lastError,
      syncedAt: syncedAt ?? this.syncedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (idempotencyKey.present) {
      map['idempotency_key'] = Variable<String>(idempotencyKey.value);
    }
    if (cardUid.present) {
      map['card_uid'] = Variable<String>(cardUid.value);
    }
    if (studentName.present) {
      map['student_name'] = Variable<String>(studentName.value);
    }
    if (amountCents.present) {
      map['amount_cents'] = Variable<int>(amountCents.value);
    }
    if (itemsJson.present) {
      map['items_json'] = Variable<String>(itemsJson.value);
    }
    if (deviceLocalTimestamp.present) {
      map['device_local_timestamp'] = Variable<String>(
        deviceLocalTimestamp.value,
      );
    }
    if (kampalaDay.present) {
      map['kampala_day'] = Variable<String>(kampalaDay.value);
    }
    if (kampalaWeek.present) {
      map['kampala_week'] = Variable<String>(kampalaWeek.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (channel.present) {
      map['channel'] = Variable<String>(channel.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (appliedCents.present) {
      map['applied_cents'] = Variable<int>(appliedCents.value);
    }
    if (shortfallCents.present) {
      map['shortfall_cents'] = Variable<int>(shortfallCents.value);
    }
    if (flags.present) {
      map['flags'] = Variable<String>(flags.value);
    }
    if (reason.present) {
      map['reason'] = Variable<String>(reason.value);
    }
    if (serverTransactionId.present) {
      map['server_transaction_id'] = Variable<int>(serverTransactionId.value);
    }
    if (attempts.present) {
      map['attempts'] = Variable<int>(attempts.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    if (syncedAt.present) {
      map['synced_at'] = Variable<DateTime>(syncedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SaleQueueCompanion(')
          ..write('id: $id, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('cardUid: $cardUid, ')
          ..write('studentName: $studentName, ')
          ..write('amountCents: $amountCents, ')
          ..write('itemsJson: $itemsJson, ')
          ..write('deviceLocalTimestamp: $deviceLocalTimestamp, ')
          ..write('kampalaDay: $kampalaDay, ')
          ..write('kampalaWeek: $kampalaWeek, ')
          ..write('createdAt: $createdAt, ')
          ..write('channel: $channel, ')
          ..write('status: $status, ')
          ..write('appliedCents: $appliedCents, ')
          ..write('shortfallCents: $shortfallCents, ')
          ..write('flags: $flags, ')
          ..write('reason: $reason, ')
          ..write('serverTransactionId: $serverTransactionId, ')
          ..write('attempts: $attempts, ')
          ..write('lastError: $lastError, ')
          ..write('syncedAt: $syncedAt')
          ..write(')'))
        .toString();
  }
}

class $AttendanceQueueTable extends AttendanceQueue
    with TableInfo<$AttendanceQueueTable, AttendanceQueueData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AttendanceQueueTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _idempotencyKeyMeta = const VerificationMeta(
    'idempotencyKey',
  );
  @override
  late final GeneratedColumn<String> idempotencyKey = GeneratedColumn<String>(
    'idempotency_key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'),
  );
  static const VerificationMeta _cardUidMeta = const VerificationMeta(
    'cardUid',
  );
  @override
  late final GeneratedColumn<String> cardUid = GeneratedColumn<String>(
    'card_uid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _studentNameMeta = const VerificationMeta(
    'studentName',
  );
  @override
  late final GeneratedColumn<String> studentName = GeneratedColumn<String>(
    'student_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _directionMeta = const VerificationMeta(
    'direction',
  );
  @override
  late final GeneratedColumn<String> direction = GeneratedColumn<String>(
    'direction',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _deviceLocalTimestampMeta =
      const VerificationMeta('deviceLocalTimestamp');
  @override
  late final GeneratedColumn<String> deviceLocalTimestamp =
      GeneratedColumn<String>(
        'device_local_timestamp',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _kampalaDayMeta = const VerificationMeta(
    'kampalaDay',
  );
  @override
  late final GeneratedColumn<String> kampalaDay = GeneratedColumn<String>(
    'kampala_day',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _reasonMeta = const VerificationMeta('reason');
  @override
  late final GeneratedColumn<String> reason = GeneratedColumn<String>(
    'reason',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _attemptsMeta = const VerificationMeta(
    'attempts',
  );
  @override
  late final GeneratedColumn<int> attempts = GeneratedColumn<int>(
    'attempts',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _syncedAtMeta = const VerificationMeta(
    'syncedAt',
  );
  @override
  late final GeneratedColumn<DateTime> syncedAt = GeneratedColumn<DateTime>(
    'synced_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    idempotencyKey,
    cardUid,
    studentName,
    direction,
    deviceLocalTimestamp,
    kampalaDay,
    createdAt,
    status,
    reason,
    attempts,
    syncedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'attendance_queue';
  @override
  VerificationContext validateIntegrity(
    Insertable<AttendanceQueueData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('idempotency_key')) {
      context.handle(
        _idempotencyKeyMeta,
        idempotencyKey.isAcceptableOrUnknown(
          data['idempotency_key']!,
          _idempotencyKeyMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_idempotencyKeyMeta);
    }
    if (data.containsKey('card_uid')) {
      context.handle(
        _cardUidMeta,
        cardUid.isAcceptableOrUnknown(data['card_uid']!, _cardUidMeta),
      );
    } else if (isInserting) {
      context.missing(_cardUidMeta);
    }
    if (data.containsKey('student_name')) {
      context.handle(
        _studentNameMeta,
        studentName.isAcceptableOrUnknown(
          data['student_name']!,
          _studentNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_studentNameMeta);
    }
    if (data.containsKey('direction')) {
      context.handle(
        _directionMeta,
        direction.isAcceptableOrUnknown(data['direction']!, _directionMeta),
      );
    } else if (isInserting) {
      context.missing(_directionMeta);
    }
    if (data.containsKey('device_local_timestamp')) {
      context.handle(
        _deviceLocalTimestampMeta,
        deviceLocalTimestamp.isAcceptableOrUnknown(
          data['device_local_timestamp']!,
          _deviceLocalTimestampMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_deviceLocalTimestampMeta);
    }
    if (data.containsKey('kampala_day')) {
      context.handle(
        _kampalaDayMeta,
        kampalaDay.isAcceptableOrUnknown(data['kampala_day']!, _kampalaDayMeta),
      );
    } else if (isInserting) {
      context.missing(_kampalaDayMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('reason')) {
      context.handle(
        _reasonMeta,
        reason.isAcceptableOrUnknown(data['reason']!, _reasonMeta),
      );
    }
    if (data.containsKey('attempts')) {
      context.handle(
        _attemptsMeta,
        attempts.isAcceptableOrUnknown(data['attempts']!, _attemptsMeta),
      );
    }
    if (data.containsKey('synced_at')) {
      context.handle(
        _syncedAtMeta,
        syncedAt.isAcceptableOrUnknown(data['synced_at']!, _syncedAtMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AttendanceQueueData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AttendanceQueueData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      idempotencyKey: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}idempotency_key'],
      )!,
      cardUid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}card_uid'],
      )!,
      studentName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}student_name'],
      )!,
      direction: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}direction'],
      )!,
      deviceLocalTimestamp: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}device_local_timestamp'],
      )!,
      kampalaDay: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}kampala_day'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      reason: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}reason'],
      ),
      attempts: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}attempts'],
      )!,
      syncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}synced_at'],
      ),
    );
  }

  @override
  $AttendanceQueueTable createAlias(String alias) {
    return $AttendanceQueueTable(attachedDatabase, alias);
  }
}

class AttendanceQueueData extends DataClass
    implements Insertable<AttendanceQueueData> {
  final int id;
  final String idempotencyKey;
  final String cardUid;
  final String studentName;
  final String direction;
  final String deviceLocalTimestamp;
  final String kampalaDay;
  final DateTime createdAt;
  final String status;
  final String? reason;
  final int attempts;
  final DateTime? syncedAt;
  const AttendanceQueueData({
    required this.id,
    required this.idempotencyKey,
    required this.cardUid,
    required this.studentName,
    required this.direction,
    required this.deviceLocalTimestamp,
    required this.kampalaDay,
    required this.createdAt,
    required this.status,
    this.reason,
    required this.attempts,
    this.syncedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['idempotency_key'] = Variable<String>(idempotencyKey);
    map['card_uid'] = Variable<String>(cardUid);
    map['student_name'] = Variable<String>(studentName);
    map['direction'] = Variable<String>(direction);
    map['device_local_timestamp'] = Variable<String>(deviceLocalTimestamp);
    map['kampala_day'] = Variable<String>(kampalaDay);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['status'] = Variable<String>(status);
    if (!nullToAbsent || reason != null) {
      map['reason'] = Variable<String>(reason);
    }
    map['attempts'] = Variable<int>(attempts);
    if (!nullToAbsent || syncedAt != null) {
      map['synced_at'] = Variable<DateTime>(syncedAt);
    }
    return map;
  }

  AttendanceQueueCompanion toCompanion(bool nullToAbsent) {
    return AttendanceQueueCompanion(
      id: Value(id),
      idempotencyKey: Value(idempotencyKey),
      cardUid: Value(cardUid),
      studentName: Value(studentName),
      direction: Value(direction),
      deviceLocalTimestamp: Value(deviceLocalTimestamp),
      kampalaDay: Value(kampalaDay),
      createdAt: Value(createdAt),
      status: Value(status),
      reason: reason == null && nullToAbsent
          ? const Value.absent()
          : Value(reason),
      attempts: Value(attempts),
      syncedAt: syncedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(syncedAt),
    );
  }

  factory AttendanceQueueData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AttendanceQueueData(
      id: serializer.fromJson<int>(json['id']),
      idempotencyKey: serializer.fromJson<String>(json['idempotencyKey']),
      cardUid: serializer.fromJson<String>(json['cardUid']),
      studentName: serializer.fromJson<String>(json['studentName']),
      direction: serializer.fromJson<String>(json['direction']),
      deviceLocalTimestamp: serializer.fromJson<String>(
        json['deviceLocalTimestamp'],
      ),
      kampalaDay: serializer.fromJson<String>(json['kampalaDay']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      status: serializer.fromJson<String>(json['status']),
      reason: serializer.fromJson<String?>(json['reason']),
      attempts: serializer.fromJson<int>(json['attempts']),
      syncedAt: serializer.fromJson<DateTime?>(json['syncedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'idempotencyKey': serializer.toJson<String>(idempotencyKey),
      'cardUid': serializer.toJson<String>(cardUid),
      'studentName': serializer.toJson<String>(studentName),
      'direction': serializer.toJson<String>(direction),
      'deviceLocalTimestamp': serializer.toJson<String>(deviceLocalTimestamp),
      'kampalaDay': serializer.toJson<String>(kampalaDay),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'status': serializer.toJson<String>(status),
      'reason': serializer.toJson<String?>(reason),
      'attempts': serializer.toJson<int>(attempts),
      'syncedAt': serializer.toJson<DateTime?>(syncedAt),
    };
  }

  AttendanceQueueData copyWith({
    int? id,
    String? idempotencyKey,
    String? cardUid,
    String? studentName,
    String? direction,
    String? deviceLocalTimestamp,
    String? kampalaDay,
    DateTime? createdAt,
    String? status,
    Value<String?> reason = const Value.absent(),
    int? attempts,
    Value<DateTime?> syncedAt = const Value.absent(),
  }) => AttendanceQueueData(
    id: id ?? this.id,
    idempotencyKey: idempotencyKey ?? this.idempotencyKey,
    cardUid: cardUid ?? this.cardUid,
    studentName: studentName ?? this.studentName,
    direction: direction ?? this.direction,
    deviceLocalTimestamp: deviceLocalTimestamp ?? this.deviceLocalTimestamp,
    kampalaDay: kampalaDay ?? this.kampalaDay,
    createdAt: createdAt ?? this.createdAt,
    status: status ?? this.status,
    reason: reason.present ? reason.value : this.reason,
    attempts: attempts ?? this.attempts,
    syncedAt: syncedAt.present ? syncedAt.value : this.syncedAt,
  );
  AttendanceQueueData copyWithCompanion(AttendanceQueueCompanion data) {
    return AttendanceQueueData(
      id: data.id.present ? data.id.value : this.id,
      idempotencyKey: data.idempotencyKey.present
          ? data.idempotencyKey.value
          : this.idempotencyKey,
      cardUid: data.cardUid.present ? data.cardUid.value : this.cardUid,
      studentName: data.studentName.present
          ? data.studentName.value
          : this.studentName,
      direction: data.direction.present ? data.direction.value : this.direction,
      deviceLocalTimestamp: data.deviceLocalTimestamp.present
          ? data.deviceLocalTimestamp.value
          : this.deviceLocalTimestamp,
      kampalaDay: data.kampalaDay.present
          ? data.kampalaDay.value
          : this.kampalaDay,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      status: data.status.present ? data.status.value : this.status,
      reason: data.reason.present ? data.reason.value : this.reason,
      attempts: data.attempts.present ? data.attempts.value : this.attempts,
      syncedAt: data.syncedAt.present ? data.syncedAt.value : this.syncedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AttendanceQueueData(')
          ..write('id: $id, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('cardUid: $cardUid, ')
          ..write('studentName: $studentName, ')
          ..write('direction: $direction, ')
          ..write('deviceLocalTimestamp: $deviceLocalTimestamp, ')
          ..write('kampalaDay: $kampalaDay, ')
          ..write('createdAt: $createdAt, ')
          ..write('status: $status, ')
          ..write('reason: $reason, ')
          ..write('attempts: $attempts, ')
          ..write('syncedAt: $syncedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    idempotencyKey,
    cardUid,
    studentName,
    direction,
    deviceLocalTimestamp,
    kampalaDay,
    createdAt,
    status,
    reason,
    attempts,
    syncedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AttendanceQueueData &&
          other.id == this.id &&
          other.idempotencyKey == this.idempotencyKey &&
          other.cardUid == this.cardUid &&
          other.studentName == this.studentName &&
          other.direction == this.direction &&
          other.deviceLocalTimestamp == this.deviceLocalTimestamp &&
          other.kampalaDay == this.kampalaDay &&
          other.createdAt == this.createdAt &&
          other.status == this.status &&
          other.reason == this.reason &&
          other.attempts == this.attempts &&
          other.syncedAt == this.syncedAt);
}

class AttendanceQueueCompanion extends UpdateCompanion<AttendanceQueueData> {
  final Value<int> id;
  final Value<String> idempotencyKey;
  final Value<String> cardUid;
  final Value<String> studentName;
  final Value<String> direction;
  final Value<String> deviceLocalTimestamp;
  final Value<String> kampalaDay;
  final Value<DateTime> createdAt;
  final Value<String> status;
  final Value<String?> reason;
  final Value<int> attempts;
  final Value<DateTime?> syncedAt;
  const AttendanceQueueCompanion({
    this.id = const Value.absent(),
    this.idempotencyKey = const Value.absent(),
    this.cardUid = const Value.absent(),
    this.studentName = const Value.absent(),
    this.direction = const Value.absent(),
    this.deviceLocalTimestamp = const Value.absent(),
    this.kampalaDay = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.status = const Value.absent(),
    this.reason = const Value.absent(),
    this.attempts = const Value.absent(),
    this.syncedAt = const Value.absent(),
  });
  AttendanceQueueCompanion.insert({
    this.id = const Value.absent(),
    required String idempotencyKey,
    required String cardUid,
    required String studentName,
    required String direction,
    required String deviceLocalTimestamp,
    required String kampalaDay,
    required DateTime createdAt,
    required String status,
    this.reason = const Value.absent(),
    this.attempts = const Value.absent(),
    this.syncedAt = const Value.absent(),
  }) : idempotencyKey = Value(idempotencyKey),
       cardUid = Value(cardUid),
       studentName = Value(studentName),
       direction = Value(direction),
       deviceLocalTimestamp = Value(deviceLocalTimestamp),
       kampalaDay = Value(kampalaDay),
       createdAt = Value(createdAt),
       status = Value(status);
  static Insertable<AttendanceQueueData> custom({
    Expression<int>? id,
    Expression<String>? idempotencyKey,
    Expression<String>? cardUid,
    Expression<String>? studentName,
    Expression<String>? direction,
    Expression<String>? deviceLocalTimestamp,
    Expression<String>? kampalaDay,
    Expression<DateTime>? createdAt,
    Expression<String>? status,
    Expression<String>? reason,
    Expression<int>? attempts,
    Expression<DateTime>? syncedAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (idempotencyKey != null) 'idempotency_key': idempotencyKey,
      if (cardUid != null) 'card_uid': cardUid,
      if (studentName != null) 'student_name': studentName,
      if (direction != null) 'direction': direction,
      if (deviceLocalTimestamp != null)
        'device_local_timestamp': deviceLocalTimestamp,
      if (kampalaDay != null) 'kampala_day': kampalaDay,
      if (createdAt != null) 'created_at': createdAt,
      if (status != null) 'status': status,
      if (reason != null) 'reason': reason,
      if (attempts != null) 'attempts': attempts,
      if (syncedAt != null) 'synced_at': syncedAt,
    });
  }

  AttendanceQueueCompanion copyWith({
    Value<int>? id,
    Value<String>? idempotencyKey,
    Value<String>? cardUid,
    Value<String>? studentName,
    Value<String>? direction,
    Value<String>? deviceLocalTimestamp,
    Value<String>? kampalaDay,
    Value<DateTime>? createdAt,
    Value<String>? status,
    Value<String?>? reason,
    Value<int>? attempts,
    Value<DateTime?>? syncedAt,
  }) {
    return AttendanceQueueCompanion(
      id: id ?? this.id,
      idempotencyKey: idempotencyKey ?? this.idempotencyKey,
      cardUid: cardUid ?? this.cardUid,
      studentName: studentName ?? this.studentName,
      direction: direction ?? this.direction,
      deviceLocalTimestamp: deviceLocalTimestamp ?? this.deviceLocalTimestamp,
      kampalaDay: kampalaDay ?? this.kampalaDay,
      createdAt: createdAt ?? this.createdAt,
      status: status ?? this.status,
      reason: reason ?? this.reason,
      attempts: attempts ?? this.attempts,
      syncedAt: syncedAt ?? this.syncedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (idempotencyKey.present) {
      map['idempotency_key'] = Variable<String>(idempotencyKey.value);
    }
    if (cardUid.present) {
      map['card_uid'] = Variable<String>(cardUid.value);
    }
    if (studentName.present) {
      map['student_name'] = Variable<String>(studentName.value);
    }
    if (direction.present) {
      map['direction'] = Variable<String>(direction.value);
    }
    if (deviceLocalTimestamp.present) {
      map['device_local_timestamp'] = Variable<String>(
        deviceLocalTimestamp.value,
      );
    }
    if (kampalaDay.present) {
      map['kampala_day'] = Variable<String>(kampalaDay.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (reason.present) {
      map['reason'] = Variable<String>(reason.value);
    }
    if (attempts.present) {
      map['attempts'] = Variable<int>(attempts.value);
    }
    if (syncedAt.present) {
      map['synced_at'] = Variable<DateTime>(syncedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AttendanceQueueCompanion(')
          ..write('id: $id, ')
          ..write('idempotencyKey: $idempotencyKey, ')
          ..write('cardUid: $cardUid, ')
          ..write('studentName: $studentName, ')
          ..write('direction: $direction, ')
          ..write('deviceLocalTimestamp: $deviceLocalTimestamp, ')
          ..write('kampalaDay: $kampalaDay, ')
          ..write('createdAt: $createdAt, ')
          ..write('status: $status, ')
          ..write('reason: $reason, ')
          ..write('attempts: $attempts, ')
          ..write('syncedAt: $syncedAt')
          ..write(')'))
        .toString();
  }
}

class $PinFailuresTable extends PinFailures
    with TableInfo<$PinFailuresTable, PinFailure> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PinFailuresTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _cardUidMeta = const VerificationMeta(
    'cardUid',
  );
  @override
  late final GeneratedColumn<String> cardUid = GeneratedColumn<String>(
    'card_uid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _failuresMeta = const VerificationMeta(
    'failures',
  );
  @override
  late final GeneratedColumn<int> failures = GeneratedColumn<int>(
    'failures',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _unreportedMeta = const VerificationMeta(
    'unreported',
  );
  @override
  late final GeneratedColumn<int> unreported = GeneratedColumn<int>(
    'unreported',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _firstFailureAtMeta = const VerificationMeta(
    'firstFailureAt',
  );
  @override
  late final GeneratedColumn<DateTime> firstFailureAt =
      GeneratedColumn<DateTime>(
        'first_failure_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _lastFailureAtMeta = const VerificationMeta(
    'lastFailureAt',
  );
  @override
  late final GeneratedColumn<DateTime> lastFailureAt =
      GeneratedColumn<DateTime>(
        'last_failure_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _lockedMeta = const VerificationMeta('locked');
  @override
  late final GeneratedColumn<bool> locked = GeneratedColumn<bool>(
    'locked',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("locked" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  @override
  List<GeneratedColumn> get $columns => [
    cardUid,
    failures,
    unreported,
    firstFailureAt,
    lastFailureAt,
    locked,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pin_failures';
  @override
  VerificationContext validateIntegrity(
    Insertable<PinFailure> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('card_uid')) {
      context.handle(
        _cardUidMeta,
        cardUid.isAcceptableOrUnknown(data['card_uid']!, _cardUidMeta),
      );
    } else if (isInserting) {
      context.missing(_cardUidMeta);
    }
    if (data.containsKey('failures')) {
      context.handle(
        _failuresMeta,
        failures.isAcceptableOrUnknown(data['failures']!, _failuresMeta),
      );
    } else if (isInserting) {
      context.missing(_failuresMeta);
    }
    if (data.containsKey('unreported')) {
      context.handle(
        _unreportedMeta,
        unreported.isAcceptableOrUnknown(data['unreported']!, _unreportedMeta),
      );
    } else if (isInserting) {
      context.missing(_unreportedMeta);
    }
    if (data.containsKey('first_failure_at')) {
      context.handle(
        _firstFailureAtMeta,
        firstFailureAt.isAcceptableOrUnknown(
          data['first_failure_at']!,
          _firstFailureAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_firstFailureAtMeta);
    }
    if (data.containsKey('last_failure_at')) {
      context.handle(
        _lastFailureAtMeta,
        lastFailureAt.isAcceptableOrUnknown(
          data['last_failure_at']!,
          _lastFailureAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_lastFailureAtMeta);
    }
    if (data.containsKey('locked')) {
      context.handle(
        _lockedMeta,
        locked.isAcceptableOrUnknown(data['locked']!, _lockedMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {cardUid};
  @override
  PinFailure map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PinFailure(
      cardUid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}card_uid'],
      )!,
      failures: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}failures'],
      )!,
      unreported: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}unreported'],
      )!,
      firstFailureAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}first_failure_at'],
      )!,
      lastFailureAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_failure_at'],
      )!,
      locked: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}locked'],
      )!,
    );
  }

  @override
  $PinFailuresTable createAlias(String alias) {
    return $PinFailuresTable(attachedDatabase, alias);
  }
}

class PinFailure extends DataClass implements Insertable<PinFailure> {
  final String cardUid;
  final int failures;
  final int unreported;
  final DateTime firstFailureAt;
  final DateTime lastFailureAt;
  final bool locked;
  const PinFailure({
    required this.cardUid,
    required this.failures,
    required this.unreported,
    required this.firstFailureAt,
    required this.lastFailureAt,
    required this.locked,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['card_uid'] = Variable<String>(cardUid);
    map['failures'] = Variable<int>(failures);
    map['unreported'] = Variable<int>(unreported);
    map['first_failure_at'] = Variable<DateTime>(firstFailureAt);
    map['last_failure_at'] = Variable<DateTime>(lastFailureAt);
    map['locked'] = Variable<bool>(locked);
    return map;
  }

  PinFailuresCompanion toCompanion(bool nullToAbsent) {
    return PinFailuresCompanion(
      cardUid: Value(cardUid),
      failures: Value(failures),
      unreported: Value(unreported),
      firstFailureAt: Value(firstFailureAt),
      lastFailureAt: Value(lastFailureAt),
      locked: Value(locked),
    );
  }

  factory PinFailure.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PinFailure(
      cardUid: serializer.fromJson<String>(json['cardUid']),
      failures: serializer.fromJson<int>(json['failures']),
      unreported: serializer.fromJson<int>(json['unreported']),
      firstFailureAt: serializer.fromJson<DateTime>(json['firstFailureAt']),
      lastFailureAt: serializer.fromJson<DateTime>(json['lastFailureAt']),
      locked: serializer.fromJson<bool>(json['locked']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'cardUid': serializer.toJson<String>(cardUid),
      'failures': serializer.toJson<int>(failures),
      'unreported': serializer.toJson<int>(unreported),
      'firstFailureAt': serializer.toJson<DateTime>(firstFailureAt),
      'lastFailureAt': serializer.toJson<DateTime>(lastFailureAt),
      'locked': serializer.toJson<bool>(locked),
    };
  }

  PinFailure copyWith({
    String? cardUid,
    int? failures,
    int? unreported,
    DateTime? firstFailureAt,
    DateTime? lastFailureAt,
    bool? locked,
  }) => PinFailure(
    cardUid: cardUid ?? this.cardUid,
    failures: failures ?? this.failures,
    unreported: unreported ?? this.unreported,
    firstFailureAt: firstFailureAt ?? this.firstFailureAt,
    lastFailureAt: lastFailureAt ?? this.lastFailureAt,
    locked: locked ?? this.locked,
  );
  PinFailure copyWithCompanion(PinFailuresCompanion data) {
    return PinFailure(
      cardUid: data.cardUid.present ? data.cardUid.value : this.cardUid,
      failures: data.failures.present ? data.failures.value : this.failures,
      unreported: data.unreported.present
          ? data.unreported.value
          : this.unreported,
      firstFailureAt: data.firstFailureAt.present
          ? data.firstFailureAt.value
          : this.firstFailureAt,
      lastFailureAt: data.lastFailureAt.present
          ? data.lastFailureAt.value
          : this.lastFailureAt,
      locked: data.locked.present ? data.locked.value : this.locked,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PinFailure(')
          ..write('cardUid: $cardUid, ')
          ..write('failures: $failures, ')
          ..write('unreported: $unreported, ')
          ..write('firstFailureAt: $firstFailureAt, ')
          ..write('lastFailureAt: $lastFailureAt, ')
          ..write('locked: $locked')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    cardUid,
    failures,
    unreported,
    firstFailureAt,
    lastFailureAt,
    locked,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PinFailure &&
          other.cardUid == this.cardUid &&
          other.failures == this.failures &&
          other.unreported == this.unreported &&
          other.firstFailureAt == this.firstFailureAt &&
          other.lastFailureAt == this.lastFailureAt &&
          other.locked == this.locked);
}

class PinFailuresCompanion extends UpdateCompanion<PinFailure> {
  final Value<String> cardUid;
  final Value<int> failures;
  final Value<int> unreported;
  final Value<DateTime> firstFailureAt;
  final Value<DateTime> lastFailureAt;
  final Value<bool> locked;
  final Value<int> rowid;
  const PinFailuresCompanion({
    this.cardUid = const Value.absent(),
    this.failures = const Value.absent(),
    this.unreported = const Value.absent(),
    this.firstFailureAt = const Value.absent(),
    this.lastFailureAt = const Value.absent(),
    this.locked = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PinFailuresCompanion.insert({
    required String cardUid,
    required int failures,
    required int unreported,
    required DateTime firstFailureAt,
    required DateTime lastFailureAt,
    this.locked = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : cardUid = Value(cardUid),
       failures = Value(failures),
       unreported = Value(unreported),
       firstFailureAt = Value(firstFailureAt),
       lastFailureAt = Value(lastFailureAt);
  static Insertable<PinFailure> custom({
    Expression<String>? cardUid,
    Expression<int>? failures,
    Expression<int>? unreported,
    Expression<DateTime>? firstFailureAt,
    Expression<DateTime>? lastFailureAt,
    Expression<bool>? locked,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (cardUid != null) 'card_uid': cardUid,
      if (failures != null) 'failures': failures,
      if (unreported != null) 'unreported': unreported,
      if (firstFailureAt != null) 'first_failure_at': firstFailureAt,
      if (lastFailureAt != null) 'last_failure_at': lastFailureAt,
      if (locked != null) 'locked': locked,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PinFailuresCompanion copyWith({
    Value<String>? cardUid,
    Value<int>? failures,
    Value<int>? unreported,
    Value<DateTime>? firstFailureAt,
    Value<DateTime>? lastFailureAt,
    Value<bool>? locked,
    Value<int>? rowid,
  }) {
    return PinFailuresCompanion(
      cardUid: cardUid ?? this.cardUid,
      failures: failures ?? this.failures,
      unreported: unreported ?? this.unreported,
      firstFailureAt: firstFailureAt ?? this.firstFailureAt,
      lastFailureAt: lastFailureAt ?? this.lastFailureAt,
      locked: locked ?? this.locked,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (cardUid.present) {
      map['card_uid'] = Variable<String>(cardUid.value);
    }
    if (failures.present) {
      map['failures'] = Variable<int>(failures.value);
    }
    if (unreported.present) {
      map['unreported'] = Variable<int>(unreported.value);
    }
    if (firstFailureAt.present) {
      map['first_failure_at'] = Variable<DateTime>(firstFailureAt.value);
    }
    if (lastFailureAt.present) {
      map['last_failure_at'] = Variable<DateTime>(lastFailureAt.value);
    }
    if (locked.present) {
      map['locked'] = Variable<bool>(locked.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PinFailuresCompanion(')
          ..write('cardUid: $cardUid, ')
          ..write('failures: $failures, ')
          ..write('unreported: $unreported, ')
          ..write('firstFailureAt: $firstFailureAt, ')
          ..write('lastFailureAt: $lastFailureAt, ')
          ..write('locked: $locked, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $KvTable extends Kv with TableInfo<$KvTable, KvData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $KvTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
    'key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
    'value',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'kv';
  @override
  VerificationContext validateIntegrity(
    Insertable<KvData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
        _keyMeta,
        key.isAcceptableOrUnknown(data['key']!, _keyMeta),
      );
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
        _valueMeta,
        value.isAcceptableOrUnknown(data['value']!, _valueMeta),
      );
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  KvData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return KvData(
      key: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}key'],
      )!,
      value: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}value'],
      )!,
    );
  }

  @override
  $KvTable createAlias(String alias) {
    return $KvTable(attachedDatabase, alias);
  }
}

class KvData extends DataClass implements Insertable<KvData> {
  final String key;
  final String value;
  const KvData({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  KvCompanion toCompanion(bool nullToAbsent) {
    return KvCompanion(key: Value(key), value: Value(value));
  }

  factory KvData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return KvData(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  KvData copyWith({String? key, String? value}) =>
      KvData(key: key ?? this.key, value: value ?? this.value);
  KvData copyWithCompanion(KvCompanion data) {
    return KvData(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('KvData(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is KvData && other.key == this.key && other.value == this.value);
}

class KvCompanion extends UpdateCompanion<KvData> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const KvCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  KvCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  }) : key = Value(key),
       value = Value(value);
  static Insertable<KvData> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  KvCompanion copyWith({
    Value<String>? key,
    Value<String>? value,
    Value<int>? rowid,
  }) {
    return KvCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('KvCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncLogTable extends SyncLog with TableInfo<$SyncLogTable, SyncLogData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncLogTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _atMeta = const VerificationMeta('at');
  @override
  late final GeneratedColumn<DateTime> at = GeneratedColumn<DateTime>(
    'at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _kindMeta = const VerificationMeta('kind');
  @override
  late final GeneratedColumn<String> kind = GeneratedColumn<String>(
    'kind',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _okMeta = const VerificationMeta('ok');
  @override
  late final GeneratedColumn<bool> ok = GeneratedColumn<bool>(
    'ok',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("ok" IN (0, 1))',
    ),
  );
  static const VerificationMeta _messageMeta = const VerificationMeta(
    'message',
  );
  @override
  late final GeneratedColumn<String> message = GeneratedColumn<String>(
    'message',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, at, kind, ok, message];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_log';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncLogData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('at')) {
      context.handle(_atMeta, at.isAcceptableOrUnknown(data['at']!, _atMeta));
    } else if (isInserting) {
      context.missing(_atMeta);
    }
    if (data.containsKey('kind')) {
      context.handle(
        _kindMeta,
        kind.isAcceptableOrUnknown(data['kind']!, _kindMeta),
      );
    } else if (isInserting) {
      context.missing(_kindMeta);
    }
    if (data.containsKey('ok')) {
      context.handle(_okMeta, ok.isAcceptableOrUnknown(data['ok']!, _okMeta));
    } else if (isInserting) {
      context.missing(_okMeta);
    }
    if (data.containsKey('message')) {
      context.handle(
        _messageMeta,
        message.isAcceptableOrUnknown(data['message']!, _messageMeta),
      );
    } else if (isInserting) {
      context.missing(_messageMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncLogData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncLogData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      at: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}at'],
      )!,
      kind: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}kind'],
      )!,
      ok: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}ok'],
      )!,
      message: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}message'],
      )!,
    );
  }

  @override
  $SyncLogTable createAlias(String alias) {
    return $SyncLogTable(attachedDatabase, alias);
  }
}

class SyncLogData extends DataClass implements Insertable<SyncLogData> {
  final int id;
  final DateTime at;
  final String kind;
  final bool ok;
  final String message;
  const SyncLogData({
    required this.id,
    required this.at,
    required this.kind,
    required this.ok,
    required this.message,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['at'] = Variable<DateTime>(at);
    map['kind'] = Variable<String>(kind);
    map['ok'] = Variable<bool>(ok);
    map['message'] = Variable<String>(message);
    return map;
  }

  SyncLogCompanion toCompanion(bool nullToAbsent) {
    return SyncLogCompanion(
      id: Value(id),
      at: Value(at),
      kind: Value(kind),
      ok: Value(ok),
      message: Value(message),
    );
  }

  factory SyncLogData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncLogData(
      id: serializer.fromJson<int>(json['id']),
      at: serializer.fromJson<DateTime>(json['at']),
      kind: serializer.fromJson<String>(json['kind']),
      ok: serializer.fromJson<bool>(json['ok']),
      message: serializer.fromJson<String>(json['message']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'at': serializer.toJson<DateTime>(at),
      'kind': serializer.toJson<String>(kind),
      'ok': serializer.toJson<bool>(ok),
      'message': serializer.toJson<String>(message),
    };
  }

  SyncLogData copyWith({
    int? id,
    DateTime? at,
    String? kind,
    bool? ok,
    String? message,
  }) => SyncLogData(
    id: id ?? this.id,
    at: at ?? this.at,
    kind: kind ?? this.kind,
    ok: ok ?? this.ok,
    message: message ?? this.message,
  );
  SyncLogData copyWithCompanion(SyncLogCompanion data) {
    return SyncLogData(
      id: data.id.present ? data.id.value : this.id,
      at: data.at.present ? data.at.value : this.at,
      kind: data.kind.present ? data.kind.value : this.kind,
      ok: data.ok.present ? data.ok.value : this.ok,
      message: data.message.present ? data.message.value : this.message,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncLogData(')
          ..write('id: $id, ')
          ..write('at: $at, ')
          ..write('kind: $kind, ')
          ..write('ok: $ok, ')
          ..write('message: $message')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, at, kind, ok, message);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncLogData &&
          other.id == this.id &&
          other.at == this.at &&
          other.kind == this.kind &&
          other.ok == this.ok &&
          other.message == this.message);
}

class SyncLogCompanion extends UpdateCompanion<SyncLogData> {
  final Value<int> id;
  final Value<DateTime> at;
  final Value<String> kind;
  final Value<bool> ok;
  final Value<String> message;
  const SyncLogCompanion({
    this.id = const Value.absent(),
    this.at = const Value.absent(),
    this.kind = const Value.absent(),
    this.ok = const Value.absent(),
    this.message = const Value.absent(),
  });
  SyncLogCompanion.insert({
    this.id = const Value.absent(),
    required DateTime at,
    required String kind,
    required bool ok,
    required String message,
  }) : at = Value(at),
       kind = Value(kind),
       ok = Value(ok),
       message = Value(message);
  static Insertable<SyncLogData> custom({
    Expression<int>? id,
    Expression<DateTime>? at,
    Expression<String>? kind,
    Expression<bool>? ok,
    Expression<String>? message,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (at != null) 'at': at,
      if (kind != null) 'kind': kind,
      if (ok != null) 'ok': ok,
      if (message != null) 'message': message,
    });
  }

  SyncLogCompanion copyWith({
    Value<int>? id,
    Value<DateTime>? at,
    Value<String>? kind,
    Value<bool>? ok,
    Value<String>? message,
  }) {
    return SyncLogCompanion(
      id: id ?? this.id,
      at: at ?? this.at,
      kind: kind ?? this.kind,
      ok: ok ?? this.ok,
      message: message ?? this.message,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (at.present) {
      map['at'] = Variable<DateTime>(at.value);
    }
    if (kind.present) {
      map['kind'] = Variable<String>(kind.value);
    }
    if (ok.present) {
      map['ok'] = Variable<bool>(ok.value);
    }
    if (message.present) {
      map['message'] = Variable<String>(message.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncLogCompanion(')
          ..write('id: $id, ')
          ..write('at: $at, ')
          ..write('kind: $kind, ')
          ..write('ok: $ok, ')
          ..write('message: $message')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedCardsTable cachedCards = $CachedCardsTable(this);
  late final $ProductsTable products = $ProductsTable(this);
  late final $CategoriesTable categories = $CategoriesTable(this);
  late final $RosterCardsTable rosterCards = $RosterCardsTable(this);
  late final $SaleQueueTable saleQueue = $SaleQueueTable(this);
  late final $AttendanceQueueTable attendanceQueue = $AttendanceQueueTable(
    this,
  );
  late final $PinFailuresTable pinFailures = $PinFailuresTable(this);
  late final $KvTable kv = $KvTable(this);
  late final $SyncLogTable syncLog = $SyncLogTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    cachedCards,
    products,
    categories,
    rosterCards,
    saleQueue,
    attendanceQueue,
    pinFailures,
    kv,
    syncLog,
  ];
}

typedef $$CachedCardsTableCreateCompanionBuilder =
    CachedCardsCompanion Function({
      required String cardUid,
      required int cardId,
      required String status,
      required String pinHash,
      required int studentId,
      required String displayName,
      Value<String?> photoUrl,
      required int schoolId,
      required int walletId,
      required int balanceCents,
      required int todaySpendCents,
      required int weekSpendCents,
      required String spendDay,
      required String weekStart,
      required int offlineCeilingCents,
      required String policyJson,
      required DateTime balanceAsOf,
      Value<int> rowid,
    });
typedef $$CachedCardsTableUpdateCompanionBuilder =
    CachedCardsCompanion Function({
      Value<String> cardUid,
      Value<int> cardId,
      Value<String> status,
      Value<String> pinHash,
      Value<int> studentId,
      Value<String> displayName,
      Value<String?> photoUrl,
      Value<int> schoolId,
      Value<int> walletId,
      Value<int> balanceCents,
      Value<int> todaySpendCents,
      Value<int> weekSpendCents,
      Value<String> spendDay,
      Value<String> weekStart,
      Value<int> offlineCeilingCents,
      Value<String> policyJson,
      Value<DateTime> balanceAsOf,
      Value<int> rowid,
    });

class $$CachedCardsTableFilterComposer
    extends Composer<_$AppDatabase, $CachedCardsTable> {
  $$CachedCardsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get cardId => $composableBuilder(
    column: $table.cardId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get pinHash => $composableBuilder(
    column: $table.pinHash,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get studentId => $composableBuilder(
    column: $table.studentId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get walletId => $composableBuilder(
    column: $table.walletId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get balanceCents => $composableBuilder(
    column: $table.balanceCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get todaySpendCents => $composableBuilder(
    column: $table.todaySpendCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get weekSpendCents => $composableBuilder(
    column: $table.weekSpendCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get spendDay => $composableBuilder(
    column: $table.spendDay,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get weekStart => $composableBuilder(
    column: $table.weekStart,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get offlineCeilingCents => $composableBuilder(
    column: $table.offlineCeilingCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get policyJson => $composableBuilder(
    column: $table.policyJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get balanceAsOf => $composableBuilder(
    column: $table.balanceAsOf,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedCardsTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedCardsTable> {
  $$CachedCardsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get cardId => $composableBuilder(
    column: $table.cardId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get pinHash => $composableBuilder(
    column: $table.pinHash,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get studentId => $composableBuilder(
    column: $table.studentId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get walletId => $composableBuilder(
    column: $table.walletId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get balanceCents => $composableBuilder(
    column: $table.balanceCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get todaySpendCents => $composableBuilder(
    column: $table.todaySpendCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get weekSpendCents => $composableBuilder(
    column: $table.weekSpendCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get spendDay => $composableBuilder(
    column: $table.spendDay,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get weekStart => $composableBuilder(
    column: $table.weekStart,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get offlineCeilingCents => $composableBuilder(
    column: $table.offlineCeilingCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get policyJson => $composableBuilder(
    column: $table.policyJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get balanceAsOf => $composableBuilder(
    column: $table.balanceAsOf,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedCardsTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedCardsTable> {
  $$CachedCardsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get cardUid =>
      $composableBuilder(column: $table.cardUid, builder: (column) => column);

  GeneratedColumn<int> get cardId =>
      $composableBuilder(column: $table.cardId, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get pinHash =>
      $composableBuilder(column: $table.pinHash, builder: (column) => column);

  GeneratedColumn<int> get studentId =>
      $composableBuilder(column: $table.studentId, builder: (column) => column);

  GeneratedColumn<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get photoUrl =>
      $composableBuilder(column: $table.photoUrl, builder: (column) => column);

  GeneratedColumn<int> get schoolId =>
      $composableBuilder(column: $table.schoolId, builder: (column) => column);

  GeneratedColumn<int> get walletId =>
      $composableBuilder(column: $table.walletId, builder: (column) => column);

  GeneratedColumn<int> get balanceCents => $composableBuilder(
    column: $table.balanceCents,
    builder: (column) => column,
  );

  GeneratedColumn<int> get todaySpendCents => $composableBuilder(
    column: $table.todaySpendCents,
    builder: (column) => column,
  );

  GeneratedColumn<int> get weekSpendCents => $composableBuilder(
    column: $table.weekSpendCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get spendDay =>
      $composableBuilder(column: $table.spendDay, builder: (column) => column);

  GeneratedColumn<String> get weekStart =>
      $composableBuilder(column: $table.weekStart, builder: (column) => column);

  GeneratedColumn<int> get offlineCeilingCents => $composableBuilder(
    column: $table.offlineCeilingCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get policyJson => $composableBuilder(
    column: $table.policyJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get balanceAsOf => $composableBuilder(
    column: $table.balanceAsOf,
    builder: (column) => column,
  );
}

class $$CachedCardsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedCardsTable,
          CachedCard,
          $$CachedCardsTableFilterComposer,
          $$CachedCardsTableOrderingComposer,
          $$CachedCardsTableAnnotationComposer,
          $$CachedCardsTableCreateCompanionBuilder,
          $$CachedCardsTableUpdateCompanionBuilder,
          (
            CachedCard,
            BaseReferences<_$AppDatabase, $CachedCardsTable, CachedCard>,
          ),
          CachedCard,
          PrefetchHooks Function()
        > {
  $$CachedCardsTableTableManager(_$AppDatabase db, $CachedCardsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedCardsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedCardsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedCardsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> cardUid = const Value.absent(),
                Value<int> cardId = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> pinHash = const Value.absent(),
                Value<int> studentId = const Value.absent(),
                Value<String> displayName = const Value.absent(),
                Value<String?> photoUrl = const Value.absent(),
                Value<int> schoolId = const Value.absent(),
                Value<int> walletId = const Value.absent(),
                Value<int> balanceCents = const Value.absent(),
                Value<int> todaySpendCents = const Value.absent(),
                Value<int> weekSpendCents = const Value.absent(),
                Value<String> spendDay = const Value.absent(),
                Value<String> weekStart = const Value.absent(),
                Value<int> offlineCeilingCents = const Value.absent(),
                Value<String> policyJson = const Value.absent(),
                Value<DateTime> balanceAsOf = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedCardsCompanion(
                cardUid: cardUid,
                cardId: cardId,
                status: status,
                pinHash: pinHash,
                studentId: studentId,
                displayName: displayName,
                photoUrl: photoUrl,
                schoolId: schoolId,
                walletId: walletId,
                balanceCents: balanceCents,
                todaySpendCents: todaySpendCents,
                weekSpendCents: weekSpendCents,
                spendDay: spendDay,
                weekStart: weekStart,
                offlineCeilingCents: offlineCeilingCents,
                policyJson: policyJson,
                balanceAsOf: balanceAsOf,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String cardUid,
                required int cardId,
                required String status,
                required String pinHash,
                required int studentId,
                required String displayName,
                Value<String?> photoUrl = const Value.absent(),
                required int schoolId,
                required int walletId,
                required int balanceCents,
                required int todaySpendCents,
                required int weekSpendCents,
                required String spendDay,
                required String weekStart,
                required int offlineCeilingCents,
                required String policyJson,
                required DateTime balanceAsOf,
                Value<int> rowid = const Value.absent(),
              }) => CachedCardsCompanion.insert(
                cardUid: cardUid,
                cardId: cardId,
                status: status,
                pinHash: pinHash,
                studentId: studentId,
                displayName: displayName,
                photoUrl: photoUrl,
                schoolId: schoolId,
                walletId: walletId,
                balanceCents: balanceCents,
                todaySpendCents: todaySpendCents,
                weekSpendCents: weekSpendCents,
                spendDay: spendDay,
                weekStart: weekStart,
                offlineCeilingCents: offlineCeilingCents,
                policyJson: policyJson,
                balanceAsOf: balanceAsOf,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CachedCardsTable, CachedCard>(table),
                  BaseReferences<_$AppDatabase, $CachedCardsTable, CachedCard>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedCardsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedCardsTable,
      CachedCard,
      $$CachedCardsTableFilterComposer,
      $$CachedCardsTableOrderingComposer,
      $$CachedCardsTableAnnotationComposer,
      $$CachedCardsTableCreateCompanionBuilder,
      $$CachedCardsTableUpdateCompanionBuilder,
      (
        CachedCard,
        BaseReferences<_$AppDatabase, $CachedCardsTable, CachedCard>,
      ),
      CachedCard,
      PrefetchHooks Function()
    >;
typedef $$ProductsTableCreateCompanionBuilder = ProductsCompanion Function({
  Value<int> id,
  required String name,
  required int categoryId,
  required String categoryName,
  required int priceCents,
  required bool active,
  required int schoolId,
  Value<int?> merchantId,
});
typedef $$ProductsTableUpdateCompanionBuilder = ProductsCompanion Function({
  Value<int> id,
  Value<String> name,
  Value<int> categoryId,
  Value<String> categoryName,
  Value<int> priceCents,
  Value<bool> active,
  Value<int> schoolId,
  Value<int?> merchantId,
});

class $$ProductsTableFilterComposer
    extends Composer<_$AppDatabase, $ProductsTable> {
  $$ProductsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get categoryId => $composableBuilder(
    column: $table.categoryId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get categoryName => $composableBuilder(
    column: $table.categoryName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get priceCents => $composableBuilder(
    column: $table.priceCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get active => $composableBuilder(
    column: $table.active,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get merchantId => $composableBuilder(
    column: $table.merchantId,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ProductsTableOrderingComposer
    extends Composer<_$AppDatabase, $ProductsTable> {
  $$ProductsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get categoryId => $composableBuilder(
    column: $table.categoryId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get categoryName => $composableBuilder(
    column: $table.categoryName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get priceCents => $composableBuilder(
    column: $table.priceCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get active => $composableBuilder(
    column: $table.active,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get merchantId => $composableBuilder(
    column: $table.merchantId,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ProductsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ProductsTable> {
  $$ProductsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<int> get categoryId => $composableBuilder(
    column: $table.categoryId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get categoryName => $composableBuilder(
    column: $table.categoryName,
    builder: (column) => column,
  );

  GeneratedColumn<int> get priceCents => $composableBuilder(
    column: $table.priceCents,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get active =>
      $composableBuilder(column: $table.active, builder: (column) => column);

  GeneratedColumn<int> get schoolId =>
      $composableBuilder(column: $table.schoolId, builder: (column) => column);

  GeneratedColumn<int> get merchantId => $composableBuilder(
    column: $table.merchantId,
    builder: (column) => column,
  );
}

class $$ProductsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ProductsTable,
          Product,
          $$ProductsTableFilterComposer,
          $$ProductsTableOrderingComposer,
          $$ProductsTableAnnotationComposer,
          $$ProductsTableCreateCompanionBuilder,
          $$ProductsTableUpdateCompanionBuilder,
          (Product, BaseReferences<_$AppDatabase, $ProductsTable, Product>),
          Product,
          PrefetchHooks Function()
        > {
  $$ProductsTableTableManager(_$AppDatabase db, $ProductsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ProductsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ProductsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ProductsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<int> categoryId = const Value.absent(),
                Value<String> categoryName = const Value.absent(),
                Value<int> priceCents = const Value.absent(),
                Value<bool> active = const Value.absent(),
                Value<int> schoolId = const Value.absent(),
                Value<int?> merchantId = const Value.absent(),
              }) => ProductsCompanion(
                id: id,
                name: name,
                categoryId: categoryId,
                categoryName: categoryName,
                priceCents: priceCents,
                active: active,
                schoolId: schoolId,
                merchantId: merchantId,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String name,
                required int categoryId,
                required String categoryName,
                required int priceCents,
                required bool active,
                required int schoolId,
                Value<int?> merchantId = const Value.absent(),
              }) => ProductsCompanion.insert(
                id: id,
                name: name,
                categoryId: categoryId,
                categoryName: categoryName,
                priceCents: priceCents,
                active: active,
                schoolId: schoolId,
                merchantId: merchantId,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$ProductsTable, Product>(table),
                  BaseReferences<_$AppDatabase, $ProductsTable, Product>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ProductsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ProductsTable,
      Product,
      $$ProductsTableFilterComposer,
      $$ProductsTableOrderingComposer,
      $$ProductsTableAnnotationComposer,
      $$ProductsTableCreateCompanionBuilder,
      $$ProductsTableUpdateCompanionBuilder,
      (Product, BaseReferences<_$AppDatabase, $ProductsTable, Product>),
      Product,
      PrefetchHooks Function()
    >;
typedef $$CategoriesTableCreateCompanionBuilder = CategoriesCompanion Function({
  Value<int> id,
  required String name,
  required bool isUnhealthy,
  required bool active,
  required int schoolId,
});
typedef $$CategoriesTableUpdateCompanionBuilder = CategoriesCompanion Function({
  Value<int> id,
  Value<String> name,
  Value<bool> isUnhealthy,
  Value<bool> active,
  Value<int> schoolId,
});

class $$CategoriesTableFilterComposer
    extends Composer<_$AppDatabase, $CategoriesTable> {
  $$CategoriesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isUnhealthy => $composableBuilder(
    column: $table.isUnhealthy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get active => $composableBuilder(
    column: $table.active,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CategoriesTableOrderingComposer
    extends Composer<_$AppDatabase, $CategoriesTable> {
  $$CategoriesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isUnhealthy => $composableBuilder(
    column: $table.isUnhealthy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get active => $composableBuilder(
    column: $table.active,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get schoolId => $composableBuilder(
    column: $table.schoolId,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CategoriesTableAnnotationComposer
    extends Composer<_$AppDatabase, $CategoriesTable> {
  $$CategoriesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<bool> get isUnhealthy => $composableBuilder(
    column: $table.isUnhealthy,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get active =>
      $composableBuilder(column: $table.active, builder: (column) => column);

  GeneratedColumn<int> get schoolId =>
      $composableBuilder(column: $table.schoolId, builder: (column) => column);
}

class $$CategoriesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CategoriesTable,
          Category,
          $$CategoriesTableFilterComposer,
          $$CategoriesTableOrderingComposer,
          $$CategoriesTableAnnotationComposer,
          $$CategoriesTableCreateCompanionBuilder,
          $$CategoriesTableUpdateCompanionBuilder,
          (Category, BaseReferences<_$AppDatabase, $CategoriesTable, Category>),
          Category,
          PrefetchHooks Function()
        > {
  $$CategoriesTableTableManager(_$AppDatabase db, $CategoriesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CategoriesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CategoriesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CategoriesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<bool> isUnhealthy = const Value.absent(),
                Value<bool> active = const Value.absent(),
                Value<int> schoolId = const Value.absent(),
              }) => CategoriesCompanion(
                id: id,
                name: name,
                isUnhealthy: isUnhealthy,
                active: active,
                schoolId: schoolId,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String name,
                required bool isUnhealthy,
                required bool active,
                required int schoolId,
              }) => CategoriesCompanion.insert(
                id: id,
                name: name,
                isUnhealthy: isUnhealthy,
                active: active,
                schoolId: schoolId,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$CategoriesTable, Category>(table),
                  BaseReferences<_$AppDatabase, $CategoriesTable, Category>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CategoriesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CategoriesTable,
      Category,
      $$CategoriesTableFilterComposer,
      $$CategoriesTableOrderingComposer,
      $$CategoriesTableAnnotationComposer,
      $$CategoriesTableCreateCompanionBuilder,
      $$CategoriesTableUpdateCompanionBuilder,
      (Category, BaseReferences<_$AppDatabase, $CategoriesTable, Category>),
      Category,
      PrefetchHooks Function()
    >;
typedef $$RosterCardsTableCreateCompanionBuilder =
    RosterCardsCompanion Function({
      required String cardUid,
      required String status,
      required int studentId,
      required String displayName,
      required String className,
      Value<String?> photoUrl,
      Value<int> rowid,
    });
typedef $$RosterCardsTableUpdateCompanionBuilder =
    RosterCardsCompanion Function({
      Value<String> cardUid,
      Value<String> status,
      Value<int> studentId,
      Value<String> displayName,
      Value<String> className,
      Value<String?> photoUrl,
      Value<int> rowid,
    });

class $$RosterCardsTableFilterComposer
    extends Composer<_$AppDatabase, $RosterCardsTable> {
  $$RosterCardsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get studentId => $composableBuilder(
    column: $table.studentId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get className => $composableBuilder(
    column: $table.className,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnFilters(column),
  );
}

class $$RosterCardsTableOrderingComposer
    extends Composer<_$AppDatabase, $RosterCardsTable> {
  $$RosterCardsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get studentId => $composableBuilder(
    column: $table.studentId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get className => $composableBuilder(
    column: $table.className,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$RosterCardsTableAnnotationComposer
    extends Composer<_$AppDatabase, $RosterCardsTable> {
  $$RosterCardsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get cardUid =>
      $composableBuilder(column: $table.cardUid, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get studentId =>
      $composableBuilder(column: $table.studentId, builder: (column) => column);

  GeneratedColumn<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get className =>
      $composableBuilder(column: $table.className, builder: (column) => column);

  GeneratedColumn<String> get photoUrl =>
      $composableBuilder(column: $table.photoUrl, builder: (column) => column);
}

class $$RosterCardsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $RosterCardsTable,
          RosterCard,
          $$RosterCardsTableFilterComposer,
          $$RosterCardsTableOrderingComposer,
          $$RosterCardsTableAnnotationComposer,
          $$RosterCardsTableCreateCompanionBuilder,
          $$RosterCardsTableUpdateCompanionBuilder,
          (
            RosterCard,
            BaseReferences<_$AppDatabase, $RosterCardsTable, RosterCard>,
          ),
          RosterCard,
          PrefetchHooks Function()
        > {
  $$RosterCardsTableTableManager(_$AppDatabase db, $RosterCardsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RosterCardsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RosterCardsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RosterCardsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> cardUid = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<int> studentId = const Value.absent(),
                Value<String> displayName = const Value.absent(),
                Value<String> className = const Value.absent(),
                Value<String?> photoUrl = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => RosterCardsCompanion(
                cardUid: cardUid,
                status: status,
                studentId: studentId,
                displayName: displayName,
                className: className,
                photoUrl: photoUrl,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String cardUid,
                required String status,
                required int studentId,
                required String displayName,
                required String className,
                Value<String?> photoUrl = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => RosterCardsCompanion.insert(
                cardUid: cardUid,
                status: status,
                studentId: studentId,
                displayName: displayName,
                className: className,
                photoUrl: photoUrl,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$RosterCardsTable, RosterCard>(table),
                  BaseReferences<_$AppDatabase, $RosterCardsTable, RosterCard>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$RosterCardsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $RosterCardsTable,
      RosterCard,
      $$RosterCardsTableFilterComposer,
      $$RosterCardsTableOrderingComposer,
      $$RosterCardsTableAnnotationComposer,
      $$RosterCardsTableCreateCompanionBuilder,
      $$RosterCardsTableUpdateCompanionBuilder,
      (
        RosterCard,
        BaseReferences<_$AppDatabase, $RosterCardsTable, RosterCard>,
      ),
      RosterCard,
      PrefetchHooks Function()
    >;
typedef $$SaleQueueTableCreateCompanionBuilder = SaleQueueCompanion Function({
  Value<int> id,
  required String idempotencyKey,
  required String cardUid,
  required String studentName,
  required int amountCents,
  required String itemsJson,
  required String deviceLocalTimestamp,
  required String kampalaDay,
  required String kampalaWeek,
  required DateTime createdAt,
  required String channel,
  required String status,
  Value<int?> appliedCents,
  Value<int?> shortfallCents,
  Value<String> flags,
  Value<String?> reason,
  Value<int?> serverTransactionId,
  Value<int> attempts,
  Value<String?> lastError,
  Value<DateTime?> syncedAt,
});
typedef $$SaleQueueTableUpdateCompanionBuilder = SaleQueueCompanion Function({
  Value<int> id,
  Value<String> idempotencyKey,
  Value<String> cardUid,
  Value<String> studentName,
  Value<int> amountCents,
  Value<String> itemsJson,
  Value<String> deviceLocalTimestamp,
  Value<String> kampalaDay,
  Value<String> kampalaWeek,
  Value<DateTime> createdAt,
  Value<String> channel,
  Value<String> status,
  Value<int?> appliedCents,
  Value<int?> shortfallCents,
  Value<String> flags,
  Value<String?> reason,
  Value<int?> serverTransactionId,
  Value<int> attempts,
  Value<String?> lastError,
  Value<DateTime?> syncedAt,
});

class $$SaleQueueTableFilterComposer
    extends Composer<_$AppDatabase, $SaleQueueTable> {
  $$SaleQueueTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get itemsJson => $composableBuilder(
    column: $table.itemsJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get kampalaWeek => $composableBuilder(
    column: $table.kampalaWeek,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get channel => $composableBuilder(
    column: $table.channel,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get appliedCents => $composableBuilder(
    column: $table.appliedCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get shortfallCents => $composableBuilder(
    column: $table.shortfallCents,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get flags => $composableBuilder(
    column: $table.flags,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get reason => $composableBuilder(
    column: $table.reason,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get serverTransactionId => $composableBuilder(
    column: $table.serverTransactionId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SaleQueueTableOrderingComposer
    extends Composer<_$AppDatabase, $SaleQueueTable> {
  $$SaleQueueTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get itemsJson => $composableBuilder(
    column: $table.itemsJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get kampalaWeek => $composableBuilder(
    column: $table.kampalaWeek,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get channel => $composableBuilder(
    column: $table.channel,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get appliedCents => $composableBuilder(
    column: $table.appliedCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get shortfallCents => $composableBuilder(
    column: $table.shortfallCents,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get flags => $composableBuilder(
    column: $table.flags,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get reason => $composableBuilder(
    column: $table.reason,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get serverTransactionId => $composableBuilder(
    column: $table.serverTransactionId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SaleQueueTableAnnotationComposer
    extends Composer<_$AppDatabase, $SaleQueueTable> {
  $$SaleQueueTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => column,
  );

  GeneratedColumn<String> get cardUid =>
      $composableBuilder(column: $table.cardUid, builder: (column) => column);

  GeneratedColumn<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => column,
  );

  GeneratedColumn<int> get amountCents => $composableBuilder(
    column: $table.amountCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get itemsJson =>
      $composableBuilder(column: $table.itemsJson, builder: (column) => column);

  GeneratedColumn<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => column,
  );

  GeneratedColumn<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => column,
  );

  GeneratedColumn<String> get kampalaWeek => $composableBuilder(
    column: $table.kampalaWeek,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get channel =>
      $composableBuilder(column: $table.channel, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get appliedCents => $composableBuilder(
    column: $table.appliedCents,
    builder: (column) => column,
  );

  GeneratedColumn<int> get shortfallCents => $composableBuilder(
    column: $table.shortfallCents,
    builder: (column) => column,
  );

  GeneratedColumn<String> get flags =>
      $composableBuilder(column: $table.flags, builder: (column) => column);

  GeneratedColumn<String> get reason =>
      $composableBuilder(column: $table.reason, builder: (column) => column);

  GeneratedColumn<int> get serverTransactionId => $composableBuilder(
    column: $table.serverTransactionId,
    builder: (column) => column,
  );

  GeneratedColumn<int> get attempts =>
      $composableBuilder(column: $table.attempts, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);

  GeneratedColumn<DateTime> get syncedAt =>
      $composableBuilder(column: $table.syncedAt, builder: (column) => column);
}

class $$SaleQueueTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SaleQueueTable,
          SaleQueueData,
          $$SaleQueueTableFilterComposer,
          $$SaleQueueTableOrderingComposer,
          $$SaleQueueTableAnnotationComposer,
          $$SaleQueueTableCreateCompanionBuilder,
          $$SaleQueueTableUpdateCompanionBuilder,
          (
            SaleQueueData,
            BaseReferences<_$AppDatabase, $SaleQueueTable, SaleQueueData>,
          ),
          SaleQueueData,
          PrefetchHooks Function()
        > {
  $$SaleQueueTableTableManager(_$AppDatabase db, $SaleQueueTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SaleQueueTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SaleQueueTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SaleQueueTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> idempotencyKey = const Value.absent(),
                Value<String> cardUid = const Value.absent(),
                Value<String> studentName = const Value.absent(),
                Value<int> amountCents = const Value.absent(),
                Value<String> itemsJson = const Value.absent(),
                Value<String> deviceLocalTimestamp = const Value.absent(),
                Value<String> kampalaDay = const Value.absent(),
                Value<String> kampalaWeek = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<String> channel = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<int?> appliedCents = const Value.absent(),
                Value<int?> shortfallCents = const Value.absent(),
                Value<String> flags = const Value.absent(),
                Value<String?> reason = const Value.absent(),
                Value<int?> serverTransactionId = const Value.absent(),
                Value<int> attempts = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
              }) => SaleQueueCompanion(
                id: id,
                idempotencyKey: idempotencyKey,
                cardUid: cardUid,
                studentName: studentName,
                amountCents: amountCents,
                itemsJson: itemsJson,
                deviceLocalTimestamp: deviceLocalTimestamp,
                kampalaDay: kampalaDay,
                kampalaWeek: kampalaWeek,
                createdAt: createdAt,
                channel: channel,
                status: status,
                appliedCents: appliedCents,
                shortfallCents: shortfallCents,
                flags: flags,
                reason: reason,
                serverTransactionId: serverTransactionId,
                attempts: attempts,
                lastError: lastError,
                syncedAt: syncedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String idempotencyKey,
                required String cardUid,
                required String studentName,
                required int amountCents,
                required String itemsJson,
                required String deviceLocalTimestamp,
                required String kampalaDay,
                required String kampalaWeek,
                required DateTime createdAt,
                required String channel,
                required String status,
                Value<int?> appliedCents = const Value.absent(),
                Value<int?> shortfallCents = const Value.absent(),
                Value<String> flags = const Value.absent(),
                Value<String?> reason = const Value.absent(),
                Value<int?> serverTransactionId = const Value.absent(),
                Value<int> attempts = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
              }) => SaleQueueCompanion.insert(
                id: id,
                idempotencyKey: idempotencyKey,
                cardUid: cardUid,
                studentName: studentName,
                amountCents: amountCents,
                itemsJson: itemsJson,
                deviceLocalTimestamp: deviceLocalTimestamp,
                kampalaDay: kampalaDay,
                kampalaWeek: kampalaWeek,
                createdAt: createdAt,
                channel: channel,
                status: status,
                appliedCents: appliedCents,
                shortfallCents: shortfallCents,
                flags: flags,
                reason: reason,
                serverTransactionId: serverTransactionId,
                attempts: attempts,
                lastError: lastError,
                syncedAt: syncedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SaleQueueTable, SaleQueueData>(table),
                  BaseReferences<_$AppDatabase, $SaleQueueTable, SaleQueueData>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SaleQueueTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SaleQueueTable,
      SaleQueueData,
      $$SaleQueueTableFilterComposer,
      $$SaleQueueTableOrderingComposer,
      $$SaleQueueTableAnnotationComposer,
      $$SaleQueueTableCreateCompanionBuilder,
      $$SaleQueueTableUpdateCompanionBuilder,
      (
        SaleQueueData,
        BaseReferences<_$AppDatabase, $SaleQueueTable, SaleQueueData>,
      ),
      SaleQueueData,
      PrefetchHooks Function()
    >;
typedef $$AttendanceQueueTableCreateCompanionBuilder =
    AttendanceQueueCompanion Function({
      Value<int> id,
      required String idempotencyKey,
      required String cardUid,
      required String studentName,
      required String direction,
      required String deviceLocalTimestamp,
      required String kampalaDay,
      required DateTime createdAt,
      required String status,
      Value<String?> reason,
      Value<int> attempts,
      Value<DateTime?> syncedAt,
    });
typedef $$AttendanceQueueTableUpdateCompanionBuilder =
    AttendanceQueueCompanion Function({
      Value<int> id,
      Value<String> idempotencyKey,
      Value<String> cardUid,
      Value<String> studentName,
      Value<String> direction,
      Value<String> deviceLocalTimestamp,
      Value<String> kampalaDay,
      Value<DateTime> createdAt,
      Value<String> status,
      Value<String?> reason,
      Value<int> attempts,
      Value<DateTime?> syncedAt,
    });

class $$AttendanceQueueTableFilterComposer
    extends Composer<_$AppDatabase, $AttendanceQueueTable> {
  $$AttendanceQueueTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get direction => $composableBuilder(
    column: $table.direction,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get reason => $composableBuilder(
    column: $table.reason,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$AttendanceQueueTableOrderingComposer
    extends Composer<_$AppDatabase, $AttendanceQueueTable> {
  $$AttendanceQueueTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get direction => $composableBuilder(
    column: $table.direction,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get reason => $composableBuilder(
    column: $table.reason,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$AttendanceQueueTableAnnotationComposer
    extends Composer<_$AppDatabase, $AttendanceQueueTable> {
  $$AttendanceQueueTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get idempotencyKey => $composableBuilder(
    column: $table.idempotencyKey,
    builder: (column) => column,
  );

  GeneratedColumn<String> get cardUid =>
      $composableBuilder(column: $table.cardUid, builder: (column) => column);

  GeneratedColumn<String> get studentName => $composableBuilder(
    column: $table.studentName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get direction =>
      $composableBuilder(column: $table.direction, builder: (column) => column);

  GeneratedColumn<String> get deviceLocalTimestamp => $composableBuilder(
    column: $table.deviceLocalTimestamp,
    builder: (column) => column,
  );

  GeneratedColumn<String> get kampalaDay => $composableBuilder(
    column: $table.kampalaDay,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get reason =>
      $composableBuilder(column: $table.reason, builder: (column) => column);

  GeneratedColumn<int> get attempts =>
      $composableBuilder(column: $table.attempts, builder: (column) => column);

  GeneratedColumn<DateTime> get syncedAt =>
      $composableBuilder(column: $table.syncedAt, builder: (column) => column);
}

class $$AttendanceQueueTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $AttendanceQueueTable,
          AttendanceQueueData,
          $$AttendanceQueueTableFilterComposer,
          $$AttendanceQueueTableOrderingComposer,
          $$AttendanceQueueTableAnnotationComposer,
          $$AttendanceQueueTableCreateCompanionBuilder,
          $$AttendanceQueueTableUpdateCompanionBuilder,
          (
            AttendanceQueueData,
            BaseReferences<
              _$AppDatabase,
              $AttendanceQueueTable,
              AttendanceQueueData
            >,
          ),
          AttendanceQueueData,
          PrefetchHooks Function()
        > {
  $$AttendanceQueueTableTableManager(
    _$AppDatabase db,
    $AttendanceQueueTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AttendanceQueueTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AttendanceQueueTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AttendanceQueueTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> idempotencyKey = const Value.absent(),
                Value<String> cardUid = const Value.absent(),
                Value<String> studentName = const Value.absent(),
                Value<String> direction = const Value.absent(),
                Value<String> deviceLocalTimestamp = const Value.absent(),
                Value<String> kampalaDay = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String?> reason = const Value.absent(),
                Value<int> attempts = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
              }) => AttendanceQueueCompanion(
                id: id,
                idempotencyKey: idempotencyKey,
                cardUid: cardUid,
                studentName: studentName,
                direction: direction,
                deviceLocalTimestamp: deviceLocalTimestamp,
                kampalaDay: kampalaDay,
                createdAt: createdAt,
                status: status,
                reason: reason,
                attempts: attempts,
                syncedAt: syncedAt,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String idempotencyKey,
                required String cardUid,
                required String studentName,
                required String direction,
                required String deviceLocalTimestamp,
                required String kampalaDay,
                required DateTime createdAt,
                required String status,
                Value<String?> reason = const Value.absent(),
                Value<int> attempts = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
              }) => AttendanceQueueCompanion.insert(
                id: id,
                idempotencyKey: idempotencyKey,
                cardUid: cardUid,
                studentName: studentName,
                direction: direction,
                deviceLocalTimestamp: deviceLocalTimestamp,
                kampalaDay: kampalaDay,
                createdAt: createdAt,
                status: status,
                reason: reason,
                attempts: attempts,
                syncedAt: syncedAt,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$AttendanceQueueTable, AttendanceQueueData>(
                    table,
                  ),
                  BaseReferences<
                    _$AppDatabase,
                    $AttendanceQueueTable,
                    AttendanceQueueData
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$AttendanceQueueTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $AttendanceQueueTable,
      AttendanceQueueData,
      $$AttendanceQueueTableFilterComposer,
      $$AttendanceQueueTableOrderingComposer,
      $$AttendanceQueueTableAnnotationComposer,
      $$AttendanceQueueTableCreateCompanionBuilder,
      $$AttendanceQueueTableUpdateCompanionBuilder,
      (
        AttendanceQueueData,
        BaseReferences<
          _$AppDatabase,
          $AttendanceQueueTable,
          AttendanceQueueData
        >,
      ),
      AttendanceQueueData,
      PrefetchHooks Function()
    >;
typedef $$PinFailuresTableCreateCompanionBuilder =
    PinFailuresCompanion Function({
      required String cardUid,
      required int failures,
      required int unreported,
      required DateTime firstFailureAt,
      required DateTime lastFailureAt,
      Value<bool> locked,
      Value<int> rowid,
    });
typedef $$PinFailuresTableUpdateCompanionBuilder =
    PinFailuresCompanion Function({
      Value<String> cardUid,
      Value<int> failures,
      Value<int> unreported,
      Value<DateTime> firstFailureAt,
      Value<DateTime> lastFailureAt,
      Value<bool> locked,
      Value<int> rowid,
    });

class $$PinFailuresTableFilterComposer
    extends Composer<_$AppDatabase, $PinFailuresTable> {
  $$PinFailuresTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get failures => $composableBuilder(
    column: $table.failures,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get unreported => $composableBuilder(
    column: $table.unreported,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get firstFailureAt => $composableBuilder(
    column: $table.firstFailureAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastFailureAt => $composableBuilder(
    column: $table.lastFailureAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get locked => $composableBuilder(
    column: $table.locked,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PinFailuresTableOrderingComposer
    extends Composer<_$AppDatabase, $PinFailuresTable> {
  $$PinFailuresTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get cardUid => $composableBuilder(
    column: $table.cardUid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get failures => $composableBuilder(
    column: $table.failures,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get unreported => $composableBuilder(
    column: $table.unreported,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get firstFailureAt => $composableBuilder(
    column: $table.firstFailureAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastFailureAt => $composableBuilder(
    column: $table.lastFailureAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get locked => $composableBuilder(
    column: $table.locked,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PinFailuresTableAnnotationComposer
    extends Composer<_$AppDatabase, $PinFailuresTable> {
  $$PinFailuresTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get cardUid =>
      $composableBuilder(column: $table.cardUid, builder: (column) => column);

  GeneratedColumn<int> get failures =>
      $composableBuilder(column: $table.failures, builder: (column) => column);

  GeneratedColumn<int> get unreported => $composableBuilder(
    column: $table.unreported,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get firstFailureAt => $composableBuilder(
    column: $table.firstFailureAt,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get lastFailureAt => $composableBuilder(
    column: $table.lastFailureAt,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get locked =>
      $composableBuilder(column: $table.locked, builder: (column) => column);
}

class $$PinFailuresTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PinFailuresTable,
          PinFailure,
          $$PinFailuresTableFilterComposer,
          $$PinFailuresTableOrderingComposer,
          $$PinFailuresTableAnnotationComposer,
          $$PinFailuresTableCreateCompanionBuilder,
          $$PinFailuresTableUpdateCompanionBuilder,
          (
            PinFailure,
            BaseReferences<_$AppDatabase, $PinFailuresTable, PinFailure>,
          ),
          PinFailure,
          PrefetchHooks Function()
        > {
  $$PinFailuresTableTableManager(_$AppDatabase db, $PinFailuresTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PinFailuresTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PinFailuresTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PinFailuresTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> cardUid = const Value.absent(),
                Value<int> failures = const Value.absent(),
                Value<int> unreported = const Value.absent(),
                Value<DateTime> firstFailureAt = const Value.absent(),
                Value<DateTime> lastFailureAt = const Value.absent(),
                Value<bool> locked = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PinFailuresCompanion(
                cardUid: cardUid,
                failures: failures,
                unreported: unreported,
                firstFailureAt: firstFailureAt,
                lastFailureAt: lastFailureAt,
                locked: locked,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String cardUid,
                required int failures,
                required int unreported,
                required DateTime firstFailureAt,
                required DateTime lastFailureAt,
                Value<bool> locked = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PinFailuresCompanion.insert(
                cardUid: cardUid,
                failures: failures,
                unreported: unreported,
                firstFailureAt: firstFailureAt,
                lastFailureAt: lastFailureAt,
                locked: locked,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$PinFailuresTable, PinFailure>(table),
                  BaseReferences<_$AppDatabase, $PinFailuresTable, PinFailure>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PinFailuresTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PinFailuresTable,
      PinFailure,
      $$PinFailuresTableFilterComposer,
      $$PinFailuresTableOrderingComposer,
      $$PinFailuresTableAnnotationComposer,
      $$PinFailuresTableCreateCompanionBuilder,
      $$PinFailuresTableUpdateCompanionBuilder,
      (
        PinFailure,
        BaseReferences<_$AppDatabase, $PinFailuresTable, PinFailure>,
      ),
      PinFailure,
      PrefetchHooks Function()
    >;
typedef $$KvTableCreateCompanionBuilder = KvCompanion Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$KvTableUpdateCompanionBuilder = KvCompanion Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$KvTableFilterComposer extends Composer<_$AppDatabase, $KvTable> {
  $$KvTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnFilters(column),
  );
}

class $$KvTableOrderingComposer extends Composer<_$AppDatabase, $KvTable> {
  $$KvTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$KvTableAnnotationComposer extends Composer<_$AppDatabase, $KvTable> {
  $$KvTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$KvTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $KvTable,
          KvData,
          $$KvTableFilterComposer,
          $$KvTableOrderingComposer,
          $$KvTableAnnotationComposer,
          $$KvTableCreateCompanionBuilder,
          $$KvTableUpdateCompanionBuilder,
          (KvData, BaseReferences<_$AppDatabase, $KvTable, KvData>),
          KvData,
          PrefetchHooks Function()
        > {
  $$KvTableTableManager(_$AppDatabase db, $KvTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$KvTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$KvTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$KvTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) => KvCompanion(key: key, value: value, rowid: rowid),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) => KvCompanion.insert(key: key, value: value, rowid: rowid),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$KvTable, KvData>(table),
                  BaseReferences<_$AppDatabase, $KvTable, KvData>(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$KvTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $KvTable,
      KvData,
      $$KvTableFilterComposer,
      $$KvTableOrderingComposer,
      $$KvTableAnnotationComposer,
      $$KvTableCreateCompanionBuilder,
      $$KvTableUpdateCompanionBuilder,
      (KvData, BaseReferences<_$AppDatabase, $KvTable, KvData>),
      KvData,
      PrefetchHooks Function()
    >;
typedef $$SyncLogTableCreateCompanionBuilder = SyncLogCompanion Function({
  Value<int> id,
  required DateTime at,
  required String kind,
  required bool ok,
  required String message,
});
typedef $$SyncLogTableUpdateCompanionBuilder = SyncLogCompanion Function({
  Value<int> id,
  Value<DateTime> at,
  Value<String> kind,
  Value<bool> ok,
  Value<String> message,
});

class $$SyncLogTableFilterComposer
    extends Composer<_$AppDatabase, $SyncLogTable> {
  $$SyncLogTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get at => $composableBuilder(
    column: $table.at,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get kind => $composableBuilder(
    column: $table.kind,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get ok => $composableBuilder(
    column: $table.ok,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get message => $composableBuilder(
    column: $table.message,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncLogTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncLogTable> {
  $$SyncLogTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get at => $composableBuilder(
    column: $table.at,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get kind => $composableBuilder(
    column: $table.kind,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get ok => $composableBuilder(
    column: $table.ok,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get message => $composableBuilder(
    column: $table.message,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncLogTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncLogTable> {
  $$SyncLogTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<DateTime> get at =>
      $composableBuilder(column: $table.at, builder: (column) => column);

  GeneratedColumn<String> get kind =>
      $composableBuilder(column: $table.kind, builder: (column) => column);

  GeneratedColumn<bool> get ok =>
      $composableBuilder(column: $table.ok, builder: (column) => column);

  GeneratedColumn<String> get message =>
      $composableBuilder(column: $table.message, builder: (column) => column);
}

class $$SyncLogTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncLogTable,
          SyncLogData,
          $$SyncLogTableFilterComposer,
          $$SyncLogTableOrderingComposer,
          $$SyncLogTableAnnotationComposer,
          $$SyncLogTableCreateCompanionBuilder,
          $$SyncLogTableUpdateCompanionBuilder,
          (
            SyncLogData,
            BaseReferences<_$AppDatabase, $SyncLogTable, SyncLogData>,
          ),
          SyncLogData,
          PrefetchHooks Function()
        > {
  $$SyncLogTableTableManager(_$AppDatabase db, $SyncLogTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncLogTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncLogTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncLogTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<DateTime> at = const Value.absent(),
                Value<String> kind = const Value.absent(),
                Value<bool> ok = const Value.absent(),
                Value<String> message = const Value.absent(),
              }) => SyncLogCompanion(
                id: id,
                at: at,
                kind: kind,
                ok: ok,
                message: message,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required DateTime at,
                required String kind,
                required bool ok,
                required String message,
              }) => SyncLogCompanion.insert(
                id: id,
                at: at,
                kind: kind,
                ok: ok,
                message: message,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncLogTable, SyncLogData>(table),
                  BaseReferences<_$AppDatabase, $SyncLogTable, SyncLogData>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncLogTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncLogTable,
      SyncLogData,
      $$SyncLogTableFilterComposer,
      $$SyncLogTableOrderingComposer,
      $$SyncLogTableAnnotationComposer,
      $$SyncLogTableCreateCompanionBuilder,
      $$SyncLogTableUpdateCompanionBuilder,
      (SyncLogData, BaseReferences<_$AppDatabase, $SyncLogTable, SyncLogData>),
      SyncLogData,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedCardsTableTableManager get cachedCards =>
      $$CachedCardsTableTableManager(_db, _db.cachedCards);
  $$ProductsTableTableManager get products =>
      $$ProductsTableTableManager(_db, _db.products);
  $$CategoriesTableTableManager get categories =>
      $$CategoriesTableTableManager(_db, _db.categories);
  $$RosterCardsTableTableManager get rosterCards =>
      $$RosterCardsTableTableManager(_db, _db.rosterCards);
  $$SaleQueueTableTableManager get saleQueue =>
      $$SaleQueueTableTableManager(_db, _db.saleQueue);
  $$AttendanceQueueTableTableManager get attendanceQueue =>
      $$AttendanceQueueTableTableManager(_db, _db.attendanceQueue);
  $$PinFailuresTableTableManager get pinFailures =>
      $$PinFailuresTableTableManager(_db, _db.pinFailures);
  $$KvTableTableManager get kv => $$KvTableTableManager(_db, _db.kv);
  $$SyncLogTableTableManager get syncLog =>
      $$SyncLogTableTableManager(_db, _db.syncLog);
}
