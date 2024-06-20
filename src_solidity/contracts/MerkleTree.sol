pragma solidity >= 0.5.0;
pragma experimental ABIEncoderV2;

library MerkleTree {
    function upperPower2(uint n) internal pure returns (uint) {
        uint res = 2;
        while (res < n) {
            res *= 2;
        }
        return res;
    }

    bytes32 constant zeroHash = keccak256(abi.encodePacked(bytes32(0)));
    function getRoot(bytes32[] memory dataArr) internal pure returns (bytes32) {
        uint n = dataArr.length;
        uint cnt = upperPower2(n)/2;
        bytes32[] memory hashes = new bytes32[](cnt);

        for (uint i = 0; i < cnt; i++) {
            if ((2*i+1) < n) {
                hashes[i] = keccak256(abi.encodePacked(dataArr[2*i], dataArr[2*i+1]));
            } else if (2*i == n-1) {
                hashes[i] = keccak256(abi.encodePacked(dataArr[2*i], zeroHash));
            } else {
                hashes[i] = keccak256(abi.encodePacked(zeroHash, zeroHash));
            }
        }

        // return zeroBytes;
        // return hashes[cnt-1];

        // uint level = 1;

        do {
            cnt /= 2;
            // level += 1;
            for (uint i = 0; i < cnt; i++) {
                hashes[i] = keccak256(abi.encodePacked(hashes[2*i], hashes[2*i+1]));
            }
            // if (level == 4) {
            //     return hashes[1];
            // }
        } while (cnt >= 2);

        return hashes[0];
    }

    function verify(
        uint index, bytes32 leaf, bytes32 root, bytes32[] memory proof
    ) internal pure returns (bool) {
        bytes32 hash = leaf;

        for (uint i = 0; i < proof.length; i++) {
            bytes32 proofElement = proof[i];

            if (index % 2 == 0) {
                hash = keccak256(abi.encodePacked(hash, proofElement));
            } else {
                hash = keccak256(abi.encodePacked(proofElement, hash));
            }

            index = index / 2;
        }

        return hash == root;
    }
    
}