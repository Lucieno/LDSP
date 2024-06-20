# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: offchaincommun.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='offchaincommun.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x14offchaincommun.proto\"4\n\x0bPaymentInfo\x12\x13\n\x0b\x63ustomer_id\x18\x01 \x01(\r\x12\x10\n\x08prespend\x18\x02 \x01(\t\"8\n\x0fMerchantPayInfo\x12\x13\n\x0bmerchant_id\x18\x01 \x01(\r\x12\x10\n\x08prespend\x18\x02 \x01(\t\"\x1e\n\tSignature\x12\x11\n\tsignature\x18\x01 \x01(\t\"-\n\x06PuzSol\x12\x13\n\x0b\x63ustomer_id\x18\x01 \x01(\r\x12\x0e\n\x06puzsol\x18\x02 \x01(\t\"K\n\x11WithdrawalRequest\x12\x13\n\x0b\x63ustomer_id\x18\x01 \x01(\r\x12\x0f\n\x07\x66und_id\x18\x02 \x01(\t\x12\x10\n\x08num_coin\x18\x03 \x01(\r\"\x0e\n\x01Y\x12\t\n\x01Y\x18\x01 \x01(\t\";\n\x11MerchantSignature\x12\x13\n\x0bmerchant_id\x18\x01 \x01(\r\x12\x11\n\tsignature\x18\x02 \x01(\t\"W\n\x0c\x43ustomerSign\x12\x13\n\x0b\x63ustomer_id\x18\x01 \x01(\r\x12\x11\n\tsignature\x18\x02 \x01(\t\x12\x10\n\x08\x62lind_sn\x18\x03 \x01(\t\x12\r\n\x05Y_sgn\x18\x04 \x01(\t\"\x07\n\x05\x45mpty2\x8f\x03\n\x0eOffchainCommun\x12,\n\x0cStartPayment\x12\x0c.PaymentInfo\x1a\n.Signature\"\x00\x30\x01\x12\x32\n\x0eProcessPayment\x12\x10.MerchantPayInfo\x1a\n.Signature\"\x00\x30\x01\x12#\n\x0eTransmitPuzSol\x12\x07.PuzSol\x1a\x06.Empty\"\x00\x12-\n\x0fStartWithdrawal\x12\x12.WithdrawalRequest\x1a\x02.Y\"\x00\x30\x01\x12\x34\n\x14SingleBlindSignMerge\x12\x12.MerchantSignature\x1a\x06.Empty\"\x00\x12+\n\x10\x42\x61tchWithdrawC2M\x12\r.CustomerSign\x1a\x06.Empty\"\x00\x12\x31\n\x11\x42\x61tchBlindSignM2L\x12\x12.MerchantSignature\x1a\x06.Empty\"\x00\x12\x31\n\x10\x42\x61tchWithdrawC2L\x12\r.CustomerSign\x1a\n.Signature\"\x00\x30\x01\x62\x06proto3'
)




_PAYMENTINFO = _descriptor.Descriptor(
  name='PaymentInfo',
  full_name='PaymentInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='customer_id', full_name='PaymentInfo.customer_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='prespend', full_name='PaymentInfo.prespend', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=24,
  serialized_end=76,
)


_MERCHANTPAYINFO = _descriptor.Descriptor(
  name='MerchantPayInfo',
  full_name='MerchantPayInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='merchant_id', full_name='MerchantPayInfo.merchant_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='prespend', full_name='MerchantPayInfo.prespend', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=78,
  serialized_end=134,
)


_SIGNATURE = _descriptor.Descriptor(
  name='Signature',
  full_name='Signature',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='signature', full_name='Signature.signature', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=136,
  serialized_end=166,
)


_PUZSOL = _descriptor.Descriptor(
  name='PuzSol',
  full_name='PuzSol',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='customer_id', full_name='PuzSol.customer_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='puzsol', full_name='PuzSol.puzsol', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=168,
  serialized_end=213,
)


_WITHDRAWALREQUEST = _descriptor.Descriptor(
  name='WithdrawalRequest',
  full_name='WithdrawalRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='customer_id', full_name='WithdrawalRequest.customer_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fund_id', full_name='WithdrawalRequest.fund_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='num_coin', full_name='WithdrawalRequest.num_coin', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=215,
  serialized_end=290,
)


_Y = _descriptor.Descriptor(
  name='Y',
  full_name='Y',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='Y', full_name='Y.Y', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=292,
  serialized_end=306,
)


_MERCHANTSIGNATURE = _descriptor.Descriptor(
  name='MerchantSignature',
  full_name='MerchantSignature',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='merchant_id', full_name='MerchantSignature.merchant_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='signature', full_name='MerchantSignature.signature', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=308,
  serialized_end=367,
)


_CUSTOMERSIGN = _descriptor.Descriptor(
  name='CustomerSign',
  full_name='CustomerSign',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='customer_id', full_name='CustomerSign.customer_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='signature', full_name='CustomerSign.signature', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='blind_sn', full_name='CustomerSign.blind_sn', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='Y_sgn', full_name='CustomerSign.Y_sgn', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=369,
  serialized_end=456,
)


