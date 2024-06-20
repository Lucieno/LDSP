// pragma solidity >=0.5.0;
pragma solidity ^0.7.6;
pragma experimental ABIEncoderV2;

import "./Pairing.sol";
// import "./PairingHelper.sol";
import "./ECVerify.sol";
// import "./BLS.sol";
import "./MerkleTree.sol";

contract LDSP {
    uint constant public CoinWorth = 10;
    uint constant public CurveOrder =
        21888242871839275222246405745257275088548364400416034343698204186575808495617;
    uint constant public DoubleSpendCollateral = 1000;

    address payable leader;

    uint EpochIndex;
    Pairing.G1Point EpochHash;

    constructor() payable {
        leader = msg.sender;
    }

    Pairing.G2Point vk;

    function getEpochHash() public view returns (uint256[2] memory) {
        return [uint(EpochHash.x), uint(EpochHash.y)];
    }

    function getHashed(uint x) public pure returns (uint256) {
        return uint256(keccak256(abi.encodePacked(x)));
    }

    function getEncoded(uint x) public view returns (bytes memory ) {
        return abi.encodePacked(EpochIndex);
    }

    function setVk(uint[4] memory _vk) public returns (bool) {
        require(msg.sender == leader);
        vk = Pairing.G2Point({x: [_vk[0], _vk[1]], y: [_vk[2], _vk[3]]});
        return true;
    }

    function setEpochIndex(uint _epochIndex) public returns (bool) {
        require(msg.sender == leader);
        EpochIndex = _epochIndex;
        EpochHash = Pairing.hashToG1(abi.encodePacked(EpochIndex));
        return true;
    }

	function arrToG1(uint[2] memory arr) pure internal returns (Pairing.G1Point memory) {
        Pairing.G1Point memory res = Pairing.G1Point({
            x: arr[0],
            y: arr[1] 
        });
		return res;
	}

	function arrToG2(uint[] memory arr) pure internal returns (Pairing.G2Point memory) {
        Pairing.G2Point memory res = Pairing.G2Point({
            x: [arr[0], arr[1]],
            y: [arr[2], arr[3]]
        });
		return res;
	}

    // Single Withdrawal

    mapping(uint => bytes32) public SingleFundHash;
    mapping(uint => bytes32) public SingleBlindSignHash;

    uint constant FUNDED_FLAG = 0;
    uint constant REVEALED_FLAG = 1;
    uint constant REVEAL_FAILED_FALG = 2;
    // uint constant REVEAL_SUCCEED_FALG = 3;

    // customer call
    function singleWithdrawFund(
        uint fundId, uint[] memory CommittedY, uint blindSn
    ) public payable returns (bool) {
        require(msg.value >= CoinWorth);
        require(SingleBlindSignHash[fundId] == bytes32(0x0));
        SingleFundHash[fundId] = keccak256(abi.encodePacked(msg.sender, CommittedY, blindSn, FUNDED_FLAG));
        return true;
    }

    // assume the leader call it on behave of all merchants
    bool constant CHALLNEGED_FLAG = true;
    function singleWithdrawalBlindSign(
        uint fundId, uint[] memory blindSign
    ) public returns (bool) {
        require(msg.sender == leader);
        SingleBlindSignHash[fundId] = keccak256(abi.encodePacked(blindSign, !CHALLNEGED_FLAG));
        return true;
    }

    function verifyBlindSign(uint[2] memory blindSign, uint[2] memory CommittedY, uint blindSn
    ) internal returns (uint) {
        Pairing.G1Point memory left = arrToG1(blindSign);
        Pairing.G1Point memory Y = arrToG1(CommittedY);
        Pairing.G1Point memory right = Pairing.addG1(Pairing.curveMul(EpochHash, blindSn), Y);

        return Pairing.pairing2(Pairing.negate(left), Pairing.P2(), right, vk);
    }

    // assume the customer calls it
    function singleWithdrawalChallengeBlindSign(
        uint fundId, uint[2] memory CommittedY, uint blindSn, uint[2] memory blindSign
    ) public returns (bool) {
        require(SingleFundHash[fundId] == keccak256(abi.encodePacked(
            msg.sender, CommittedY, blindSn, FUNDED_FLAG)));
        require(SingleBlindSignHash[fundId] == keccak256(abi.encodePacked(blindSign, !CHALLNEGED_FLAG)));

        uint result = verifyBlindSign(blindSign, CommittedY, blindSn);
        // bool result = Pairing.pairing2(Pairing.negate(Pairing.P1()), Pairing.P2(), Pairing.P1(), Pairing.P2());
        // return result;
        if (result != 0) {
            SingleBlindSignHash[fundId] = keccak256(abi.encodePacked(blindSign, CHALLNEGED_FLAG));
            msg.sender.transfer(CoinWorth);
            return true;
        }

        return false;
    }

    bool constant IS_CLOSE = true;
    bool constant IS_FAILED = true;
    bool constant IS_SUBMITTED = true;
    mapping(uint => bytes32) batchFundHash;

    function batchWithdrawalFund(uint fundId, uint numTotalCoin) payable public returns (bool) {
        require(msg.value >= numTotalCoin * CoinWorth);
        require(batchFundHash[fundId] == bytes32(0x0));

        batchFundHash[fundId] = keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, !IS_SUBMITTED, !IS_FAILED, !IS_CLOSE));
        return true;
    }

    mapping(uint => bytes32) batchSubmitBlindSignHash;

    function batchWithdrawalSubmitBlindSign(
        uint fundId, uint prevCoin, uint currCoin, 
        bytes32 batchBlindSnYHash, bytes memory customerSign, address customerAddr, 
        uint numTotalCoin, uint[] memory batchBlindSign
    ) public returns (bool) {
        require(msg.sender == leader, "msg.sender == leader");
        require(batchSubmitBlindSignHash[fundId] == bytes32(0x0), 
            "Wrong batchSubmitBlindSignHash[fundId]");
        require(batchFundHash[fundId] == keccak256(abi.encodePacked(
            customerAddr, numTotalCoin, !IS_SUBMITTED, !IS_FAILED, !IS_CLOSE)),
            "Wrong batchFundHash[fundId]");

        // verify customer signature
        bytes32 messageHash = keccak256(abi.encodePacked(customerAddr, prevCoin, currCoin, batchBlindSnYHash));
        require(ECVerify.verify(customerAddr, messageHash, customerSign), "Wrong Signatuyre");

        require(batchBlindSign.length == currCoin * 2, "batchBlindSign.length check failed");
        // bytes32 batchBlindSignHash = keccak256(abi.encodePacked(currCoin, batchBlindSign));
        bytes32[] memory dataArr = new bytes32[](batchBlindSign.length/2);
        for (uint i = 0; i < batchBlindSign.length/2; i++) {
            dataArr[i] = keccak256(abi.encodePacked(batchBlindSign[2*i], batchBlindSign[2*i+1]));
        }
        bytes32 batchBlindSignHash = MerkleTree.getRoot(dataArr);

        batchFundHash[fundId] = keccak256(abi.encodePacked(
            customerAddr, numTotalCoin, IS_SUBMITTED, !IS_FAILED, !IS_CLOSE));
        batchSubmitBlindSignHash[fundId] = keccak256(abi.encodePacked(
            // customerAddr, prevCoin, currCoin, batchBlindSnYHash));
            customerAddr, prevCoin, currCoin, batchBlindSnYHash, batchBlindSignHash));
        return true;
    }

    function batchWithdrawalClose(
        uint fundId, uint numTotalCoin
    ) public returns (bool) {
        require(batchFundHash[fundId] == keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, !IS_SUBMITTED, !IS_FAILED, !IS_CLOSE)),
            "Wrong batchFundHash[fundId]");

        batchFundHash[fundId] = keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, IS_SUBMITTED, !IS_FAILED, IS_CLOSE));

        return true;
    }

    function pickFromArr(uint[] memory arr, uint idx) internal pure returns (uint[2] memory) {
        return [arr[idx*2], arr[idx*2+1]];
    }

    function batchWithdrawalChallengeBlindSign(
        uint fundId, uint prevCoin, uint currCoin, 
        // bytes32 batchBlindSnYHash, 
        uint numTotalCoin, 
        // bytes32 batchBlindSignHash,
        bytes32[] calldata snY,
        // uint batchBlindSn, uint[2] memory batchY, bytes32 blindSnYRoof, bytes32[] memory blindSnYProof,
        bytes32[] calldata blindSign,
        // uint[2] memory blindSign, bytes32 blindSignRoof, bytes32[] memory blindSignProof,
        uint challengeIdx
    ) public returns (bool) {
        require(batchFundHash[fundId] == keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, IS_SUBMITTED, !IS_FAILED, !IS_CLOSE)), 
            "Checking batchFundHash[fundId]");
        require(batchSubmitBlindSignHash[fundId] == keccak256(abi.encodePacked(
            // msg.sender, prevCoin, currCoin, snY[3])),
            msg.sender, prevCoin, currCoin, snY[3], blindSign[2])),
            "Checking batchSubmitBlindSignHash");

        require(challengeIdx < currCoin, "challengeIdx < currCoin");
        require(MerkleTree.verify(
            challengeIdx, keccak256(abi.encodePacked(uint(snY[0]), uint(snY[1]), uint(snY[2]))), snY[3], snY[4:]),
            "Checking blindSnYHash");
        require(MerkleTree.verify(
            challengeIdx, keccak256(abi.encodePacked(uint(blindSign[0]), uint(blindSign[1]))), blindSign[2], blindSign[3:]),
            "Checking blindSign");
        
        uint pairing_res = verifyBlindSign(
            [uint(blindSign[0]), uint(blindSign[1])],
            [uint(snY[1]), uint(snY[2])],
            uint(snY[0]));

        if (pairing_res != 0) {
            batchFundHash[fundId] = keccak256(
                abi.encodePacked(msg.sender, numTotalCoin, IS_SUBMITTED, IS_FAILED, !IS_CLOSE));
            msg.sender.transfer(numTotalCoin * CoinWorth);
            return true;
        }

        return false;
    }

    mapping(uint => bytes32) singleRefundRevealHash;

    function singleRefundReveal(
        uint fundId, uint[] memory CommittedY, uint blindSn,
        uint alpha, uint beta, uint hashedSn
    ) public returns (bool) {
        require(SingleFundHash[fundId] == keccak256(abi.encodePacked(
            msg.sender, CommittedY, blindSn, FUNDED_FLAG)), 
            "checking SingleFundHash");
        
        singleRefundRevealHash[fundId] = keccak256(abi.encodePacked(
            alpha, beta, hashedSn));

        SingleFundHash[fundId] = keccak256(abi.encodePacked(
            msg.sender, CommittedY, blindSn, REVEALED_FLAG));
        return true;
    }

    function verifyOpening(
        uint[2] memory CommittedY, uint blindSn,
        uint alpha, uint beta, uint hashedSn
    ) internal returns (bool) {
        Pairing.G1Point memory yPrime = Pairing.addG1(
            Pairing.curveMul(arrToG1(CommittedY), alpha),
            Pairing.curveMul(EpochHash, mulmod(alpha, beta, CurveOrder)));
        uint hpmy = uint256(keccak256(abi.encodePacked(hashedSn, yPrime.x, yPrime.y)));
        uint alpha_inverse = Pairing.expMod(alpha, CurveOrder-2, CurveOrder);

        uint computed_blindSn = addmod(
            mulmod(alpha_inverse, hpmy, CurveOrder), 
            beta, 
            CurveOrder);
        // return computed_blindSn;

        return (computed_blindSn == blindSn);
    }

    function singleRefundChallengeOpening(
        uint fundId, uint[2] memory CommittedY, uint blindSn,
        uint alpha, uint beta, uint hashedSn, address customerAddr
    ) public returns (bool) {
        require(leader == msg.sender, "msg.sender must be leader");
        require(SingleFundHash[fundId] == keccak256(abi.encodePacked(
            customerAddr, CommittedY, blindSn, REVEALED_FLAG)), 
            "checking SingleFundHash");
        
        require(singleRefundRevealHash[fundId] == keccak256(abi.encodePacked(
            alpha, beta, hashedSn)),
            "checking singleRefundRevealHash");
        
        bool verifyResult = verifyOpening(CommittedY, blindSn, alpha, beta, hashedSn);

        if (verifyResult == false) {
            SingleFundHash[fundId] = keccak256(abi.encodePacked(
                customerAddr, CommittedY, blindSn, REVEAL_FAILED_FALG));
            msg.sender.transfer(CoinWorth);
            return true;
        }

        return false;
    }

    function singleRefundChallengeSpent(
        uint fundId, uint[2] memory CommittedY, uint blindSn,
        uint alpha, uint beta, uint hashedSn, address customerAddr,
        uint sn
    ) public returns (bool) {
        require(leader == msg.sender, "msg.sender must be leader");
        require(SingleFundHash[fundId] == keccak256(abi.encodePacked(
            customerAddr, CommittedY, blindSn, REVEALED_FLAG)), 
            "checking SingleFundHash");
        
        require(singleRefundRevealHash[fundId] == keccak256(abi.encodePacked(
            alpha, beta, hashedSn)),
            "checking singleRefundRevealHash");
        
        bool verifyResult = (hashedSn == uint(keccak256(abi.encodePacked(sn))));

        if (verifyResult == true) {
            SingleFundHash[fundId] = keccak256(abi.encodePacked(
                customerAddr, CommittedY, blindSn, REVEAL_FAILED_FALG));
            msg.sender.transfer(CoinWorth);
            return true;
        }

        return false;
    }

    function batchRefundReveal(
        uint fundId, uint[] memory key, 
        uint leftBound, uint rightBound, uint numTotalCoin
    ) public returns (bool) {
        require(batchFundHash[fundId] == keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, !IS_SUBMITTED, !IS_FAILED, !IS_CLOSE)),
            "Check batchFundHash");

        bytes32[] memory dataArr = new bytes32[](key.length);

        for (uint i = 0; i < key.length; i++) {
            dataArr[i] = keccak256(abi.encodePacked(key[i]));
        }
        
        bytes32 root = MerkleTree.getRoot(dataArr);

        batchFundHash[fundId] = keccak256(abi.encodePacked(
            msg.sender, numTotalCoin, !IS_SUBMITTED, leftBound, rightBound, root, key.length));
        return true;
    }

    function isRight(uint x) internal pure returns (bool) {
        return x % 2 == 0;
        // return ((x - 1) / 2) * 2 + 2 == x;
    }

    function isLeft(uint x) internal pure returns (bool) {
        return x % 2 == 1;
        // return ((x - 1) / 2) * 2 + 1 == x;
    }

    function toParent(uint x) internal pure returns (uint) {
        return (x - 1) / 2;
    }

    function segLocate(
        uint coinId, uint leftBound, uint rightBound, uint numCoin
    ) internal pure returns (uint) {
        uint keyIdx = 0;
        uint layerIdx = 0;
        leftBound += numCoin - 1;
        rightBound += numCoin - 1;
        coinId += numCoin - 1;
        while ((leftBound > 0) && (rightBound > 0) && (leftBound < rightBound)) {
            if (isRight(leftBound)) {
                if (coinId == leftBound) return ((keyIdx << 128) + layerIdx);
                keyIdx++;
                leftBound++;
            }
            leftBound = toParent(leftBound);

            if (isLeft(rightBound)) {
                if (coinId == rightBound) return ((keyIdx << 128) + layerIdx);
                keyIdx++;
                rightBound--;
            }
            rightBound = toParent(rightBound);

            layerIdx++;
            coinId = toParent(coinId);
        }

        if (leftBound == rightBound) {
            return ((keyIdx << 128) + layerIdx);
            // keyIdx++;
        }

        require(false, "segLocate: outside of left/rightBound");
        // return ((keyIdx-1) << 128 + layerIdx);
        // return (keyIdx, layerIdx);
    }

    function verifyEncOpenning(
        uint key, bytes32[] calldata encOpening, bytes32[] calldata commitment
    ) internal returns (bool) {
        uint alpha = uint(encOpening[0]) ^ uint(keccak256(abi.encodePacked(key, uint(0))));
        uint beta = uint(encOpening[1]) ^ uint(keccak256(abi.encodePacked(key, uint(1))));
        uint hashedSn = uint(encOpening[2]) ^ uint(keccak256(abi.encodePacked(key, uint(2))));

        return verifyOpening(
            [uint(commitment[0]), uint(commitment[1])], uint(commitment[2]), 
           alpha, beta, hashedSn);
    }

    uint constant CHALLENGE_OPEN_SUCCESS = 5;
    function batchRefundChallenge(
        uint[] calldata idx,
        // uint fundId, uint coinId, uint numTotalCoin, uint leftBound, uint rightBound, uint sn,
        address customerAddr,
        bytes32[] calldata key,
        // uint key, bytes32 keyRoot, uint numSubmittedKey, bytes32[] memory keyProof, 
        bytes32[] calldata encOpening,
        // uint[3] memory encOpening, bbytes32 encOpeningRoot, ytes32[] memory encOpeningProof,
        bytes32[] calldata cmt,
        // bytes32 commitmentRoot, uint[3] memory commitment, bytes32[] memory commitmentProof,
        bytes memory customerSign
    ) public returns (bool) {
        require(batchFundHash[idx[0]] == keccak256(abi.encodePacked(
            customerAddr, idx[2], !IS_SUBMITTED, idx[3], idx[4], key[1], uint(key[2]))),
            "Checking batchFundHash");
        require((idx[3] <= idx[1]) && (idx[1] <= idx[4]), 
            "Checking left/right Bound");

        require(ECVerify.verify(
            customerAddr, 
            keccak256(abi.encodePacked(idx[0], idx[2], encOpening[3], cmt[0])), 
            customerSign), 
            "Wrong Signature");

        uint keyLayerIdx = segLocate(idx[1], idx[3], idx[4], idx[2]);

        require(MerkleTree.verify(
            uint(keyLayerIdx >> 128), keccak256(abi.encodePacked(uint(key[0]))), key[1], key[3:]),
            "Checking Key");
        require(MerkleTree.verify(
            uint((keyLayerIdx & ((1 << 128)-1)) * idx[2] + idx[1]), 
            keccak256(abi.encodePacked(encOpening[:3])), 
            encOpening[3], encOpening[4:]),
            "Checking encOpening");

        bool spentVerify = (
            (uint(encOpening[2]) ^ uint(keccak256(abi.encodePacked(uint(key[0]), uint(2))))) == 
            uint(keccak256(abi.encodePacked(idx[5]))));

        if ((spentVerify == false) && (idx[5] == 0)) {
            require(MerkleTree.verify(
                idx[1], keccak256(abi.encodePacked(cmt[1:4])), cmt[0], cmt[4:]),
                "Checking cmt");
        }

        if (spentVerify ||
            ((idx[5] == 0) && (verifyEncOpenning(uint(key[0]), encOpening[:3], cmt[1:4]) == false))) {
            msg.sender.transfer(idx[2] * CoinWorth);
            batchFundHash[idx[0]] = keccak256(abi.encodePacked(customerAddr, idx[2], CHALLENGE_OPEN_SUCCESS));
            return true;
        }

        return false;
    }

    function verifySn(
        Pairing.G2Point memory _verificationKey,
        uint sn,
        uint[4] calldata sign
    ) internal returns (bool) {
        uint hashedSn = uint(keccak256(abi.encodePacked(sn)));
        Pairing.G1Point memory Y_prime = arrToG1([sign[2], sign[3]]);
        uint hpmy = uint(keccak256(abi.encodePacked(hashedSn, sign[2], sign[3])));
        Pairing.G1Point memory right = Pairing.addG1(Pairing.curveMul(EpochHash, hpmy), Y_prime);

        uint result = Pairing.pairing2(
            Pairing.negateLst([sign[0], sign[1]]),
            Pairing.P2(), 
            right, 
            _verificationKey);
        return result == 0;
    }

    uint constant DEPOSIT_SUBMIT = 0;
    mapping(uint => bytes32) SingleDepositHash;
    function singleDepositSubmit(
        uint sn, uint[4] memory signSn, bytes memory leaderSign
    ) public returns (bool) {
        require(SingleDepositHash[sn] == bytes32(0));

        bytes32 messagehash = keccak256(abi.encodePacked(sn, signSn, msg.sender));
        require(ECVerify.verify(leader, messagehash, leaderSign), "Wrong Signatuyre");

        msg.sender.transfer(CoinWorth);

        SingleDepositHash[sn] = keccak256(abi.encodePacked(signSn, msg.sender, DEPOSIT_SUBMIT));
        return true;
    }

    uint constant DEPOSIT_WRONG_SIGN = 1;
    function singleDepositChallengeSignSn(
        uint sn, uint[4] calldata signSn, address merchantAddr
    ) public returns (bool) {
        require(SingleDepositHash[sn] == keccak256(
            abi.encodePacked(signSn, merchantAddr, DEPOSIT_SUBMIT)),
            "Checking SingleDepositHash");

        if (verifySn(vk, sn, signSn) == false) {
            SingleDepositHash[sn] = keccak256(abi.encodePacked(
                signSn, merchantAddr, DEPOSIT_WRONG_SIGN));
            msg.sender.transfer(CoinWorth);
            return true;
        }

        return false;
    }

    function singleDepositChallengeDoubleSpent(
        uint sn, uint[] memory signSn, 
        address merchant1stAddr, bytes memory leaderSign2nd
    ) public returns (bool) {
        require(SingleDepositHash[sn] == keccak256(abi.encodePacked(
            signSn, merchant1stAddr, DEPOSIT_SUBMIT)),
            "Checking SingleDepositHash");
        require(merchant1stAddr != msg.sender,
            "The two merchants should be different");

        bytes32 messagehash = keccak256(abi.encodePacked(sn, signSn, msg.sender));
        if (ECVerify.verify(leader, messagehash, leaderSign2nd)) {
            SingleDepositHash[sn] = keccak256(abi.encodePacked(
                signSn, merchant1stAddr, msg.sender, DEPOSIT_SUBMIT));
            msg.sender.transfer(CoinWorth);
            return true;
        }

        return false;
    }

    function verifyBlsHashed(
        Pairing.G2Point memory _verificationKey,
        bytes32 hashedMessage,
        uint[2] calldata sign
    ) internal returns (bool) {
        Pairing.G1Point memory hashedOnCurve = Pairing.curveMul(Pairing.P1(), uint(hashedMessage));
        uint result = Pairing.pairing2(Pairing.negateLst([sign[0], sign[1]]), Pairing.P2(), hashedOnCurve, _verificationKey);
        return result == 0;
    }

    bytes32 public MerchantBalanceHash = bytes32(0);
    mapping(uint => bytes32) public RoundConsensusHash;

    function roundConsensusSubmit(
        uint roundIdx,
        bytes32 spentHash,
        uint[2] calldata jointSign,
        uint[] memory merchantBalance
    ) public returns (bool) {
        require(msg.sender == leader);
        require(RoundConsensusHash[roundIdx] == bytes32(0), "roundIdx exist");

        bytes32 _merchantBalanceHash = keccak256(abi.encodePacked(merchantBalance));
        bytes32 hashedMessage = keccak256(abi.encodePacked(roundIdx, spentHash, _merchantBalanceHash));
        // return hashedMessage;
        if (verifyBlsHashed(vk, hashedMessage, jointSign) == false) {
            return false;
        }

        MerchantBalanceHash = _merchantBalanceHash;
        RoundConsensusHash[roundIdx] = hashedMessage;
        return true;
    }

    mapping(bytes32 => uint) public DoubleSpendHash;
    function ChallengeDoubleSpend(
        uint sn, 
        uint[] memory signSn,
        address merchant2ndAddr, 
        bytes memory leaderSign1,
        bytes memory leaderSign2
    ) public returns (bool) {
        bytes32 storeHash = keccak256(abi.encodePacked(sn, msg.sender));
        require(DoubleSpendHash[storeHash] == uint(0), "Seen Victim");

        bytes32 messageHash1 = keccak256(abi.encodePacked(sn, signSn, msg.sender));
        bytes32 messageHash2 = keccak256(abi.encodePacked(sn, signSn, merchant2ndAddr));
        if (ECVerify.verify(leader, messageHash1, leaderSign1) && ECVerify.verify(leader, messageHash2, leaderSign2)) {
            DoubleSpendHash[storeHash] = 1;
            msg.sender.transfer(DoubleSpendCollateral);
            return true;
        }

        return false;
    }

}