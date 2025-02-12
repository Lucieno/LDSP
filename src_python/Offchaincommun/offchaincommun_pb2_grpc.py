# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import src_python.Offchaincommun.offchaincommun_pb2 as offchaincommun__pb2


class OffchainCommunStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.StartPayment = channel.unary_stream(
                '/OffchainCommun/StartPayment',
                request_serializer=offchaincommun__pb2.PaymentInfo.SerializeToString,
                response_deserializer=offchaincommun__pb2.Signature.FromString,
                )
        self.ProcessPayment = channel.unary_stream(
                '/OffchainCommun/ProcessPayment',
                request_serializer=offchaincommun__pb2.MerchantPayInfo.SerializeToString,
                response_deserializer=offchaincommun__pb2.Signature.FromString,
                )
        self.TransmitPuzSol = channel.unary_unary(
                '/OffchainCommun/TransmitPuzSol',
                request_serializer=offchaincommun__pb2.PuzSol.SerializeToString,
                response_deserializer=offchaincommun__pb2.Empty.FromString,
                )
        self.StartWithdrawal = channel.unary_stream(
                '/OffchainCommun/StartWithdrawal',
                request_serializer=offchaincommun__pb2.WithdrawalRequest.SerializeToString,
                response_deserializer=offchaincommun__pb2.Y.FromString,
                )
        self.SingleBlindSignMerge = channel.unary_unary(
                '/OffchainCommun/SingleBlindSignMerge',
                request_serializer=offchaincommun__pb2.MerchantSignature.SerializeToString,
                response_deserializer=offchaincommun__pb2.Empty.FromString,
                )
        self.BatchWithdrawC2M = channel.unary_unary(
                '/OffchainCommun/BatchWithdrawC2M',
                request_serializer=offchaincommun__pb2.CustomerSign.SerializeToString,
                response_deserializer=offchaincommun__pb2.Empty.FromString,
                )
        self.BatchBlindSignM2L = channel.unary_unary(
                '/OffchainCommun/BatchBlindSignM2L',
                request_serializer=offchaincommun__pb2.MerchantSignature.SerializeToString,
                response_deserializer=offchaincommun__pb2.Empty.FromString,
                )
        self.BatchWithdrawC2L = channel.unary_stream(
                '/OffchainCommun/BatchWithdrawC2L',
                request_serializer=offchaincommun__pb2.CustomerSign.SerializeToString,
                response_deserializer=offchaincommun__pb2.Signature.FromString,
                )


class OffchainCommunServicer(object):
    """Missing associated documentation comment in .proto file."""

    def StartPayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ProcessPayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TransmitPuzSol(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartWithdrawal(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SingleBlindSignMerge(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BatchWithdrawC2M(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BatchBlindSignM2L(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BatchWithdrawC2L(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_OffchainCommunServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'StartPayment': grpc.unary_stream_rpc_method_handler(
                    servicer.StartPayment,
                    request_deserializer=offchaincommun__pb2.PaymentInfo.FromString,
                    response_serializer=offchaincommun__pb2.Signature.SerializeToString,
            ),
            'ProcessPayment': grpc.unary_stream_rpc_method_handler(
                    servicer.ProcessPayment,
                    request_deserializer=offchaincommun__pb2.MerchantPayInfo.FromString,
                    response_serializer=offchaincommun__pb2.Signature.SerializeToString,
            ),
            'TransmitPuzSol': grpc.unary_unary_rpc_method_handler(
                    servicer.TransmitPuzSol,
                    request_deserializer=offchaincommun__pb2.PuzSol.FromString,
                    response_serializer=offchaincommun__pb2.Empty.SerializeToString,
            ),
            'StartWithdrawal': grpc.unary_stream_rpc_method_handler(
                    servicer.StartWithdrawal,
                    request_deserializer=offchaincommun__pb2.WithdrawalRequest.FromString,
                    response_serializer=offchaincommun__pb2.Y.SerializeToString,
            ),
            'SingleBlindSignMerge': grpc.unary_unary_rpc_method_handler(
                    servicer.SingleBlindSignMerge,
                    request_deserializer=offchaincommun__pb2.MerchantSignature.FromString,
                    response_serializer=offchaincommun__pb2.Empty.SerializeToString,
            ),
            'BatchWithdrawC2M': grpc.unary_unary_rpc_method_handler(
                    servicer.BatchWithdrawC2M,
                    request_deserializer=offchaincommun__pb2.CustomerSign.FromString,
                    response_serializer=offchaincommun__pb2.Empty.SerializeToString,
            ),
            'BatchBlindSignM2L': grpc.unary_unary_rpc_method_handler(
                    servicer.BatchBlindSignM2L,
                    request_deserializer=offchaincommun__pb2.MerchantSignature.FromString,
                    response_serializer=offchaincommun__pb2.Empty.SerializeToString,
            ),
            'BatchWithdrawC2L': grpc.unary_stream_rpc_method_handler(
                    servicer.BatchWithdrawC2L,
                    request_deserializer=offchaincommun__pb2.CustomerSign.FromString,
                    response_serializer=offchaincommun__pb2.Signature.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'OffchainCommun', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class OffchainCommun(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def StartPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/OffchainCommun/StartPayment',
            offchaincommun__pb2.PaymentInfo.SerializeToString,
            offchaincommun__pb2.Signature.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ProcessPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/OffchainCommun/ProcessPayment',
            offchaincommun__pb2.MerchantPayInfo.SerializeToString,
            offchaincommun__pb2.Signature.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def TransmitPuzSol(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/OffchainCommun/TransmitPuzSol',
            offchaincommun__pb2.PuzSol.SerializeToString,
            offchaincommun__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StartWithdrawal(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/OffchainCommun/StartWithdrawal',
            offchaincommun__pb2.WithdrawalRequest.SerializeToString,
            offchaincommun__pb2.Y.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SingleBlindSignMerge(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/OffchainCommun/SingleBlindSignMerge',
            offchaincommun__pb2.MerchantSignature.SerializeToString,
            offchaincommun__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BatchWithdrawC2M(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/OffchainCommun/BatchWithdrawC2M',
            offchaincommun__pb2.CustomerSign.SerializeToString,
            offchaincommun__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BatchBlindSignM2L(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/OffchainCommun/BatchBlindSignM2L',
            offchaincommun__pb2.MerchantSignature.SerializeToString,
            offchaincommun__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BatchWithdrawC2L(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/OffchainCommun/BatchWithdrawC2L',
            offchaincommun__pb2.CustomerSign.SerializeToString,
            offchaincommun__pb2.Signature.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