_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=458,
  serialized_end=465,
)

DESCRIPTOR.message_types_by_name['PaymentInfo'] = _PAYMENTINFO
DESCRIPTOR.message_types_by_name['MerchantPayInfo'] = _MERCHANTPAYINFO
DESCRIPTOR.message_types_by_name['Signature'] = _SIGNATURE
DESCRIPTOR.message_types_by_name['PuzSol'] = _PUZSOL
DESCRIPTOR.message_types_by_name['WithdrawalRequest'] = _WITHDRAWALREQUEST
DESCRIPTOR.message_types_by_name['Y'] = _Y
DESCRIPTOR.message_types_by_name['MerchantSignature'] = _MERCHANTSIGNATURE
DESCRIPTOR.message_types_by_name['CustomerSign'] = _CUSTOMERSIGN
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PaymentInfo = _reflection.GeneratedProtocolMessageType('PaymentInfo', (_message.Message,), {
  'DESCRIPTOR' : _PAYMENTINFO,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:PaymentInfo)
  })
_sym_db.RegisterMessage(PaymentInfo)

MerchantPayInfo = _reflection.GeneratedProtocolMessageType('MerchantPayInfo', (_message.Message,), {
  'DESCRIPTOR' : _MERCHANTPAYINFO,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:MerchantPayInfo)
  })
_sym_db.RegisterMessage(MerchantPayInfo)

Signature = _reflection.GeneratedProtocolMessageType('Signature', (_message.Message,), {
  'DESCRIPTOR' : _SIGNATURE,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:Signature)
  })
_sym_db.RegisterMessage(Signature)

PuzSol = _reflection.GeneratedProtocolMessageType('PuzSol', (_message.Message,), {
  'DESCRIPTOR' : _PUZSOL,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:PuzSol)
  })
_sym_db.RegisterMessage(PuzSol)

WithdrawalRequest = _reflection.GeneratedProtocolMessageType('WithdrawalRequest', (_message.Message,), {
  'DESCRIPTOR' : _WITHDRAWALREQUEST,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:WithdrawalRequest)
  })
_sym_db.RegisterMessage(WithdrawalRequest)

Y = _reflection.GeneratedProtocolMessageType('Y', (_message.Message,), {
  'DESCRIPTOR' : _Y,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:Y)
  })
_sym_db.RegisterMessage(Y)

MerchantSignature = _reflection.GeneratedProtocolMessageType('MerchantSignature', (_message.Message,), {
  'DESCRIPTOR' : _MERCHANTSIGNATURE,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:MerchantSignature)
  })
_sym_db.RegisterMessage(MerchantSignature)

CustomerSign = _reflection.GeneratedProtocolMessageType('CustomerSign', (_message.Message,), {
  'DESCRIPTOR' : _CUSTOMERSIGN,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:CustomerSign)
  })
_sym_db.RegisterMessage(CustomerSign)

Empty = _reflection.GeneratedProtocolMessageType('Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'offchaincommun_pb2'
  # @@protoc_insertion_point(class_scope:Empty)
  })
_sym_db.RegisterMessage(Empty)



_OFFCHAINCOMMUN = _descriptor.ServiceDescriptor(
  name='OffchainCommun',
  full_name='OffchainCommun',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=468,
  serialized_end=867,
  methods=[
  _descriptor.MethodDescriptor(
    name='StartPayment',
    full_name='OffchainCommun.StartPayment',
    index=0,
    containing_service=None,
    input_type=_PAYMENTINFO,
    output_type=_SIGNATURE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ProcessPayment',
    full_name='OffchainCommun.ProcessPayment',
    index=1,
    containing_service=None,
    input_type=_MERCHANTPAYINFO,
    output_type=_SIGNATURE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='TransmitPuzSol',
    full_name='OffchainCommun.TransmitPuzSol',
    index=2,
    containing_service=None,
    input_type=_PUZSOL,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='StartWithdrawal',
    full_name='OffchainCommun.StartWithdrawal',
    index=3,
    containing_service=None,
    input_type=_WITHDRAWALREQUEST,
    output_type=_Y,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='SingleBlindSignMerge',
    full_name='OffchainCommun.SingleBlindSignMerge',
    index=4,
    containing_service=None,
    input_type=_MERCHANTSIGNATURE,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='BatchWithdrawC2M',
    full_name='OffchainCommun.BatchWithdrawC2M',
    index=5,
    containing_service=None,
    input_type=_CUSTOMERSIGN,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='BatchBlindSignM2L',
    full_name='OffchainCommun.BatchBlindSignM2L',
    index=6,
    containing_service=None,
    input_type=_MERCHANTSIGNATURE,
    output_type=_EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='BatchWithdrawC2L',
    full_name='OffchainCommun.BatchWithdrawC2L',
    index=7,
    containing_service=None,
    input_type=_CUSTOMERSIGN,
    output_type=_SIGNATURE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_OFFCHAINCOMMUN)

DESCRIPTOR.services_by_name['OffchainCommun'] = _OFFCHAINCOMMUN

# @@protoc_insertion_point(module_scope)
